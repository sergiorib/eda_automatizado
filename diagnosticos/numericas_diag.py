# diagnosticos/numericas_diag.py

from typing import Dict, Any, List
# Importa a função base para a criação do registro
from .base_diagnosticos import criar_registro_diagnostico

# NOTA: A função auxiliar _criar_registro_diagnostico foi removida deste arquivo
# e substituída pela importação de criar_registro_diagnostico.

# ----------------------------------------------------------------------
# Função de Diagnóstico 1: estatisticas_descritivas
# ----------------------------------------------------------------------

def diagnostico_estatistico(resultado_analise: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Gera diagnósticos básicos sobre a distribuição e magnitude das colunas.
    (Ex: Detectar valores Min/Max irreais).
    """
    diagnosticos = []
    tabela = resultado_analise.get('tabela', 'N/A')
    dados = resultado_analise['dados_resultado']
    origem = resultado_analise['tipo_analise']
    
    # Regras de Negócio (Mínimo aceitável)
    REGRAS_MAGNITUDE = {
        'idade': {'min_aceitavel': 18, 'mensagem': "Idade Mínima Irreal"},
        'renda_mensal': {'min_aceitavel': 0.0, 'mensagem': "Renda Negativa/Zero"}
    }
    
    for coluna, stats in dados.items():
        min_valor = stats.get('min')
        
        # Aplica regra de Magnitude Mínima
        if coluna in REGRAS_MAGNITUDE:
            regra = REGRAS_MAGNITUDE[coluna]
            if min_valor < regra['min_aceitavel']:
                diagnosticos.append(criar_registro_diagnostico(
                    id_diag="ESTAT_MAGNITUDE_001",
                    tabela=tabela,
                    coluna=coluna,
                    origem=origem,
                    severidade="CRÍTICO",
                    categoria="QUALIDADE_DADOS",
                    mensagem=regra['mensagem'],
                    detalhe=f"O valor mínimo ({min_valor}) é menor que o limite aceitável ({regra['min_aceitavel']}).",
                    recomendacao="Limpar ou imputar valores mínimos fora do domínio aceitável.",
                    evidencia={"min_encontrado": min_valor, "min_esperado": regra['min_aceitavel']}
                ))
    
    return diagnosticos

# ----------------------------------------------------------------------
# Função de Diagnóstico 2: teste_de_outliers_iqr
# ----------------------------------------------------------------------

def diagnostico_outliers_iqr(resultado_analise: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Interpreta o resultado do teste IQR para emitir alertas.
    """
    diagnosticos = []
    tabela = resultado_analise.get('tabela', 'N/A')
    dados = resultado_analise['dados_resultado']
    origem = resultado_analise['tipo_analise']
    
    for coluna, stats in dados.items():
        outliers_count = stats.get('outliers_count', 0)
        
        if outliers_count > 0:
            # Nota: Percentual preciso requer total de registros. Aqui, apenas emitimos o alerta.
            diagnosticos.append(criar_registro_diagnostico(
                id_diag="OUTLIER_IQR_001",
                tabela=tabela,
                coluna=coluna,
                origem=origem,
                severidade="ALERTA",
                categoria="DISTRIBUIÇÃO",
                mensagem="Outliers detectados por IQR.",
                detalhe=f"{outliers_count} registros são outliers IQR. Limites: [{stats.get('limite_inferior'):.2f}, {stats.get('limite_superior'):.2f}].",
                recomendacao="Investigar a causa e considerar técnicas de tratamento de outliers para modelagem.",
                evidencia={"outliers_count": outliers_count}
            ))
                
    return diagnosticos

# ----------------------------------------------------------------------
# Função de Diagnóstico 3: teste_de_outliers_zscore
# ----------------------------------------------------------------------

def diagnostico_outliers_zscore(resultado_analise: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Interpreta o resultado do teste Z-Score para emitir alertas.
    """
    diagnosticos = []
    tabela = resultado_analise.get('tabela', 'N/A')
    dados = resultado_analise['dados_resultado']
    origem = resultado_analise['tipo_analise']
    
    for coluna, stats in dados.items():
        outliers_count = stats.get('outliers_count', 0)
        
        if outliers_count > 0:
            diagnosticos.append(criar_registro_diagnostico(
                id_diag="OUTLIER_ZSCORE_002",
                tabela=tabela,
                coluna=coluna,
                origem=origem,
                severidade="INFO", 
                categoria="DISTRIBUIÇÃO",
                mensagem="Outliers detectados via Z-Score (forte indicação de não-normalidade).",
                detalhe=f"{outliers_count} registros têm Z-Score > {stats.get('limite_zscore')}. Média={stats.get('mean'):.2f}, DP={stats.get('std'):.2f}.",
                recomendacao="Considerar transformação logarítmica ou não-paramétrica para modelagem.",
                evidencia={"outliers_count": outliers_count}
            ))
                
    return diagnosticos


# ----------------------------------------------------------------------
# Função de Diagnóstico 4: analise_de_correlacao
# ----------------------------------------------------------------------

def diagnostico_correlacao(resultado_analise: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Interpreta a matriz de correlação para identificar pares de alta correlação.
    """
    diagnosticos = []
    tabela = resultado_analise.get('tabela', 'N/A')
    dados = resultado_analise['dados_resultado']
    origem = resultado_analise['tipo_analise']
    
    pares_altos = dados.get('pares_alta_correlacao', [])
    
    if pares_altos:
        
        pares_display = pares_altos[:3] 
        pares_str = ", ".join([f"{p['par'][0]} vs {p['par'][1]} (ρ={p['valor']})" for p in pares_display])
        
        diagnosticos.append(criar_registro_diagnostico(
            id_diag="CORR_ALTA_001",
            tabela=tabela,
            coluna="N/A",
            origem=origem,
            severidade="ALERTA",
            categoria="MODELAGEM",
            mensagem="Alta multicolinearidade potencial detectada.",
            detalhe=f"{len(pares_altos)} pares de colunas exibem alta correlação. Exemplos: {pares_str}.",
            recomendacao="Em modelos preditivos, considere remover ou combinar variáveis correlacionadas (ex: PCA) para evitar multicolinearidade e overfitting.",
            evidencia={"total_pares": len(pares_altos), "pares_completos": pares_altos}
        ))
        
    return diagnosticos