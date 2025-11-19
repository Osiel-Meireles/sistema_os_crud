# CÓDIGO COMPLETO E ATUALIZADO PARA: sistema_os_crud-main/app.py

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
            
            from database import init_db
            init_db(db_engine)
            
            global _engine
            database._engine = db_engine
            return db_engine
            
        except OperationalError as e:
            print(f"Tentativa {i + 1} de {retries} falhou: {e}")
            if i < retries - 1:
                time.sleep(2)
            else:
                st.error("Não foi possível conectar ao banco de dados após várias tentativas.")
                raise

def show_login_page():
    st.set_page_config(page_title="Sistema de Registro de OS - PMLEM", page_icon="🔐", layout="centered")
    
    st.title("Login - Sistema de Registro de OS - PMLEM")
    
    with st.form("login_form"):
        username = st.text_input("Usuário", placeholder="Digite seu usuário")
        password = st.text_input("Senha", type="password", placeholder="Digite sua senha")
        submitted = st.form_submit_button("Entrar", use_container_width=True)
        
        if submitted:
            if not username or not password:
                st.error("Por favor, preencha todos os campos.")
            else:
                conn_engine = database.get_connection()
                user = authenticate_user(conn_engine, username, password)
                
                if user:
                    st.session_state.authenticated = True
                    st.session_state.username = user['username']
                    st.session_state.role = user['role']
                    st.session_state.display_name = user.get('display_name', user['username'])
                    
                    if user['role'] == "tecnico_recarga":
                        st.session_state.current_page = "Minhas Recargas"
                    elif user['role'] == "tecnico":
                        st.session_state.current_page = "Minhas Tarefas"
                    else:
                        st.session_state.current_page = "Dashboard"
                    
                    st.success(f"Bem-vindo(a), {st.session_state.display_name}!")
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")

def show_main_app():
    st.set_page_config(page_title="Sistema de Registro de OS - PMLEM", page_icon="🏢", layout="wide")
    
    with st.sidebar:
        st.header("Sistema de Registro de OS - PMLEM")
        st.markdown(f"**Usuário:** {st.session_state.get('display_name', st.session_state.get('username', 'N/A'))}")
        st.markdown(f"**Perfil:** {st.session_state.get('role', 'N/A').replace('_', ' ').title()}")
        st.markdown("---")
        
        role = st.session_state.get("role", "")
        
        if 'current_page' not in st.session_state:
            if role == "tecnico_recarga":
                st.session_state.current_page = "Minhas Recargas"
            elif role == "tecnico":
                st.session_state.current_page = "Minhas Tarefas"
            else:
                st.session_state.current_page = "Dashboard"
        
        # TECNICO MENU
        if role == "tecnico":
            if st.button("Minhas Tarefas", use_container_width=True):
                st.session_state.current_page = "Minhas Tarefas"
            
            st.markdown("---")
            
            if st.button("Laudos Técnicos", use_container_width=True):
                st.session_state.current_page = "Laudos"
            
            if st.button("Filtrar OS", use_container_width=True):
                st.session_state.current_page = "Filtrar OS"
            
            if st.button("Dar Baixa", use_container_width=True):
                st.session_state.current_page = "Dar Baixa"
            
            st.markdown("---")
            
            if st.button("Minha Conta", use_container_width=True):
                st.session_state.current_page = "Minha Conta"
            
            st.markdown("---")
            
            if st.button("Sair", use_container_width=True, type="primary"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
        
        # ADMIN MENU
        elif role == "admin":
            if st.button("Dashboard", use_container_width=True):
                st.session_state.current_page = "Dashboard"
            
            st.markdown("---")
            
            if st.button("Registrar OS", use_container_width=True):
                st.session_state.current_page = "Registrar OS"
            
            if st.button("Filtrar OS", use_container_width=True):
                st.session_state.current_page = "Filtrar OS"
            
            if st.button("Dar Baixa", use_container_width=True):
                st.session_state.current_page = "Dar Baixa"
            
            st.markdown("---")
            
            if st.button("Equipamentos", use_container_width=True):
                st.session_state.current_page = "Equipamentos"
            
            if st.button("Minhas Recargas", use_container_width=True):
                st.session_state.current_page = "Minhas Recargas"
            
            if st.button("Laudos", use_container_width=True):
                st.session_state.current_page = "Laudos"
            
            if st.button("Importar Dados", use_container_width=True):
                st.session_state.current_page = "Importar Dados"
            
            st.markdown("---")
            
            if st.button("Gerenciar Usuários", use_container_width=True):
                st.session_state.current_page = "Gerenciar Usuários"
            
            st.markdown("---")
            
            if st.button("Minha Conta", use_container_width=True):
                st.session_state.current_page = "Minha Conta"
            
            st.markdown("---")
            
            if st.button("Sair", use_container_width=True, type="primary"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
        
        # TECNICO_RECARGA MENU
        elif role == "tecnico_recarga":
            if st.button("Minhas Recargas", use_container_width=True):
                st.session_state.current_page = "Minhas Recargas"
            
            st.markdown("---")
            
            if st.button("Minha Conta", use_container_width=True):
                st.session_state.current_page = "Minha Conta"
            
            st.markdown("---")
            
            if st.button("Sair", use_container_width=True, type="primary"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
        
        # ADMINISTRATIVO MENU
        elif role == "administrativo":
            if st.button("Dashboard", use_container_width=True):
                st.session_state.current_page = "Dashboard"
            
            st.markdown("---")
            
            if st.button("Registrar OS", use_container_width=True):
                st.session_state.current_page = "Registrar OS"
            
            if st.button("Filtrar OS", use_container_width=True):
                st.session_state.current_page = "Filtrar OS"
            
            if st.button("Dar Baixa", use_container_width=True):
                st.session_state.current_page = "Dar Baixa"
            
            st.markdown("---")
            
            if st.button("Minhas Recargas", use_container_width=True):
                st.session_state.current_page = "Minhas Recargas"
            
            st.markdown("---")
            
            if st.button("Minha Conta", use_container_width=True):
                st.session_state.current_page = "Minha Conta"
            
            st.markdown("---")
            
            if st.button("Sair", use_container_width=True, type="primary"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
        
        # OUTROS
        else:
            if st.button("Dashboard", use_container_width=True):
                st.session_state.current_page = "Dashboard"
            
            st.markdown("---")
            
            if st.button("Minha Conta", use_container_width=True):
                st.session_state.current_page = "Minha Conta"
            
            st.markdown("---")
            
            if st.button("Sair", use_container_width=True, type="primary"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
    
    # Verificação de acesso às páginas
    page = st.session_state.current_page
    role = st.session_state.get("role", "")
    
    # Regras de acesso por página
    access_rules = {
        "Dashboard": ["admin", "administrativo"],
        "Registrar OS": ["admin", "administrativo"],
        "Minhas Tarefas": ["tecnico"],
        "Minhas Recargas": ["tecnico_recarga", "admin", "administrativo"],
        "Filtrar OS": ["tecnico", "admin", "administrativo"],
        "Dar Baixa": ["tecnico", "admin", "administrativo"],
        "Equipamentos": ["admin", "administrativo"],
        "Laudos": ["tecnico", "admin"],
        "Importar Dados": ["admin"],
        "Gerenciar Usuários": ["admin"],
        "Minha Conta": ["admin", "tecnico", "administrativo", "tecnico_recarga"],
    }
    
    # Validar acesso
    if page in access_rules and role not in access_rules[page]:
        st.error(f"Acesso Negado: Você não tem permissão para acessar '{page}'.")
        st.info(f"Retornando para homepage...")
        
        if role == "tecnico":
            st.session_state.current_page = "Minhas Tarefas"
        elif role == "tecnico_recarga":
            st.session_state.current_page = "Minhas Recargas"
        else:
            st.session_state.current_page = "Dashboard"
        
        st.rerun()
    
    # Roteamento de páginas
    if page == "Dashboard":
        import dashboard
        dashboard.render()
    
    elif page == "Registrar OS":
        import registrar_os
        registrar_os.render()
    
    elif page == "Minhas Tarefas":
        import minhas_tarefas
        minhas_tarefas.render()
    
    elif page == "Minhas Recargas":
        import minhas_recargas
        minhas_recargas.render()
    
    elif page == "Filtrar OS":
        import filtro
        filtro.render()
    
    elif page == "Dar Baixa":
        import dar_baixa
        dar_baixa.render()
    
    elif page == "Equipamentos":
        import equipamentos
        equipamentos.render()
    
    elif page == "Laudos":
        import laudos
        laudos.render()
    
    elif page == "Registrar Laudo":
        import laudos
        laudos.render()
    
    elif page == "Importar Dados":
        import importar_dados
        importar_dados.render()
    
    elif page == "Gerenciar Usuários":
        import gerenciar_usuarios
        gerenciar_usuarios.render()
    
    elif page == "Minha Conta":
        import minha_conta
        minha_conta.render()

def main():
    initialize_database()
    
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        show_login_page()
    else:
        show_main_app()

if __name__ == "__main__":
    main()