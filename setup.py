from database import init_db
from import_export import importar_os_interna, importar_os_externa
import os

if __name__ == '__main__':
    print("Iniciando a configuração do banco de dados...")
    
    # 1. Inicializar as tabelas
    try:
        init_db()
        print("Tabelas do banco de dados inicializadas com sucesso.")
    except Exception as e:
        print(f"Erro ao inicializar as tabelas: {e}")
        # Retorna para o usuário a mensagem de erro
    
    # 2. Importar dados iniciais do arquivo SQLite, se existir
    sqlite_db_path = "ordens_servico.db"
    if os.path.exists(sqlite_db_path):
        from migrate_data import migrate_data
        print("Migrando dados do arquivo SQLite...")
        try:
            migrate_data()
            print("Migração de dados do SQLite concluída.")
        except Exception as e:
            print(f"Erro na migração de dados do SQLite: {e}")
            
    print("Configuração do sistema concluída. Você pode agora executar o app.py.")