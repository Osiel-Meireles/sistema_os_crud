import os
import time
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import OperationalError
from datetime import datetime

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "ordens_servico_dev")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "1234")

def get_connection(db_name=DB_NAME):
    """
    Cria e retorna uma conexão com um banco de dados específico, com lógica de repetição.
    """
    engine_url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{db_name}"
    retries = 10
    delay = 5  # segundos

    for i in range(retries):
        try:
            engine = create_engine(engine_url)
            connection = engine.connect()
            connection.close()
            print(f"Conexão com o banco de dados '{db_name}' estabelecida com sucesso.")
            return engine
        except OperationalError as e:
            print(f"Erro ao conectar ao banco de dados '{db_name}': {e}")
            if i < retries - 1:
                print(f"Tentativa {i + 1} de {retries}. Nova tentativa em {delay} segundos...")
                time.sleep(delay)
            else:
                print(f"Não foi possível conectar ao banco de dados '{db_name}' após múltiplas tentativas.")
                raise
    return None

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

def init_db():
    """
    Cria as tabelas no banco de dados se elas não existirem.
    """
    engine = get_connection()
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
        print(f"ERRO AO INICIAR O BANCO DE DADOS: {e}")
        raise e
