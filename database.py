# CÓDIGO ATUALIZADO E COMPLETO PARA: sistema_os_crud-main/database.py

import os
import time
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import OperationalError
from datetime import datetime

_engine = None

def get_connection():
    if _engine is None:
        raise RuntimeError("O engine do banco de dados não foi inicializado...")
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
            
            # --- Tabela OS Interna (Inalterada) ---
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
                registrado_por VARCHAR(100),
                laudo_filename VARCHAR(255),
                laudo_pdf BYTEA
            )
            """))

            # --- Tabela OS Externa (Inalterada) ---
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
                registrado_por VARCHAR(100),
                laudo_filename VARCHAR(255),
                laudo_pdf BYTEA
            )
            """))

            # --- Tabela Equipamentos (Inalterada) ---
            session.execute(text("""
            CREATE TABLE IF NOT EXISTS equipamentos (
                id SERIAL PRIMARY KEY,
                categoria VARCHAR(255) NOT NULL,
                patrimonio VARCHAR(255),
                hostname VARCHAR(255) NOT NULL,
                especificacao TEXT NOT NULL,
                secretaria VARCHAR(255) NOT NULL,
                setor VARCHAR(255),
                localizacao_fisica VARCHAR(255),
                ip VARCHAR(255) UNIQUE,
                mac VARCHAR(255) UNIQUE,
                subrede VARCHAR(255),
                gateway VARCHAR(255),
                dns VARCHAR(255),
                numero_serie VARCHAR(255),
                observacoes TEXT,
                data_registro TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
            """))

            # --- Tabela Laudos (Inalterada) ---
            session.execute(text("""
            CREATE TABLE IF NOT EXISTS laudos (
                id SERIAL PRIMARY KEY,
                tipo_os VARCHAR(50) NOT NULL,
                numero_os VARCHAR(255) NOT NULL,
                componente VARCHAR(255) NOT NULL,
                especificacao TEXT NOT NULL,
                link_compra VARCHAR(1024),
                observacoes TEXT,
                tecnico VARCHAR(255) NOT NULL,
                status VARCHAR(100) NOT NULL DEFAULT 'PENDENTE',
                data_registro TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                data_atendimento TIMESTAMP WITH TIME ZONE
            )
            """))
            
            session.execute(text("CREATE INDEX IF NOT EXISTS idx_laudos_numero_os ON laudos (numero_os, tipo_os)"))
            
            # --- ATUALIZAÇÃO DA TABELA DE USUÁRIOS ---
            session.execute(text("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role VARCHAR(50) NOT NULL CHECK (role IN ('admin', 'tecnico', 'administrativo')),
                display_name VARCHAR(255), -- <-- NOVA COLUNA
                data_registro TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
            """))
            
            # --- MIGRAÇÃO AUTOMÁTICA ---
            session.execute(text("ALTER TABLE os_interna ADD COLUMN IF NOT EXISTS registrado_por VARCHAR(100);"))
            session.execute(text("ALTER TABLE os_externa ADD COLUMN IF NOT EXISTS registrado_por VARCHAR(100);"))
            # --- ADICIONA A NOVA COLUNA SE ELA NÃO EXISTIR ---
            session.execute(text("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS display_name VARCHAR(255);"))
            # --- FIM DA MIGRAÇÃO ---

            session.commit()
    except Exception as e:
        print(f"ERRO AO CRIAR AS TABELAS: {e}")
        raise e