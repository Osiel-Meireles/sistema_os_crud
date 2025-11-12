# CÓDIGO ATUALIZADO E COMPLETO PARA: sistema_os_crud-main/app.py

import streamlit as st
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
import time
import os
import database  
from auth import authenticate_user 

@st.cache_resource(show_spinner="Conectando e configurando o banco de dados...", ttl=300)
def initialize_database():
    retries = 10
    for i in range(retries):
        try:
            DB_HOST = os.getenv("DB_HOST", "localhost")
            DB_NAME = os.getenv("DB_NAME", "ordens_servico")
            DB_USER = os.getenv("DB_USER", "postgres")
            DB_PASSWORD = os.getenv("DB_PASSWORD", "1234")
            db_engine_url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
            db_engine = create_engine(db_engine_url, pool_pre_ping=True, pool_size=10, max_overflow=20, pool_recycle=3600)
            with db_engine.connect() as connection:
                connection.execute(text("SELECT 1"))
                print(f"✅ Conexão com o banco '{DB_NAME}' bem-sucedida.")
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

conn_engine = initialize_database()
if conn_engine is None:
    st.error("🔴 Sistema indisponível. Por favor, contate o administrador.")
    st.stop()
else:
    database._engine = conn_engine

# ===============================
# IMPORTAÇÃO DAS PÁGINAS
# ===============================
import registrar_os, filtro, dar_baixa, dashboard
import laudos, equipamentos, gerenciar_usuarios, minha_conta, minhas_tarefas
import editar_os # <-- IMPORTA A NOVA PÁGINA

# ===============================
# FUNÇÃO DA TELA DE LOGIN
# ===============================
def render_login_page():
    st.set_page_config(layout="centered")
    st.image("Secretaria da Fazenda.png", width=300)
    st.title("Login - Sistema de Ordens de Serviço")
    with st.form("login_form"):
        username = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        submitted = st.form_submit_button("Entrar", use_container_width=True, type="primary")
        if submitted:
            if not username or not password:
                st.error("Por favor, preencha o usuário e a senha.")
            else:
                user_data = authenticate_user(conn_engine, username, password)
                if user_data:
                    st.session_state.logged_in = True
                    st.session_state.username = user_data['username']
                    st.session_state.role = user_data['role']
                    st.session_state.display_name = user_data['display_name'] 
                    
                    if user_data['role'] == 'tecnico':
                        st.session_state.page = "Minhas Tarefas"
                    else:
                        st.session_state.page = "Dashboard"
                    st.success("Login bem-sucedido!")
                    st.rerun()
                else:
                    st.error("Usuário ou senha inválido.")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if not st.session_state.logged_in:
    render_login_page()
    st.stop() 

st.set_page_config(layout="wide")
st.markdown("<h2 style='text-align: left;'>Sistema de Registro de Ordens de Serviço</h2>", unsafe_allow_html=True)

# ===============================
# CONTROLE DE NAVEGAÇÃO (PÓS-LOGIN)
# ===============================
USER_ROLE = st.session_state.get('role', 'tecnico') 
USERNAME = st.session_state.get('username', '')
DISPLAY_NAME = st.session_state.get('display_name', USERNAME) 

if 'page' not in st.session_state:
    if USER_ROLE == 'tecnico':
        st.session_state.page = "Minhas Tarefas"
    else:
        st.session_state.page = "Dashboard"

st.sidebar.image("Secretaria da Fazenda.png", use_container_width=True)
st.sidebar.markdown(f"Usuário: **{DISPLAY_NAME}**") 
st.sidebar.markdown(f"Função: **{USER_ROLE.capitalize()}**")

if USER_ROLE == 'tecnico':
    if st.sidebar.button("Minhas Tarefas", use_container_width=True): 
        st.session_state.page = "Minhas Tarefas"
st.sidebar.markdown("<h3 style='text-align: left;'>Navegação</h3>", unsafe_allow_html=True)
if USER_ROLE in ['admin', 'administrativo']: 
    if st.sidebar.button("Dashboard", use_container_width=True): st.session_state.page = "Dashboard"
if st.sidebar.button("Registrar Ordem de Serviço", use_container_width=True): st.session_state.page = "Registrar OS"
if st.sidebar.button("Filtrar Ordem de Serviço", use_container_width=True): st.session_state.page = "Filtrar OS"
if st.sidebar.button("Atualizar Ordem de Serviço", use_container_width=True): st.session_state.page = "Dar Baixa em OS"
if USER_ROLE in ['admin', 'tecnico']:
    if st.sidebar.button("Registro de Laudos", use_container_width=True): st.session_state.page = "Laudos"
st.sidebar.markdown("---")
if USER_ROLE == 'admin':
    st.sidebar.markdown("**Administração**") 
    if st.sidebar.button("Registro de Equipamentos", use_container_width=True): st.session_state.page = "Equipamentos"
    if st.sidebar.button("Gerenciar Usuários", use_container_width=True): st.session_state.page = "Gerenciar Usuários"
st.sidebar.markdown("---")
if st.sidebar.button("Minha Conta", use_container_width=True): st.session_state.page = "Minha Conta" 
if st.sidebar.button("Sair", use_container_width=True, type="secondary"):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""
    st.session_state.display_name = "" 
    st.session_state.page = "Dashboard" 
    st.rerun()

# ===============================
# RENDERIZAÇÃO DAS PÁGINAS
# ===============================
if st.session_state.page == "Dashboard" and USER_ROLE in ['admin', 'administrativo']: 
    dashboard.render()
elif st.session_state.page == "Registrar OS": 
    registrar_os.render()
elif st.session_state.page == "Filtrar OS": 
    filtro.render()
elif st.session_state.page == "Dar Baixa em OS": 
    dar_baixa.render()
elif st.session_state.page == "Minha Conta":
    minha_conta.render()
elif st.session_state.page == "Minhas Tarefas" and USER_ROLE == 'tecnico':
    minhas_tarefas.render()
elif st.session_state.page == "Laudos" and USER_ROLE in ['admin', 'tecnico']:
    laudos.render()
elif st.session_state.page == "Equipamentos" and USER_ROLE == 'admin':
    equipamentos.render()
elif st.session_state.page == "Gerenciar Usuários" and USER_ROLE == 'admin':
    gerenciar_usuarios.render()

# --- ADICIONA A ROTA PARA A NOVA PÁGINA ---
elif st.session_state.page == "Editar OS" and USER_ROLE in ['admin', 'administrativo']:
    editar_os.render()
# --- FIM DA ADIÇÃO ---

else:
    st.error("Você não tem permissão para acessar esta página ou a página não existe.")
    if USER_ROLE == 'tecnico':
        st.session_state.page = "Minhas Tarefas"
    else:
        st.session_state.page = "Dashboard"
    st.rerun()