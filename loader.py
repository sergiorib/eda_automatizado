import pandas as pd
import os
from typing import Union

def load_data(caminho: str, tipo: str) -> pd.DataFrame:
    """
    Carrega um DataFrame com base no caminho e tipo de arquivo.

    Suporta os tipos 'csv' e 'excel'.

    Args:
        caminho (str): Caminho completo ou relativo para o arquivo de dados.
        tipo (str): O tipo de arquivo (ex: 'csv', 'excel').

    Returns:
        pd.DataFrame: O DataFrame carregado.

    Raises:
        FileNotFoundError: Se o caminho do arquivo não for encontrado.
        ValueError: Se o tipo de arquivo não for suportado.
        Exception: Em caso de erro de leitura do arquivo (ex: formato inválido).
    """
    
    # 1. Checagem de Existência do Arquivo
    if not os.path.exists(caminho):
        raise FileNotFoundError(f"Arquivo de dados não encontrado no caminho: {caminho}")

    # 2. Lógica de Carregamento
    df: Union[pd.DataFrame, None] = None
    
    tipo_normalizado = tipo.lower().strip()

    try:
        if tipo_normalizado == 'csv':
            # Parâmetros comuns para robustez do CSV
            df = pd.read_csv(caminho, sep=None, engine='python', encoding='utf-8')
            print(f"   --> Carregado CSV de {len(df)} linhas.")
            
        elif tipo_normalizado == 'excel':
            # Parâmetros comuns para robustez do Excel (assumindo a primeira aba)
            # Para carregar abas específicas, a lógica precisaria de um parâmetro adicional.
            df = pd.read_excel(caminho)
            print(f"   --> Carregado Excel de {len(df)} linhas.")
            
        else:
            raise ValueError(f"Tipo de arquivo não suportado: '{tipo}'. Suportados: 'csv', 'excel'.")

        # 3. Tratamento de Erro Pós-Carregamento
        if df is None:
            raise Exception("DataFrame não foi carregado corretamente.")
            
        return df

    except ValueError as e:
        # Re-raise o erro de tipo não suportado ou erro de leitura específico (ex: formato incorreto)
        raise ValueError(f"Erro ao carregar {caminho} ({tipo}): {e}")
    
    except Exception as e:
        # Captura outros erros de I/O ou processamento
        raise Exception(f"Erro de leitura inesperado em {caminho}: {e}")


# --- Exemplo de Uso (apenas para teste local) ---
# if __name__ == '__main__':
#     # Crie um arquivo 'teste.csv' e 'teste.xlsx' para testar localmente
#     try:
#         # df_csv = load_data('dados/transacoes/vendas_q3.csv', 'csv')
#         # print(f"CSV carregado com colunas: {df_csv.columns.tolist()}")
        
#         # df_excel = load_data('dados/clientes.xlsx', 'excel')
#         # print(f"Excel carregado com colunas: {df_excel.columns.tolist()}")

#         pass
#     except Exception as e:
#         print(f"Falha no teste: {e}")