# data_loader/loader.py

import pandas as pd
import os
from typing import Union

def load_data(caminho: str, tipo: str) -> pd.DataFrame:
    """
    Carrega um DataFrame com base no caminho e tipo de arquivo.
    """
    
    if not os.path.exists(caminho):
        raise FileNotFoundError(f"Arquivo de dados não encontrado no caminho: {caminho}")

    df: Union[pd.DataFrame, None] = None
    tipo_normalizado = tipo.lower().strip()

    try:
        if tipo_normalizado == 'csv':
            # Tenta UTF-8 e, em caso de falha de decodificação, tenta CP1252
            try:
                df = pd.read_csv(caminho, sep=None, engine='python', encoding='utf-8')
            except UnicodeDecodeError:
                print(f"   --> Aviso: UTF-8 falhou. Tentando 'cp1252' para {caminho}")
                df = pd.read_csv(caminho, sep=None, engine='python', encoding='cp1252')
            
            print(f"   --> Carregado CSV de {len(df)} linhas.")
            
        elif tipo_normalizado == 'excel':
            df = pd.read_excel(caminho)
            print(f"   --> Carregado Excel de {len(df)} linhas.")
            
        else:
            raise ValueError(f"Tipo de arquivo não suportado: '{tipo}'. Suportados: 'csv', 'excel'.")

        if df is None:
            raise Exception("DataFrame não foi carregado corretamente.")
            
        return df

    except ValueError as e:
        raise ValueError(f"Erro ao carregar {caminho} ({tipo}): {e}")
    
    except Exception as e:
        raise Exception(f"Erro de leitura inesperado em {caminho}: {e}")