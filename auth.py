# CÓDIGO ATUALIZADO E COMPLETO PARA: sistema_os_crud-main/auth.py

from passlib.context import CryptContext
from sqlalchemy import text
from database import get_connection
import re 

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Gera o hash de uma senha."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a senha simples corresponde ao hash."""
    return pwd_context.verify(plain_password, hashed_password)

def validate_password(password):
    """Valida se a senha tem min 8 chars, 1 maiúscula, 1 minúscula, 1 número, 1 especial."""
    if len(password) < 8: return False, "A senha deve ter pelo menos 8 caracteres."
    if not re.search(r"[A-Z]", password): return False, "A senha deve ter pelo menos uma letra maiúscula."
    if not re.search(r"[a-z]", password): return False, "A senha deve ter pelo menos uma letra minúscula."
    if not re.search(r"\d", password): return False, "A senha deve ter pelo menos um número."
    if not re.search(r"[!@#$%^&*(),.?:{}|<>]", password): return False, "A senha deve ter pelo menos um caractere especial."
    return True, ""

# --- FUNÇÃO ATUALIZADA ---
def authenticate_user(conn, username: str, password: str):
    """
    Busca o usuário no banco e verifica a senha.
    Retorna os dados do usuário se for válido, senão None.
    """
    try:
        with conn.connect() as con:
            # Puxa o display_name e usa o username como fallback
            query = text("""
                SELECT *, COALESCE(display_name, username) as display_name 
                FROM usuarios 
                WHERE username = :username
            """)
            result = con.execute(query, {"username": username}).fetchone()
            
            if not result:
                return None # Usuário não encontrado
            
            user_data = result._mapping
            
            if not verify_password(password, user_data['password_hash']):
                return None # Senha incorreta
                
            return user_data # Retorna o dict completo, incluindo display_name
            
    except Exception as e:
        print(f"Erro na autenticação: {e}")
        return None
# --- FIM DA ATUALIZAÇÃO ---

def update_user_password(conn, username: str, new_password: str) -> bool:
    """
    Atualiza o hash da senha de um usuário específico no banco de dados.
    """
    try:
        new_password_hash = hash_password(new_password)
        with conn.connect() as con:
            with con.begin():
                query = text("""
                    UPDATE usuarios
                    SET password_hash = :password_hash
                    WHERE username = :username
                """)
                con.execute(query, {"password_hash": new_password_hash, "username": username})
        return True
    except Exception as e:
        print(f"Erro ao atualizar senha: {e}")
        return False