import json
import pandas as pd
from datetime import datetime
import os
import importlib

# ----------------------------------------------------------------------
# 1. IMPORTAÇÕES E DISPATCHERS
# O loader.py é importado diretamente e não será simulado.
# O resto das funções são importadas dinamicamente.
# ----------------------------------------------------------------------

try:
    # Assumindo a existência do módulo data_loader/loader.py com a função load_data
    from data_loader.loader import load_data
except ImportError:
    print("ERRO: O módulo 'data_loader.loader' com a função 'load_data' não foi encontrado.")
    print("Certifique-se de que loader.py está implementado corretamente.")
    exit()


# Dicionários que armazenarão as funções importadas dinamicamente
ANALYSIS_MAPPER = {}
DIAGNOSTIC_MAPPER = {}

def build_dispatchers(analises_config):
    """
    Constrói os mapas de funções (dispatchers) importando as funções dinamicamente 
    com base nos nomes fornecidos em 'funcao_analise' e 'funcao_diagnostico' do JSON.
    """
    
    print("\nConstruindo dispatchers de funções...")
    
    funcoes_importadas = set()

    for regra in analises_config.get('regras_globais_eda', []):
        tipo_analise = regra['tipo_analise']
        
        # --- Dispatcher de ANÁLISE ---
        funcao_analise_nome = regra.get('funcao_analise')
        if funcao_analise_nome and funcao_analise_nome not in ANALYSIS_MAPPER:
            try:
                # O módulo é inferido pelo nome da função. Ex: validacao_chave_primaria -> analises.integridade
                modulo_nome = f"analises.{funcao_analise_nome.split('_')[0]}" 
                modulo = importlib.import_module(modulo_nome)
                funcao = getattr(modulo, funcao_analise_nome)
                ANALYSIS_MAPPER[tipo_analise] = funcao
                funcoes_importadas.add(funcao_analise_nome)
            except (ImportError, AttributeError):
                print(f"   ! Falha ao carregar função de Análise '{funcao_analise_nome}'. Regra ignorada.")
                continue

        # --- Dispatcher de DIAGNÓSTICO ---
        funcao_diagnostico_nome = regra.get('funcao_diagnostico')
        if funcao_diagnostico_nome and funcao_diagnostico_nome not in DIAGNOSTIC_MAPPER:
            try:
                # O módulo é inferido. Ex: diagnostico_chave_primaria -> diagnosticos.integridade_diag
                modulo_nome = f"diagnosticos.{funcao_diagnostico_nome.replace('diagnostico_', '').split('_')[0]}_diag"
                modulo = importlib.import_module(modulo_nome)
                funcao = getattr(modulo, funcao_diagnostico_nome)
                DIAGNOSTIC_MAPPER[tipo_analise] = funcao
                funcoes_importadas.add(funcao_diagnostico_nome)
            except (ImportError, AttributeError):
                print(f"   ! Falha ao carregar função de Diagnóstico '{funcao_diagnostico_nome}'.")

    print(f"   -> {len(funcoes_importadas)} funções carregadas com sucesso.")

# ----------------------------------------------------------------------
# 2. FUNÇÕES AUXILIARES E FLUXO PRINCIPAL (Inalteradas ou Ajustadas)
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
            # Uso direto da função load_data, sem simulação.
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
            
            # Novo: Checa se a função foi carregada no dispatcher
            if tipo_analise not in ANALYSIS_MAPPER:
                continue

            colunas_para_analise = get_columns_by_type(meta_tabela, alvo_tipo)
            
            if colunas_para_analise:
                print(f"   -> Executando '{tipo_analise}' em colunas: {colunas_para_analise}")
                try:
                    funcao_analise = ANALYSIS_MAPPER[tipo_analise]
                    resultado = funcao_analise(df, colunas_para_analise, **regra.get('parametros', {}))
                    
                    # Adiciona metadados de rastreabilidade (Padronização)
                    resultado['tabela'] = tabela_nome
                    resultado['tipo_analise'] = tipo_analise
                    resultado['tipo_alvo_meta'] = alvo_tipo

                    resultados_analise.append(resultado)
                except Exception as e:
                    print(f"   ! ERRO na execução da análise '{tipo_analise}' ({e.__class__.__name__}): {e}")
                    
    return resultados_analise


def executar_diagnostico(resultados_analise: list) -> tuple:
    """FASE 2: Itera sobre resultados de análise para gerar registros de diagnóstico JSON."""
    
    print("\n--- INICIANDO FASE DE DIAGNÓSTICO (Interpretação e Regras) ---")
    diagnosticos_registrados = []
    total_alertas = 0
    total_criticos = 0
    
    for resultado in resultados_analise:
        tipo_analise = resultado['tipo_analise']
        
        # Novo: Checa se a função foi carregada no dispatcher
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


def construir_saida_final(diagnosticos_registrados: list, metadata: dict, total_alertas: int, total_criticos: int) -> dict:
    """Constrói o JSON de saída final padronizado para uso em pipelines."""
    
    resumo = {
        "data_execucao": datetime.now().isoformat(),
        "total_tabelas": len(metadata['tabelas']),
        "total_analises_executadas": len(diagnosticos_registrados),
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
        # Carregando metadados das tabelas (EDA_Tabelas.json)
        with open('EDA_Tabelas.json', 'r') as f:
            metadata = json.load(f)
        # Carregando regras de análise com os nomes das funções (EDA_analises.json)
        with open('EDA_analises.json', 'r') as f:
            analises_config = json.load(f)
        
    except FileNotFoundError as e:
        print(f"Erro: Arquivo de configuração não encontrado: {e.filename}")
        return
    except json.JSONDecodeError:
        print("Erro: Falha ao decodificar JSON em um dos arquivos de configuração.")
        return

    # Construir os dispatchers DEPOIS de carregar a config
    build_dispatchers(analises_config)

    # Executar Pipeline
    
    # Fase 1: Análise
    resultados_fase_analise = executar_analise(metadata, analises_config)

    # Fase 2: Diagnóstico
    registros_fase_diagnostico, total_alertas, total_criticos = executar_diagnostico(resultados_fase_analise)

    # Construir e Exportar
    relatorio_final = construir_saida_final(
        registros_fase_diagnostico, 
        metadata, 
        total_alertas, 
        total_criticos
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
    # Define o caminho de trabalho para garantir que as importações funcionem
    # Assume que a raiz do projeto é o diretório pai de main_runner.py
    # path_root = os.path.dirname(os.path.abspath(__file__))
    # sys.path.append(path_root)
    # ^ Isso pode ser necessário dependendo de como você executa o script
    
    main()