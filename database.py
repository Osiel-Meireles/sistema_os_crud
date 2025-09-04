import os
import time
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import OperationalError
from datetime import datetime

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "ordens_servico")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "1234")

# Cache da conexão para que a aplicação não precise recriar a cada vez
_engine = None

def get_connection():
    """
    Cria e retorna uma conexão com o banco de dados.
    """
    global _engine
    if _engine is None:
        engine_url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
        _engine = create_engine(engine_url)
    return _engine

def gerar_proximo_numero_os(con, table_name):
    ano_atual = datetime.now().strftime('%y')
    sufixo_ano = f"%-{ano_atual}"

    query = text(f"""
        SELECT COALESCE(MAX(CAST(SPLIT_PART(numero, '-', 1) AS INTEGER)), 0)
        FROM {table_name}
        WHERE numero LIKE :sufixo
    """)

    resultado = con.execute(query, {"sufixo": sufixo_ano}).scalar()
    proximo_sequencial = resultado + 1
    novo_numero_os = f"{proximo_sequencial}-{ano_atual}"
    return novo_numero_os

# --- FUNÇÃO CORRIGIDA ABAIXO ---
def init_db(engine): 
    """
    Cria as tabelas no banco de dados se elas não existirem, usando o engine fornecido.
    """
    try:
        with Session(engine) as session:
            # Definição da tabela os_interna
            session.execute(text("""
            CREATE TABLE IF NOT EXISTS os_interna (
                id SERIAL PRIMARY KEY, numero VARCHAR(255) UNIQUE, secretaria VARCHAR(255),
                setor VARCHAR(255), data DATE, hora TIME, solicitante VARCHAR(255),
                telefone VARCHAR(255), solicitacao_cliente TEXT, categoria VARCHAR(255),
                patrimonio VARCHAR(255), equipamento VARCHAR(255), descricao TEXT,
                servico_executado TEXT, status VARCHAR(255), data_finalizada DATE,
                data_retirada DATE, retirada_por VARCHAR(255), tecnico VARCHAR(255),
                assinatura_solicitante_entrada TEXT, assinatura_solicitante_retirada TEXT
            )
            """))

            # Definição da tabela os_externa
            session.execute(text("""
            CREATE TABLE IF NOT EXISTS os_externa (
                id SERIAL PRIMARY KEY, numero VARCHAR(255) UNIQUE, secretaria VARCHAR(255),
                setor VARCHAR(255), data DATE, hora TIME, solicitante VARCHAR(255),
                telefone VARCHAR(255), solicitacao_cliente TEXT, categoria VARCHAR(255),
                patrimonio VARCHAR(255), equipamento VARCHAR(255), descricao TEXT,
                servico_executado TEXT, status VARCHAR(255), data_finalizada DATE,
                data_retirada DATE, retirada_por VARCHAR(255), tecnico VARCHAR(255),
                assinatura_solicitante_entrada TEXT, assinatura_solicitante_retirada TEXT
            )
            """))
            session.commit()
    except Exception as e:
        print(f"ERRO AO CRIAR AS TABELAS: {e}")
        raise e
