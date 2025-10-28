# main_runner.py

import json
import pandas as pd
from datetime import datetime
import os
import sys
import importlib

# ----------------------------------------------------------------------
# SOLUÇÃO PARA MODULE RESOLUTION
# ----------------------------------------------------------------------
# AQUI: Define a pasta raiz do projeto no caminho de importação do Python
# Isso permite que pacotes como 'diagnosticos' e 'analises' sejam encontrados.
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# ----------------------------------------------------------------------
# 1. IMPORTAÇÕES E DISPATCHERS
# ----------------------------------------------------------------------

try:
    from data_loader.loader import load_data
except ImportError:
    print("ERRO: O módulo 'data_loader.loader' com a função 'load_data' não foi encontrado.")
    exit()

# Dicionários que armazenarão as funções importadas dinamicamente
ANALYSIS_MAPPER = {}
DIAGNOSTIC_MAPPER = {}

def build_dispatchers(analises_config):
    """
    Constrói os mapas de funções (dispatchers) importando as funções dinamicamente.
    """
    print("\nConstruindo dispatchers de funções...")
    funcoes_importadas = set()
    ANALYSIS_MAPPER.clear()
    DIAGNOSTIC_MAPPER.clear()

    for regra in analises_config.get('regras_globais_eda', []):
        tipo_analise = regra['tipo_analise']
        modulo_base_nome = regra.get('modulo')
        
        if not modulo_base_nome:
            print(f"   ! Regra '{tipo_analise}' ignorada: Campo 'modulo' não especificado no JSON.")
            continue
        
        # --- Dispatcher de ANÁLISE ---
        funcao_analise_nome = regra.get('funcao_analise')
        if funcao_analise_nome and tipo_analise not in ANALYSIS_MAPPER:
            try:
                modulo_analise_nome = f"analises.{modulo_base_nome}" 
                modulo = importlib.import_module(modulo_analise_nome)
                funcao = getattr(modulo, funcao_analise_nome)
                ANALYSIS_MAPPER[tipo_analise] = funcao
                funcoes_importadas.add(funcao_analise_nome)
            except (ImportError, AttributeError) as e:
                print(f"   ! ERRO CRÍTICO ao carregar função de Análise '{funcao_analise_nome}'.")
                print(f"     Módulo Tentado: {modulo_analise_nome}")
                print(f"     Detalhe da Exceção ({e.__class__.__name__}): {e}")
                print(f"     Regra '{tipo_analise}' ignorada na fase de análise.")
                continue

        # --- Dispatcher de DIAGNÓSTICO ---
        funcao_diagnostico_nome = regra.get('funcao_diagnostico')
        if funcao_diagnostico_nome and tipo_analise not in DIAGNOSTIC_MAPPER:
            try:
                modulo_diagnostico_nome = f"diagnosticos.{modulo_base_nome}_diag"
                modulo = importlib.import_module(modulo_diagnostico_nome)
                funcao = getattr(modulo, funcao_diagnostico_nome)
                DIAGNOSTIC_MAPPER[tipo_analise] = funcao
                funcoes_importadas.add(funcao_diagnostico_nome)
            except (ImportError, AttributeError) as e:
                print(f"   ! ERRO CRÍTICO ao carregar função de Diagnóstico '{funcao_diagnostico_nome}'.")
                print(f"     Módulo Tentado: {modulo_diagnostico_nome}")
                print(f"     Detalhe da Exceção ({e.__class__.__name__}): {e}")
                print(f"     Regra '{tipo_analise}' ignorada na fase de diagnóstico.")
                continue

    print(f"   -> {len(funcoes_importadas)} funções carregadas com sucesso.")

# ----------------------------------------------------------------------
# 2. FUNÇÕES AUXILIARES E FLUXO PRINCIPAL
# ----------------------------------------------------------------------

def get_columns_by_type(meta: dict, alvo_tipos: list) -> list:
    """Extrai a lista de colunas da metatabela com base no tipo."""
    colunas_encontradas = set()
    for tipo in alvo_tipos:
        if tipo in meta:
            valor = meta[tipo]
            if isinstance(valor, str):
                colunas_encontradas.add(valor)
            elif isinstance(valor, list):
                colunas_encontradas.update(valor)
    return list(colunas_encontradas)


def executar_analise(metadata: dict, analises_config: dict) -> list:
    """FASE 1: Itera sobre tabelas e regras para coletar resultados padronizados."""
    
    print("--- INICIANDO FASE DE ANÁLISE (Coleta de Fatos) ---")
    resultados_analise = []

    for meta_tabela in metadata['tabelas']:
        tabela_nome = meta_tabela['nome_tabela']
        print(f"\n[TABELA: {tabela_nome}]")
        
        try:
            df = load_data(meta_tabela['caminho_arquivo'], meta_tabela['tipo_arquivo']) 
        except NotImplementedError:
             print("   ! ERRO: Implementação de load_data ausente ou incompleta. Pulando.")
             continue
        except Exception as e:
            print(f"   ! ERRO FATAL ao carregar dados ({e.__class__.__name__}). Pulando. Erro: {e}")
            continue
            
        for regra in analises_config.get('regras_globais_eda', []):
            tipo_analise = regra['tipo_analise']
            alvo_tipo = regra['alvo_tipo']
            
            if tipo_analise not in ANALYSIS_MAPPER:
                continue

            colunas_para_analise = get_columns_by_type(meta_tabela, alvo_tipo)
            
            if colunas_para_analise:
                print(f"   -> Executando '{tipo_analise}' em colunas: {colunas_para_analise}")
                try:
                    funcao_analise = ANALYSIS_MAPPER[tipo_analise]
                    resultado = funcao_analise(df, colunas_para_analise, **regra.get('parametros', {}))
                    
                    if not isinstance(resultado, dict):
                         print(f"   ! Tipo de Retorno INVÁLIDO: {type(resultado)}. Pulando coleta.")
                         continue
                         
                    # 1. Adiciona metadados de rastreabilidade (Padronização)
                    resultado['tabela'] = tabela_nome
                    resultado['tipo_analise'] = tipo_analise
                    resultado['tipo_alvo_meta'] = alvo_tipo

                    # 2. Adição
                    resultados_analise.append(resultado)
                    print(f"   -> SUCESSO na análise: Resultado coletado.") 
                    
                except Exception as e:
                    print(f"   ! ERRO CRÍTICO na coleta de resultado '{tipo_analise}' ({e.__class__.__name__}). Detalhe: {e}")
                    print(f"     Detalhe do Erro: {e}")
                    print("     O resultado não foi adicionado à lista mestra.")                    
    return resultados_analise

def executar_diagnostico(resultados_analise: list) -> tuple:
    """FASE 2: Itera sobre resultados de análise para gerar registros de diagnóstico JSON."""
    
    print("\n--- INICIANDO FASE DE DIAGNÓSTICO (Interpretação e Regras) ---")
    diagnosticos_registrados = []
    total_alertas = 0
    total_criticos = 0
    
    for resultado in resultados_analise:
        tipo_analise = resultado['tipo_analise']
        
        if tipo_analise in DIAGNOSTIC_MAPPER:
            try:
                funcao_diagnostico = DIAGNOSTIC_MAPPER[tipo_analise]
                
                registros = funcao_diagnostico(resultado)
                
                for registro in registros:
                    diagnosticos_registrados.append(registro)
                    if registro.get('severidade') == "ALERTA":
                        total_alertas += 1
                    elif registro.get('severidade') == "CRÍTICO":
                        total_criticos += 1
            except Exception as e:
                print(f"   ! ERRO no diagnóstico da análise '{tipo_analise}' ({e.__class__.__name__}): {e}")
        
    return diagnosticos_registrados, total_alertas, total_criticos

def construir_saida_final(diagnosticos_registrados: list, metadata: dict, total_alertas: int, total_criticos: int, total_analises_concluidas: int) -> dict:
    """Constrói o JSON de saída final padronizado para uso em pipelines."""
    
    resumo = {
        "data_execucao": datetime.now().isoformat(),
        "total_tabelas": len(metadata['tabelas']),
        "total_analises_executadas": total_analises_concluidas, # Usa a contagem real
        "total_alertas": total_alertas,
        "total_criticos": total_criticos
    }
    
    return {
        "resumo_execucao": resumo,
        "diagnosticos_registrados": diagnosticos_registrados
    }

# ----------------------------------------------------------------------
# 3. FUNÇÃO PRINCIPAL
# ----------------------------------------------------------------------

def main():
    
    print("Carregando arquivos de configuração...")
    try:
        # Assumindo que os arquivos estão em 'config/'
        with open('config/eda_tabelas.json', 'r') as f:
            metadata = json.load(f)
        with open('config/eda_analises.json', 'r') as f:
            analises_config = json.load(f)
        
    except FileNotFoundError as e:
        print(f"Erro: Arquivo de configuração não encontrado: {e.filename}")
        return
    except json.JSONDecodeError:
        print("Erro: Falha ao decodificar JSON em um dos arquivos de configuração.")
        return

    build_dispatchers(analises_config)

    # Executar Pipeline
    
    # Fase 1: Análise
    resultados_fase_analise = executar_analise(metadata, analises_config)
    total_analises_concluidas = len(resultados_fase_analise)

    # Fase 2: Diagnóstico
    registros_fase_diagnostico, total_alertas, total_criticos = executar_diagnostico(resultados_fase_analise)

    # Construir e Exportar
    relatorio_final = construir_saida_final(
        registros_fase_diagnostico, 
        metadata, 
        total_alertas, 
        total_criticos,
        total_analises_concluidas
    )

    # Exportar JSON (Saída para Pipeline)
    output_filename = 'relatorio_eda_final.json'
    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(relatorio_final, f, indent=2, ensure_ascii=False)
        print(f"\n--- SUCESSO! Relatório final exportado para {output_filename} ---")
    except Exception as e:
        print(f"\nERRO ao salvar o arquivo JSON: {e}")

if __name__ == '__main__':
    main()