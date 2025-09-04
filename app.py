import streamlit as st
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
import time
import os

# --- INÍCIO DA LÓGICA DE INICIALIZAÇÃO E AUTOCORREÇÃO ---

# Pega as credenciais do ambiente
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "ordens_servico")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "1234")

@st.cache_resource(show_spinner="Conectando e configurando o banco de dados...")
def initialize_database():
    """
    Garante que o banco de dados e as tabelas existam.
    Isso roda apenas uma vez graças ao @st.cache_resource.
    """
    try:
        # 1. Conecta ao servidor PostgreSQL (sem especificar um banco)
        default_engine_url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/postgres"
        engine = create_engine(default_engine_url)
        
        # Tenta conectar ao servidor por até 50 segundos
        retries = 10
        for i in range(retries):
            try:
                with engine.connect() as connection:
                    print("Conexão com o servidor PostgreSQL estabelecida.")
                    
                    # 2. Verifica se o banco de dados 'ordens_servico' existe
                    result = connection.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{DB_NAME}'"))
                    db_exists = result.scalar() == 1
                    
                    if not db_exists:
                        print(f"O banco de dados '{DB_NAME}' não existe. Criando...")
                        # CORREÇÃO: Finaliza a transação atual antes de criar o banco
                        connection.commit() 
                        # Define o nível de isolamento para AUTOCOMMIT
                        connection.execution_options(isolation_level="AUTOCOMMIT").execute(text(f'CREATE DATABASE "{DB_NAME}"'))
                        print(f"Banco de dados '{DB_NAME}' criado com sucesso.")
                    else:
                        print(f"O banco de dados '{DB_NAME}' já existe.")
                    
                    # 3. Agora conecta ao banco 'ordens_servico' e cria as tabelas
                    db_engine_url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
                    db_engine = create_engine(db_engine_url)
                    from database import init_db
                    init_db(db_engine) # Passa o engine para a função
                    print("Tabelas verificadas/criadas com sucesso.")
                    
                    return db_engine # Retorna o engine da conexão para ser usado pela aplicação
            
            except OperationalError:
                print(f"Servidor PostgreSQL ainda não está pronto... Tentativa {i+1}/{retries}")
                time.sleep(5)
        
        st.error("Não foi possível conectar ao servidor PostgreSQL após múltiplas tentativas.")
        return None

    except Exception as e:
        st.error(f"Ocorreu um erro inesperado ao inicializar o banco de dados: {e}")
        return None

# Executa a inicialização. Se falhar, a aplicação para aqui.
conn_engine = initialize_database()
if conn_engine is None:
    st.stop()

# --- FIM DA LÓGICA DE INICIALIZAÇÃO ---

# O resto do seu código da aplicação continua aqui
from database import get_connection
import os_interna, os_externa, filtro, dar_baixa, dashboard

st.set_page_config(layout="wide")
st.image("Secretaria_da_Fazenda-removebg-preview.png", width=600)
st.markdown("<h2 style='text-align: left;'>Sistema de Registro de Ordens de Serviço</h2>", unsafe_allow_html=True)

if 'page' not in st.session_state:
    st.session_state.page = "Home"

# ... (o resto do seu código de UI de app.py permanece o mesmo) ...

st.sidebar.markdown("<h3 style='text-align: left;'>Navegação</h3>", unsafe_allow_html=True)
if st.sidebar.button("Tela Inicial", use_container_width=True): st.session_state.page = "Home"
if st.sidebar.button("Dashboard", use_container_width=True): st.session_state.page = "Dashboard"
if st.sidebar.button("Ordem de Serviço Interna", use_container_width=True): st.session_state.page = "OS Interna"
if st.sidebar.button("Ordem de Serviço Externa", use_container_width=True): st.session_state.page = "OS Externa"
if st.sidebar.button("Filtrar Ordem de Serviço", use_container_width=True): st.session_state.page = "Filtrar OS"
if st.sidebar.button("Atualizar Ordem de Serviço", use_container_width=True): st.session_state.page = "Dar Baixa em OS"

if st.session_state.page == "Home":
    st.markdown("<h3 style='text-align: left;'>Bem-vindo(a)!</h3>", unsafe_allow_html=True)
    st.write("Selecione uma das opções abaixo para começar.")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Ordens de Serviço Internas", use_container_width=True): st.session_state.page = "OS Interna"
        if st.button("Filtrar Ordens de Serviço", use_container_width=True): st.session_state.page = "Filtrar OS"
    with col2:
        if st.button("Ordens de Serviço Externas", use_container_width=True): st.session_state.page = "OS Externa"
        if st.button("Atualizar Ordens de Serviço", use_container_width=True): st.session_state.page = "Dar Baixa em OS"
elif st.session_state.page == "Dashboard": dashboard.render()
elif st.session_state.page == "OS Interna": os_interna.render()
elif st.session_state.page == "OS Externa": os_externa.render()
elif st.session_state.page == "Filtrar OS": filtro.render()
elif st.session_state.page == "Dar Baixa em OS": dar_baixa.render()
