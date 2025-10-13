import streamlit as st
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
import time
import os
import database  # Importa o módulo database

# ===============================
# CONFIGURAÇÃO DE VARIÁVEIS
# ===============================
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "ordens_servico")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "1234")

# ===============================
# CONEXÃO RESILIENTE AO BANCO
# ===============================
@st.cache_resource(show_spinner="Conectando e configurando o banco de dados...", ttl=300)
def initialize_database():
    """
    Garante que o banco de dados exista e cria o engine resiliente,
    com tentativas automáticas e reconexão segura.
    """
    retries = 10
    for i in range(retries):
        try:
            # 1️⃣ Tenta conectar ao banco principal (assumindo que o wait-for-db.sh já o criou)
            db_engine_url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
            db_engine = create_engine(
                db_engine_url,
                pool_pre_ping=True,
                pool_size=10,
                max_overflow=20,
                pool_recycle=3600
            )

            # 2️⃣ Testa a conexão
            with db_engine.connect() as connection:
                connection.execute(text("SELECT 1"))
                print(f"✅ Conexão com o banco '{DB_NAME}' bem-sucedida.")

                # 3️⃣ Garante que as tabelas existam
                from database import init_db
                init_db(db_engine)
                print("✅ Tabelas verificadas/criadas com sucesso.")
                return db_engine

        except OperationalError as e:
            print(f"⏳ Banco ainda não está pronto ({i+1}/{retries}): {e}")
            if i < retries - 1:
                time.sleep(5)
            else:
                st.error(f"❌ Não foi possível conectar ao banco de dados após múltiplas tentativas: {e}")
                return None

    st.error("❌ Falha ao inicializar a conexão com o banco de dados.")
    return None

# Inicializa a conexão com o banco
conn_engine = initialize_database()
if conn_engine is None:
    st.error("🔴 Sistema indisponível. Por favor, contate o administrador.")
    st.stop()
else:
    database._engine = conn_engine

# ===============================
# IMPORTAÇÃO DAS PÁGINAS
# ===============================
import os_interna, os_externa, filtro, dar_baixa, dashboard

# ===============================
# CONFIGURAÇÃO VISUAL DO APP
# ===============================
st.set_page_config(layout="wide")
st.image("Secretaria_da_Fazenda-removebg-preview.png", width=600)
st.markdown("<h2 style='text-align: left;'>Sistema de Registro de Ordens de Serviço</h2>", unsafe_allow_html=True)

# ===============================
# CONTROLE DE NAVEGAÇÃO
# ===============================
if 'page' not in st.session_state:
    st.session_state.page = "Home"

st.sidebar.markdown("<h3 style='text-align: left;'>Navegação</h3>", unsafe_allow_html=True)
if st.sidebar.button("Tela Inicial", use_container_width=True): st.session_state.page = "Home"
if st.sidebar.button("Dashboard", use_container_width=True): st.session_state.page = "Dashboard"
if st.sidebar.button("Ordem de Serviço Interna", use_container_width=True): st.session_state.page = "OS Interna"
if st.sidebar.button("Ordem de Serviço Externa", use_container_width=True): st.session_state.page = "OS Externa"
if st.sidebar.button("Filtrar Ordem de Serviço", use_container_width=True): st.session_state.page = "Filtrar OS"
if st.sidebar.button("Atualizar Ordem de Serviço", use_container_width=True): st.session_state.page = "Dar Baixa em OS"

# ===============================
# PÁGINA INICIAL
# ===============================
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

# ===============================
# RENDERIZAÇÃO DAS PÁGINAS
# ===============================
elif st.session_state.page == "Dashboard": 
    dashboard.render()
elif st.session_state.page == "OS Interna": 
    os_interna.render()
elif st.session_state.page == "OS Externa": 
    os_externa.render()
elif st.session_state.page == "Filtrar OS": 
    filtro.render()
elif st.session_state.page == "Dar Baixa em OS": 
    dar_baixa.render()
