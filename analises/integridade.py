import pandas as pd
from typing import Dict, Any, List

# ----------------------------------------------------------
# Analise de chave primaria 
# ----------------------------------------------------------

def validacao_chave_primaria(df: pd.DataFrame, colunas: List[str], **parametros: Any) -> Dict[str, Any]:
    """
    Executa a validação de unicidade e nulidade para a(s) coluna(s) de chave primária.
    Assume que a lista 'colunas' contém apenas o nome da chave primária da tabela.
    
    Args:
        df (pd.DataFrame): O DataFrame a ser analisado.
        colunas (List[str]): Lista contendo o nome da coluna da chave primária.
        parametros (Any): Parâmetros adicionais da regra (checar_unicidade, checar_nulos, etc.).

    Returns:
        Dict[str, Any]: Um dicionário padronizado (ResultadoAnalise) com os resultados da validação.
    """
    
    if not colunas:
        return {
            "colunas_alvo": [],
            "status": "ERRO",
            "resumo_texto": "Nenhuma coluna de chave primária fornecida para validação.",
            "dados_resultado": {}
        }
    
    pk_col = colunas[0]
    total_registros = len(df)
    
    if total_registros == 0:
        return {
            "colunas_alvo": colunas,
            "status": "INFO",
            "resumo_texto": "Tabela vazia. Nenhuma validação de PK aplicada.",
            "dados_resultado": {"total_registros": 0}
        }

    # 1. Checagem de Nulidade
    nulos_count = df[pk_col].isnull().sum()
    
    # 2. Checagem de Unicidade
    # Conta todas as linhas que possuem um valor duplicado (mantendo False)
    duplicados_count = df[pk_col].duplicated(keep=False).sum()
    
    # 3. Determinando o Status e Resumo
    if nulos_count > 0 or duplicados_count > 0:
        status_final = "ALERTA"
        resumo = f"Falha na integridade da PK '{pk_col}': {nulos_count} nulos e {duplicados_count} duplicados."
    else:
        status_final = "SUCESSO"
        resumo = f"Chave primária '{pk_col}' validada com sucesso: 100% única e não nula."

    # 4. Estrutura de retorno padronizada
    resultado = {
        "colunas_alvo": colunas,
        "status": status_final,
        "resumo_texto": resumo,
        
        # Payload com os dados para o Diagnóstico
        "dados_resultado": {
            "total_registros": total_registros,
            "coluna_pk": pk_col,
            "nulos_count": int(nulos_count),
            "duplicados_count": int(duplicados_count),
            "percentual_duplicados": (duplicados_count / total_registros) * 100,
            "percentual_nulos": (nulos_count / total_registros) * 100
        }
    }
    
    return resultado