from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from database import init_db, DB_USER, DB_PASSWORD, DB_HOST, DB_NAME
import time

def check_and_create_db():
    """
    Verifica se o banco de dados principal existe e o cria se necessário.
    """
    try:
        # Tenta conectar ao banco de dados padrão 'postgres'
        default_engine_url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/postgres"
        engine = create_engine(default_engine_url)
        
        retries = 10
        for i in range(retries):
            try:
                with engine.connect() as connection:
                    print("Conexão com o servidor PostgreSQL estabelecida.")
                    # Verifica se o banco de dados existe
                    result = connection.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{DB_NAME}'"))
                    db_exists = result.scalar() == 1
                    
                    if not db_exists:
                        print(f"O banco de dados '{DB_NAME}' não existe. Criando...")
                        # Precisamos de uma conexão com isolamento para criar o banco
                        connection.execution_options(isolation_level="AUTOCOMMIT").execute(text(f'CREATE DATABASE "{DB_NAME}"'))
                        print(f"Banco de dados '{DB_NAME}' criado com sucesso.")
                    else:
                        print(f"O banco de dados '{DB_NAME}' já existe.")
                    return True # Sucesso
            except OperationalError as e:
                print(f"Servidor PostgreSQL ainda não está pronto... Tentativa {i+1}/{retries}")
                time.sleep(5)
        
        print("Não foi possível conectar ao servidor PostgreSQL após várias tentativas.")
        return False

    except Exception as e:
        print(f"Ocorreu um erro inesperado ao verificar/criar o banco de dados: {e}")
        return False

if __name__ == '__main__':
    print("Iniciando a configuração do banco de dados...")
    
    if check_and_create_db():
        try:
            print("Verificando/Criando tabelas...")
            init_db()
            print("Tabelas do banco de dados verificadas/criadas com sucesso.")
        except Exception as e:
            print(f"Erro ao inicializar as tabelas: {e}")
            
    print("Configuração do sistema concluída. Executando a aplicação...")
