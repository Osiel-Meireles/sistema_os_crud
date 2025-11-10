# CÓDIGO ATUALIZADO E COMPLETO PARA: sistema_os_crud-main/create_admin.py

import os
from sqlalchemy import create_engine, text
import re
import getpass 

try:
    from auth import hash_password, validate_password
except ImportError:
    print("ERRO: Não foi possível encontrar o arquivo 'auth.py'.")
    print("Certifique-se de que o arquivo 'auth.py' com a função 'hash_password' está na mesma pasta.")
    exit()

def create_admin():
    print("--- Assistente de Criação de Usuário ---")
    
    ADMIN_USERNAME = input("Digite o nome de usuário para o novo admin: ")
    if not ADMIN_USERNAME:
        print("Nome de usuário não pode ser vazio.")
        return

    while True:
        ADMIN_PASSWORD = getpass.getpass("Digite a senha para o novo admin: ")
        PASSWORD_CONFIRM = getpass.getpass("Confirme a senha: ")
        if ADMIN_PASSWORD != PASSWORD_CONFIRM:
            print("\nAs senhas não coincidem. Tente novamente.")
            continue
        is_valid, message = validate_password(ADMIN_PASSWORD)
        if not is_valid:
            print(f"\nERRO: Senha inválida: {message}")
            print("Tente novamente.")
            continue
        break

    # --- ALTERAÇÃO AQUI ---
    # Lê as variáveis de ambiente do contêiner.
    DB_HOST = os.getenv("DB_HOST")
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_PORT = "5432" # Na rede interna do Docker, a porta do Postgres é sempre 5432

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
                query_check = text("SELECT id FROM usuarios WHERE username = :username")
                exists = con.execute(query_check, {"username": ADMIN_USERNAME}).fetchone()
                
                if exists:
                    print(f"\nERRO: Usuário '{ADMIN_USERNAME}' já existe.")
                    return

                hashed_pass = hash_password(ADMIN_PASSWORD)
                display_name = ADMIN_USERNAME # Admin usa o username como display_name
                
                query_insert = text("""
                    INSERT INTO usuarios (username, password_hash, role, display_name)
                    VALUES (:username, :password, 'admin', :display_name)
                """)
                con.execute(query_insert, {
                    "username": ADMIN_USERNAME, 
                    "password": hashed_pass,
                    "display_name": display_name
                })
                print(f"\n✅ Usuário admin '{ADMIN_USERNAME}' criado com sucesso!")
    except Exception as e:
        print(f"\n❌ Falha ao criar usuário admin: {e}")

if __name__ == "__main__":
    create_admin()
