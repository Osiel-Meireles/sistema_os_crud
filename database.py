import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

# Configure as suas credenciais de acesso ao PostgreSQL
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "ordens_servico")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "1234")

def get_connection():
    # Cria o engine de conexão SQLAlchemy
    engine_url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
    return create_engine(engine_url)

def init_db():
    engine = get_connection()
    try:
        with Session(engine) as session:
            # Criar tabela OS Interna - Esquema padronizado
            session.execute(text("""
            CREATE TABLE IF NOT EXISTS os_interna (
                id SERIAL PRIMARY KEY,
                numero VARCHAR(255),
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
                tecnico VARCHAR(255)
            )
            """))

            # Criar tabela OS Externa - Esquema padronizado
            session.execute(text("""
            CREATE TABLE IF NOT EXISTS os_externa (
                id SERIAL PRIMARY KEY,
                numero VARCHAR(255),
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
                tecnico VARCHAR(255)
            )
            """))
            session.commit()
    except Exception as e:
        raise e