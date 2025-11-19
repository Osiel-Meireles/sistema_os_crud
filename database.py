# CÓDIGO COMPLETO E CORRIGIDO PARA: sistema_os_crud-main/database.py
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


def gerar_proximo_numero_recarga(con):
    """Gera o próximo número de recarga no formato YYYY-SEQUENCIAL (ex: 2025-0001)"""
    ano_atual = datetime.now().strftime('%Y')
    query = text("""
        SELECT COALESCE(MAX(CAST(SPLIT_PART(numero_recarga, '-', 2) AS INTEGER)), 0)
        FROM recargas
        WHERE numero_recarga LIKE :prefixo
    """)
    prefixo = f"{ano_atual}-%"
    resultado = con.execute(query, {"prefixo": prefixo}).scalar()
    proximo_sequencial = resultado + 1
    novo_numero = f"{ano_atual}-{proximo_sequencial:04d}"
    return novo_numero


def init_db(engine):
    try:
        with Session(engine) as session:
            # --- 1. CRIAÇÃO DAS TABELAS EXISTENTES ---
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
                    data_finalizada TIMESTAMP WITH TIME ZONE,
                    data_retirada TIMESTAMP WITH TIME ZONE,
                    retirada_por VARCHAR(255),
                    tecnico VARCHAR(255),
                    registrado_por VARCHAR(100),
                    laudo_filename VARCHAR(255),
                    laudo_pdf BYTEA
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
                    data_finalizada TIMESTAMP WITH TIME ZONE,
                    data_retirada TIMESTAMP WITH TIME ZONE,
                    retirada_por VARCHAR(255),
                    tecnico VARCHAR(255),
                    registrado_por VARCHAR(100),
                    laudo_filename VARCHAR(255),
                    laudo_pdf BYTEA
                )
            """))
            
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
            
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS laudos (
                    id SERIAL PRIMARY KEY,
                    tipo_os VARCHAR(50) NOT NULL,
                    numero_os VARCHAR(255) NOT NULL,
                    estado_conservacao VARCHAR(50),
                    diagnostico TEXT,
                    equipamento_completo VARCHAR(20),
                    observacoes TEXT,
                    tecnico VARCHAR(255) NOT NULL,
                    status VARCHAR(100) NOT NULL DEFAULT 'PENDENTE',
                    data_registro TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    data_atendimento TIMESTAMP WITH TIME ZONE
                )
            """))
            
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(100) UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role VARCHAR(50) NOT NULL CHECK (role IN ('admin', 'tecnico', 'administrativo', 'tecnico_recarga')),
                    display_name VARCHAR(255),
                    data_registro TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # --- RECRIAR TABELA RECARGAS (dropar a antiga e criar a nova) ---
            session.execute(text("DROP TABLE IF EXISTS recargas CASCADE"))
            
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS recargas (
                    id SERIAL PRIMARY KEY,
                    numero_recarga VARCHAR(50) UNIQUE NOT NULL,
                    
                    -- Data e hora de abertura (automáticas)
                    data_abertura DATE NOT NULL,
                    hora_abertura TIME NOT NULL,
                    
                    -- Localização
                    secretaria VARCHAR(100) NOT NULL,
                    localizacao VARCHAR(255) NOT NULL,
                    
                    -- Insumo
                    insumo VARCHAR(255) NOT NULL,
                    
                    -- Status simplificado
                    status VARCHAR(50) NOT NULL DEFAULT 'EM ABERTO'
                        CHECK (status IN ('EM ABERTO', 'AGUARDANDO INSUMO', 'RECARGA FEITA')),
                    
                    -- Responsável e metadados
                    responsavel VARCHAR(100),
                    data_atualizacao TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # --- 2. MIGRAÇÕES AUTOMÁTICAS ---
            session.execute(text("ALTER TABLE os_interna ADD COLUMN IF NOT EXISTS registrado_por VARCHAR(100);"))
            session.execute(text("ALTER TABLE os_externa ADD COLUMN IF NOT EXISTS registrado_por VARCHAR(100);"))
            session.execute(text("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS display_name VARCHAR(255);"))
            
            # Migração da tabela LAUDOS
            session.execute(text("ALTER TABLE laudos DROP COLUMN IF EXISTS componente;"))
            session.execute(text("ALTER TABLE laudos DROP COLUMN IF EXISTS especificacao;"))
            session.execute(text("ALTER TABLE laudos DROP COLUMN IF EXISTS link_compra;"))
            session.execute(text("ALTER TABLE laudos ADD COLUMN IF NOT EXISTS tipo_os VARCHAR(50);"))
            session.execute(text("ALTER TABLE laudos ADD COLUMN IF NOT EXISTS numero_os VARCHAR(255);"))
            session.execute(text("ALTER TABLE laudos ADD COLUMN IF NOT EXISTS estado_conservacao VARCHAR(50);"))
            session.execute(text("ALTER TABLE laudos ADD COLUMN IF NOT EXISTS diagnostico TEXT;"))
            session.execute(text("ALTER TABLE laudos ADD COLUMN IF NOT EXISTS equipamento_completo VARCHAR(20);"))
            
            # --- 3. CRIAÇÃO DE ÍNDICES ---
            session.execute(text("CREATE INDEX IF NOT EXISTS idx_laudos_numero_os ON laudos (numero_os, tipo_os)"))
            session.execute(text("CREATE INDEX IF NOT EXISTS idx_recargas_numero ON recargas (numero_recarga)"))
            session.execute(text("CREATE INDEX IF NOT EXISTS idx_recargas_status ON recargas (status)"))
            session.execute(text("CREATE INDEX IF NOT EXISTS idx_recargas_data ON recargas (data_abertura)"))
            session.execute(text("CREATE INDEX IF NOT EXISTS idx_recargas_secretaria ON recargas (secretaria)"))
            
            session.commit()
            print("✅ Banco de dados inicializado com sucesso!")
            
    except Exception as e:
        print(f"❌ ERRO AO CRIAR AS TABELAS: {e}")
        raise e