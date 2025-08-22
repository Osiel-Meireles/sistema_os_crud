from database import init_db

if __name__ == '__main__':
    print("Iniciando a configuração do banco de dados...")
    
    try:
        init_db()
        print("Tabelas do banco de dados verificadas/criadas com sucesso.")
    except Exception as e:
        print(f"Erro ao inicializar as tabelas: {e}")
            
    print("Configuração do sistema concluída. Executando a aplicação...")