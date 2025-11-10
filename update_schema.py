# CÓDIGO PARA O NOVO ARQUIVO: sistema_os_crud-main/update_schema.py

import os
from sqlalchemy import create_engine, text

def migrate_schema():
    print("--- Iniciando migração de schema (Adicionando 'administrativo' role) ---")
    
    # --- Configuração da Conexão com o Banco ---
    # Estas variáveis devem bater com seu 'docker-compose.dev.yml'
    DB_HOST = "localhost"
    DB_NAME = "ordens_servico_dev" # O banco de desenvolvimento
    DB_USER = "postgres"
    DB_PASSWORD = "1234" # A senha do seu 'db-dev'
    DB_PORT = "5434" # A porta do 'docker-compose.dev.yml'
    # --- Fim da Configuração ---
    
    db_engine_url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    try:
        engine = create_engine(db_engine_url)
        with engine.connect() as con:
            with con.begin():
                print("1. Removendo a antiga constraint 'usuarios_role_check'...")
                # O 'IF EXISTS' garante que o script não falhe se já foi removida
                con.execute(text("ALTER TABLE usuarios DROP CONSTRAINT IF EXISTS usuarios_role_check;"))
                
                print("2. Adicionando a nova constraint 'usuarios_role_check' com 'administrativo'...")
                # Adiciona a nova constraint atualizada
                con.execute(text("""
                    ALTER TABLE usuarios
                    ADD CONSTRAINT usuarios_role_check
                    CHECK (role IN ('admin', 'tecnico', 'administrativo'));
                """))
            
            print("\n✅ Schema atualizado com sucesso!")
            print("A função 'administrativo' agora é permitida.")

    except Exception as e:
        print(f"\n❌ Falha ao migrar o schema: {e}")
        if "already exists" in str(e):
             print("INFO: A nova constraint já parece existir. Nenhuma ação foi tomada.")
        else:
            print("Verifique se o banco de dados está rodando (docker compose up -d) e se as credenciais no script estão corretas.")

if __name__ == "__main__":
    migrate_schema()