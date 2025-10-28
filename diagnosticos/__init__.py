# diagnosticos/__init__.py
#
# Este arquivo facilita o carregamento dinâmico das funções de diagnóstico
# pelo main_runner.py.

from .integridade_diag import diagnostico_chave_primaria
from .numericas_diag import (
    diagnostico_estatistico,
    diagnostico_outliers_iqr,
    diagnostico_outliers_zscore,
    diagnostico_correlacao
)

# Você pode adicionar as funções de outros módulos aqui conforme você as cria
# Ex: from .categorico_diag import diagnostico_contagem

__all__ = [
    'diagnostico_chave_primaria',
    'diagnostico_estatistico',
    'diagnostico_outliers_iqr',
    'diagnostico_outliers_zscore',
    'diagnostico_correlacao'
]