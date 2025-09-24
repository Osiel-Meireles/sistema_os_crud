import os
import time
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import OperationalError
from datetime import datetime

# A variável _engine será populada exclusivamente pelo app.py após a inicialização segura.
_engine = None

def get_connection():
    """
    Retorna o engine de banco de dados global, que DEVE ser inicializado
    pelo script principal app.py.
    """
    if _engine is None:
        # Esta exceção garante que a aplicação pare imediatamente se a conexão
        # não for estabelecida pelo caminho correto, evitando erros ambíguos.
        raise RuntimeError("O engine do banco de dados não foi inicializado. O script app.py principal deve inicializar a conexão.")
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

def init_db(engine):
    try:
        with Session(engine) as session:
            session.execute(text("""
            CREATE TABLE IF NOT EXISTS os_interna (
                id SERIAL PRIMARY KEY, numero VARCHAR(255) UNIQUE, secretaria VARCHAR(255),
                setor VARCHAR(255), data DATE, hora TIME, solicitante VARCHAR(255),
                telefone VARCHAR(255), solicitacao_cliente TEXT, categoria VARCHAR(255),
                patrimonio VARCHAR(255), equipamento VARCHAR(255), descricao TEXT,
                servico_executado TEXT, status VARCHAR(255),
                data_finalizada TIMESTAMP WITH TIME ZONE,
                data_retirada TIMESTAMP WITH TIME ZONE,
                retirada_por VARCHAR(255),
                tecnico VARCHAR(255),
                laudo_filename VARCHAR(255),
                laudo_pdf BYTEA
            )
            """))

            session.execute(text("""
            CREATE TABLE IF NOT EXISTS os_externa (
                id SERIAL PRIMARY KEY, numero VARCHAR(255) UNIQUE, secretaria VARCHAR(255),
                setor VARCHAR(255), data DATE, hora TIME, solicitante VARCHAR(255),
                telefone VARCHAR(255), solicitacao_cliente TEXT, categoria VARCHAR(255),
                patrimonio VARCHAR(255), equipamento VARCHAR(255), descricao TEXT,
                servico_executado TEXT, status VARCHAR(255),
                data_finalizada TIMESTAMP WITH TIME ZONE,
                data_retirada TIMESTAMP WITH TIME ZONE,
                retirada_por VARCHAR(255),
                tecnico VARCHAR(255),
                laudo_filename VARCHAR(255),
                laudo_pdf BYTEA
            )
            """))
            session.commit()
    except Exception as e:
        print(f"ERRO AO CRIAR AS TABELAS: {e}")
        raise e