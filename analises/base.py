# analises/base.py

import pandas as pd
from typing import Tuple, Optional

def get_total_registros(df: pd.DataFrame) -> int:
    """
    Retorna o número total de registros no DataFrame.
    """
    return len(df)

def get_iqr_boundaries(series: pd.Series, multiplier: float = 1.5) -> Optional[Tuple[float, float]]:
    """
    Calcula os limites inferior e superior para detecção de outliers usando o método IQR.
    """
    
    col_series = series.dropna()
    
    if col_series.empty or len(col_series) < 2:
        return None

    Q1 = col_series.quantile(0.25)
    Q3 = col_series.quantile(0.75)
    IQR = Q3 - Q1
    
    limite_inferior = Q1 - (multiplier * IQR)
    limite_superior = Q3 + (multiplier * IQR)
    
    return (float(limite_inferior), float(limite_superior))

def obter_percentual_nan(df: pd.DataFrame, col: str) -> float:
    """
    Calcula o percentual de valores nulos em uma coluna.
    """
    total_registros = get_total_registros(df)
    
    if total_registros == 0:
        return 0.0
        
    nulos_count = df[col].isnull().sum()
    return (nulos_count / total_registros) * 100.0