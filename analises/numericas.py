import pandas as pd
import numpy as np
from typing import Dict, Any, List

# ----------------------------------------------------------------------
# ESTATISTICAS DESCRITIVAS
# ----------------------------------------------------------------------

def estatisticas_descritivas(df: pd.DataFrame, colunas: List[str], **parametros: Any) -> Dict[str, Any]:
    """
    Calcula estatísticas descritivas (count, mean, std, min, max, quartis) 
    para as colunas numéricas especificadas.
    """
    
    percentis_padrao = parametros.get('percentis', [0.25, 0.5, 0.75])
    arredondamento = parametros.get('arredondamento', 4)

    colunas_validas = [col for col in colunas if col in df.columns]
    
    if not colunas_validas:
        return {
            "colunas_alvo": colunas,
            "status": "ERRO",
            "resumo_texto": f"Nenhuma coluna válida foi encontrada no DataFrame para análise estatística.",
            "dados_resultado": {}
        }
    
    df_numerico = df[colunas_validas]
    
    try:
        df_desc = df_numerico.describe(percentiles=percentis_padrao)
        desc_transposta = df_desc.to_dict()
        
        dados_resultado = {}
        for col, stats in desc_transposta.items():
            dados_resultado[col] = {
                k: round(float(v), arredondamento) if isinstance(v, (int, float, np.number)) else v
                for k, v in stats.items()
            }
        
        status_final = "SUCESSO"
        resumo = f"Estatísticas descritivas calculadas para {len(colunas_validas)} coluna(s) numérica(s)."
        
    except Exception as e:
        status_final = "ERRO"
        resumo = f"Erro ao calcular estatísticas descritivas: {e}"
        dados_resultado = {}

    return {
        "colunas_alvo": colunas_validas,
        "status": status_final,
        "resumo_texto": resumo,
        "dados_resultado": dados_resultado
    }

# ----------------------------------------------------------------------
# OUTLIERS (IQR e ZSCORE)
# ----------------------------------------------------------------------

def teste_de_outliers_iqr(df: pd.DataFrame, colunas: List[str], **parametros: Any) -> Dict[str, Any]:
    """
    Identifica outliers usando o método do Intervalo Interquartil (IQR).
    """
    
    multiplicador_iqr = parametros.get('multiplicador_iqr', 1.5)
    
    colunas_validas = [col for col in colunas if col in df.columns]
    dados_resultado = {}
    total_outliers = 0
    
    for col in colunas_validas:
        col_series = df[col].dropna()
        if col_series.empty:
             dados_resultado[col] = {"outliers_count": 0, "status": "Vazio"}
             continue

        Q1 = col_series.quantile(0.25)
        Q3 = col_series.quantile(0.75)
        IQR = Q3 - Q1
        
        limite_inferior = Q1 - (multiplicador_iqr * IQR)
        limite_superior = Q3 + (multiplicador_iqr * IQR)
        
        outliers_count = col_series[
            (col_series < limite_inferior) | (col_series > limite_superior)
        ].count()
        
        total_outliers += outliers_count

        dados_resultado[col] = {
            "outliers_count": int(outliers_count),
            "limite_inferior": float(limite_inferior),
            "limite_superior": float(limite_superior),
            "Q1": float(Q1),
            "Q3": float(Q3)
        }

    status_final = "ALERTA" if total_outliers > 0 else "SUCESSO"
    resumo = f"Teste IQR concluído. Total de outliers encontrados: {total_outliers}."

    return {
        "colunas_alvo": colunas_validas,
        "status": status_final,
        "resumo_texto": resumo,
        "dados_resultado": dados_resultado
    }

def teste_de_outliers_zscore(df: pd.DataFrame, colunas: List[str], **parametros: Any) -> Dict[str, Any]:
    """
    Identifica outliers usando o Z-Score.
    """
    
    limite_zscore = parametros.get('limite_zscore', 3.0)
    
    colunas_validas = [col for col in colunas if col in df.columns]
    dados_resultado = {}
    total_outliers = 0
    
    for col in colunas_validas:
        col_series = df[col].dropna()
        if col_series.empty:
             dados_resultado[col] = {"outliers_count": 0, "status": "Vazio"}
             continue

        # Calcula Z-score
        mean = col_series.mean()
        std = col_series.std()
        
        if std == 0:
            dados_resultado[col] = {"outliers_count": 0, "status": "STD Zero"}
            continue
            
        z_scores = (col_series - mean) / std
        
        outliers_count = z_scores[np.abs(z_scores) > limite_zscore].count()
        total_outliers += outliers_count

        dados_resultado[col] = {
            "outliers_count": int(outliers_count),
            "limite_zscore": limite_zscore,
            "mean": float(mean),
            "std": float(std)
        }

    status_final = "ALERTA" if total_outliers > 0 else "SUCESSO"
    resumo = f"Teste Z-Score concluído. Total de outliers encontrados: {total_outliers} (Z > {limite_zscore})."

    return {
        "colunas_alvo": colunas_validas,
        "status": status_final,
        "resumo_texto": resumo,
        "dados_resultado": dados_resultado
    }

# ----------------------------------------------------------------------
# FUNÇÃO 4: analise_de_correlacao (NOVA)
# ----------------------------------------------------------------------

def analise_de_correlacao(df: pd.DataFrame, colunas: List[str], **parametros: Any) -> Dict[str, Any]:
    """
    Calcula a matriz de correlação entre as colunas numéricas especificadas.
    """
    
    metodo = parametros.get('metodo', 'pearson')
    limite_alta_correlacao = parametros.get('limite_alta_correlacao', 0.90)
    
    colunas_validas = [col for col in colunas if col in df.columns]
    
    if len(colunas_validas) < 2:
        return {
            "colunas_alvo": colunas,
            "status": "INFO",
            "resumo_texto": "Não há colunas suficientes (mínimo 2) para calcular a correlação.",
            "dados_resultado": {}
        }
    
    df_correlacao = df[colunas_validas]
    
    try:
        # Calcular a matriz de correlação
        matriz_correlacao = df_correlacao.corr(method=metodo)
        
        # Encontrar pares com alta correlação
        correlacoes_altas = []
        # Usa .unstack() para transformar a matriz em série (par, valor)
        # Filtra apenas a parte superior da matriz (i < j)
        corr_unstacked = matriz_correlacao.where(
            np.triu(np.ones(matriz_correlacao.shape), k=1).astype(bool)
        ).stack().reset_index()
        corr_unstacked.columns = ['coluna_a', 'coluna_b', 'correlacao']
        
        df_altas = corr_unstacked[np.abs(corr_unstacked['correlacao']) >= limite_alta_correlacao]
        
        for index, row in df_altas.iterrows():
            correlacoes_altas.append({
                "par": [row['coluna_a'], row['coluna_b']],
                "valor": round(row['correlacao'], 4)
            })
            
        status_final = "ALERTA" if len(correlacoes_altas) > 0 else "SUCESSO"
        resumo = f"Análise de correlação ({metodo}) concluída. {len(correlacoes_altas)} pares com alta correlação (|ρ| ≥ {limite_alta_correlacao}) encontrados."
        
    except Exception as e:
        status_final = "ERRO"
        resumo = f"Erro ao calcular a matriz de correlação: {e}"
        matriz_correlacao = None
        correlacoes_altas = []

    return {
        "colunas_alvo": colunas_validas,
        "status": status_final,
        "resumo_texto": resumo,
        "dados_resultado": {
            "matriz_correlacao": matriz_correlacao.round(4).to_dict() if matriz_correlacao is not None else {},
            "pares_alta_correlacao": correlacoes_altas
        }
    }

# ----------------------------------------------------------------------
# 
# ----------------------------------------------------------------------
