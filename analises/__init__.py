# analises/__init__.py

# 1. Importa utilitários da base (se outros módulos precisarem deles)
from .base import get_total_registros, get_iqr_boundaries, obter_percentual_nan

# 2. Importa as funções principais de análise
from .integridade import validacao_chave_primaria
from .numericas import estatisticas_descritivas, teste_de_outliers_iqr, teste_de_outliers_zscore, analise_de_correlacao

# O '__all__' lista todas as funções que o pacote expõe
__all__ = [
    # Utilitários
    'get_total_registros',
    'get_iqr_boundaries',
    'obter_percentual_nan',
    # Análises Principais
    'validacao_chave_primaria',
    'estatisticas_descritivas',
    'teste_de_outliers_iqr',
    'teste_de_outliers_zscore',
    'analise_de_correlacao'
]