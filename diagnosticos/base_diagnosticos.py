# diagnosticos/base_diagnostico.py

from typing import Dict, Any, List

def criar_registro_diagnostico(id_diag: str, tabela: str, coluna: str, origem: str, severidade: str, categoria: str, mensagem: str, detalhe: str, recomendacao: str, evidencia: Dict[str, Any]) -> Dict[str, Any]:
    """
    Função auxiliar que cria o dicionário padronizado de registro de diagnóstico.
    A string 'detalhe' no parâmetro é mapeada para 'detalhe_tecnico' no retorno.
    """
    return {
        "id_diagnostico": id_diag,
        "tabela": tabela,
        "coluna": coluna,
        "tipo_analise_origem": origem,
        "severidade": severidade,
        "categoria": categoria,
        "mensagem_curta": mensagem,
        "detalhe_tecnico": detalhe, 
        "recomendacao": recomendacao,
        "evidencia": evidencia
    }