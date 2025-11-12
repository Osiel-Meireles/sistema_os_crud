# CÓDIGO CORRIGIDO PARA: sistema_os_crud-main/create_admin.py

import os
from sqlalchemy import create_engine, text
import re
import getpass 

try:
    from auth import hash_password
except ImportError:
    print("ERRO: Não foi possível encontrar o arquivo 'auth.py'.")
    print("Certifique-se de que o arquivo 'auth.py' com a função 'hash_password' está na mesma pasta.")
    exit()

def validate_password(password):
    """Valida se a senha tem min 8 chars, 1 maiúscula, 1 minúscula, 1 número, 1 especial."""
    if len(password) < 8: return False, "A senha deve ter pelo menos 8 caracteres."
    if not re.search(r"[A-Z]", password): return False, "A senha deve ter pelo menos uma letra maiúscula."
    if not re.search(r"[a-z]", password): return False, "A senha deve ter pelo menos uma letra minúscula."
    if not re.search(r"\d", password): return False, "A senha deve ter pelo menos um número."
    if not re.search(r"[!@#$%^&*(),.?:{}|<>]", password): return False, "A senha deve ter pelo menos um caractere especial."
    return True, ""

def create_admin():
    print("--- Assistente de Criação de Usuário Admin ---")
    
    ADMIN_USERNAME = input("Digite o nome de usuário para o novo admin (ex: admin): ")
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
            print(f"\nERRO: Senha inválida. {message}")
            print("Tente novamente.")
            continue
        
        break

    # --- Configuração da Conexão com o Banco ---
    DB_HOST = os.getenv("DB_HOST", "localhost")
    
    # --- ESTA É A CORREÇÃO ---
    # O banco de dados de desenvolvimento chama-se 'ordens_servico_dev'
    DB_NAME = "ordens_servico_dev"
    # --- FIM DA CORREÇÃO ---
    
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = "1234" # A senha do seu 'db-dev'
    DB_PORT = "5434" # A porta do 'docker-compose.dev.yml'
    
    db_engine_url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    try:
        engine = create_engine(db_engine_url)
        with engine.connect() as con:
            with con.begin():
                # Verifica se o usuário já existe
                query_check = text("SELECT id FROM usuarios WHERE username = :username")
                exists = con.execute(query_check, {"username": ADMIN_USERNAME}).fetchone()
                
                if exists:
                    print(f"\nERRO: Usuário '{ADMIN_USERNAME}' já existe. Nenhuma ação foi tomada.")
                    return

                # Cria o novo usuário
                hashed_pass = hash_password(ADMIN_PASSWORD)
                query_insert = text("""
                    INSERT INTO usuarios (username, password_hash, role)
                    VALUES (:username, :password, 'admin')
                """)
                con.execute(query_insert, {"username": ADMIN_USERNAME, "password": hashed_pass})
                print(f"\n✅ Usuário admin '{ADMIN_USERNAME}' criado com sucesso!")

    except Exception as e:
        print(f"\n❌ Falha ao criar usuário admin: {e}")
        print("Verifique se o banco de dados está rodando (docker compose up -d) e se as credenciais no script estão corretas.")

if __name__ == "__main__":
    create_admin()