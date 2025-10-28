# diagnosticos/integridade_diag.py

from typing import Dict, Any, List
# Importa a função base para a criação do registro
from .base_diagnosticos import criar_registro_diagnostico

def diagnostico_chave_primaria(resultado_analise: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Interpreta o resultado da análise de chave primária e gera uma lista
    de Registros de Diagnóstico JSON (problemas acionáveis).
    """
    diagnosticos = []
    tabela = resultado_analise.get('tabela', 'N/A')
    dados = resultado_analise['dados_resultado']
    pk_col = dados.get('coluna_pk', 'N/A')
    origem = resultado_analise['tipo_analise']
    
    # ----------------------------------------------------
    # Regra 1: CHAVE DUPLICADA
    # ----------------------------------------------------
    if dados.get('duplicados_count', 0) > 0:
        diagnosticos.append(criar_registro_diagnostico(
            id_diag="PK_INTEGRIDADE_001",
            tabela=tabela,
            coluna=pk_col,
            origem=origem,
            severidade="CRÍTICO",
            categoria="INTEGRIDADE",
            mensagem="Chave primária não é única.",
            detalhe=f"{dados['percentual_duplicados']:.2f}% ({dados['duplicados_count']} registros) da PK '{pk_col}' estão duplicados.",
            recomendacao="Remover ou consolidar duplicados. Verificar o processo de geração/ETL da PK.",
            evidencia=dados
        ))

    # ----------------------------------------------------
    # Regra 2: CHAVE NULA
    # ----------------------------------------------------
    if dados.get('nulos_count', 0) > 0:
        diagnosticos.append(criar_registro_diagnostico(
            id_diag="PK_INTEGRIDADE_002",
            tabela=tabela,
            coluna=pk_col,
            origem=origem,
            severidade="ALERTA",
            categoria="QUALIDADE_DADOS",
            mensagem="Chave primária contém valores nulos.",
            detalhe=f"{dados['percentual_nulos']:.2f}% ({dados['nulos_count']} registros) da PK '{pk_col}' são nulos.",
            recomendacao="Tratar valores nulos na PK, pois violam restrições de unicidade/obrigatoriedade.",
            evidencia=dados
        ))

    return diagnosticos