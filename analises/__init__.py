# analises/__init__.py
#
# Este arquivo facilita o carregamento dinâmico das funções de análise
# pelo main_runner.py, que usa importlib para acessar as funções pelo nome.

from .integridade import validacao_chave_primaria
from .numericas import estatisticas_descritivas, teste_de_outliers_iqr, teste_de_outliers_zscore, analise_de_correlacao

# Você pode adicionar as funções de outros módulos aqui conforme você as cria
# Ex: from .categoricas import contagem_de_valores

# O '__all__' define quais objetos são exportados quando um usuário faz 'from analises import *'
__all__ = [
    'validacao_chave_primaria',
    'estatisticas_descritivas',
    'teste_de_outliers_iqr',
    'teste_de_outliers_zscore',
    'analise_de_correlacao'
]