import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "ordens_servico_dev")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "1234")

def get_connection():
    engine_url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
    return create_engine(engine_url)

def gerar_proximo_numero_os(con, table_name):
    # ... (código da função sem alterações)
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
            session.execute(text("""
            CREATE TABLE IF NOT EXISTS os_interna (
                id SERIAL PRIMARY KEY,
                numero VARCHAR(255) UNIQUE,
                secretaria VARCHAR(255),
                setor VARCHAR(255),
                data DATE,
                hora TIME,
                solicitante VARCHAR(255),
                telefone VARCHAR(255),
                solicitacao_cliente TEXT,
                categoria VARCHAR(255),
                patrimonio VARCHAR(255),
                equipamento VARCHAR(255),
                descricao TEXT,
                servico_executado TEXT,
                status VARCHAR(255),
                data_finalizada DATE,
                data_retirada DATE,
                retirada_por VARCHAR(255),
                tecnico VARCHAR(255),
                assinatura_solicitante_entrada TEXT,
                assinatura_solicitante_retirada TEXT,
                cpf_retirada VARCHAR(14)
            )
            """))

            session.execute(text("""
            CREATE TABLE IF NOT EXISTS os_externa (
                id SERIAL PRIMARY KEY,
                numero VARCHAR(255) UNIQUE,
                secretaria VARCHAR(255),
                setor VARCHAR(255),
                data DATE,
                hora TIME,
                solicitante VARCHAR(255),
                telefone VARCHAR(255),
                solicitacao_cliente TEXT,
                categoria VARCHAR(255),
                patrimonio VARCHAR(255),
                equipamento VARCHAR(255),
                descricao TEXT,
                servico_executado TEXT,
                status VARCHAR(255),
                data_finalizada DATE,
                data_retirada DATE,
                retirada_por VARCHAR(255),
                tecnico VARCHAR(255),
                assinatura_solicitante_entrada TEXT,
                assinatura_solicitante_retirada TEXT,
                cpf_retirada VARCHAR(14)
            )
            """))
            session.commit()
    except Exception as e:
        print(f"ERRO AO INICIAR O BANCO DE DADOS: {e}")
        raise e