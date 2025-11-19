# CÓDIGO COMPLETO E ATUALIZADO PARA: sistema_os_crud-main/create_admin.py
import os
from sqlalchemy import create_engine, text
from auth import hash_password

def create_admin_user():
    """Cria um usuário administrador padrão."""
    
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_NAME = os.getenv("DB_NAME", "ordens_servico")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "1234")
    
    db_engine_url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
    engine = create_engine(db_engine_url)
    
    try:
        with engine.connect() as con:
            with con.begin():
                # Verifica se já existe um admin
                result = con.execute(text("SELECT id FROM usuarios WHERE role = 'admin'")).fetchone()
                
                if result:
                    print("⚠️  Já existe um usuário administrador no sistema.")
                    return
                
                # Cria o usuário admin padrão
                username = "admin"
                password = "Admin@123"
                display_name = "Administrador do Sistema"
                password_hash = hash_password(password)
                
                query = text("""
                    INSERT INTO usuarios (username, password_hash, role, display_name)
                    VALUES (:username, :password_hash, :role, :display_name)
                """)
                
                con.execute(query, {
                    "username": username,
                    "password_hash": password_hash,
                    "role": "admin",
                    "display_name": display_name
                })
                
                print("✅ Usuário administrador criado com sucesso!")
                print(f"   Usuário: {username}")
                print(f"   Senha: {password}")
                print("   ⚠️  ALTERE A SENHA APÓS O PRIMEIRO LOGIN!")
    
    except Exception as e:
        print(f"❌ Erro ao criar usuário administrador: {e}")

if __name__ == "__main__":
    create_admin_user()