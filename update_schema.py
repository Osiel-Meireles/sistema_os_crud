# CÓDIGO ATUALIZADO E COMPLETO PARA: sistema_os_crud-main/update_schema.py

import os
from sqlalchemy import create_engine, text

def migrate_schema():
    print("--- Iniciando migração de schema (Adicionando 'administrativo' role) ---")
    
    # --- ALTERAÇÃO AQUI ---
    # Lê as variáveis de ambiente do contêiner onde o script está rodando.
    # Removemos os defaults ("localhost", "5434", etc.) que causaram o erro.
    DB_HOST = os.getenv("DB_HOST")
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_PORT = "5432" # Na rede interna do Docker, a porta do Postgres é sempre 5432

    # Verifica se as variáveis foram carregadas
    if not all([DB_HOST, DB_NAME, DB_USER, DB_PASSWORD]):
        print("\n❌ ERRO: Variáveis de ambiente (DB_HOST, DB_NAME, etc.) não foram carregadas.")
        print("Certifique-se de que o contêiner 'app' está rodando ('docker compose up -d').")
        return
    # --- FIM DA ALTERAÇÃO ---

    db_engine_url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    try:
        engine = create_engine(db_engine_url)
        with engine.connect() as con:
            with con.begin():
                print("1. Removendo a antiga constraint 'usuarios_role_check'...")
                con.execute(text("ALTER TABLE usuarios DROP CONSTRAINT IF EXISTS usuarios_role_check;"))
                
                print("2. Adicionando a nova constraint 'usuarios_role_check' com 'administrativo'...")
                con.execute(text("""
                    ALTER TABLE usuarios
                    ADD CONSTRAINT usuarios_role_check
                    CHECK (role IN ('admin', 'tecnico', 'administrativo'));
                """))
            
            print("\n✅ Schema atualizado com sucesso!")

    except Exception as e:
        print(f"\n❌ Falha ao migrar o schema: {e}")

if __name__ == "__main__":
    migrate_schema()
