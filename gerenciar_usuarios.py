# CÓDIGO ATUALIZADO E COMPLETO PARA: sistema_os_crud-main/gerenciar_usuarios.py

import streamlit as st
import pandas as pd
from sqlalchemy import text
from database import get_connection
from auth import hash_password, validate_password 
from config import TECNICOS # <-- Importa a lista de técnicos

ROLES = ["tecnico", "administrativo", "admin"]

# --- FUNÇÃO ATUALIZADA ---
def f_criar_usuario(conn, username, password, role, display_name):
    """Função para criar um novo usuário no banco."""
    try:
        with conn.connect() as con:
            with con.begin():
                query_check = text("SELECT id FROM usuarios WHERE username = :username")
                exists = con.execute(query_check, {"username": username}).fetchone()
                if exists:
                    st.error(f"Erro: O nome de usuário '{username}' já existe.")
                    return False
                
                hashed_pass = hash_password(password)
                
                query_insert = text("""
                    INSERT INTO usuarios (username, password_hash, role, display_name)
                    VALUES (:username, :password, :role, :display_name)
                """)
                con.execute(query_insert, {
                    "username": username,
                    "password": hashed_pass,
                    "role": role,
                    "display_name": display_name # Salva o nome de exibição
                })
                st.success(f"Usuário '{username}' (Nome: {display_name}) criado com sucesso!")
                return True
                
    except Exception as e:
        st.error(f"Erro ao criar usuário: {e}")
        return False
# --- FIM DA ATUALIZAÇÃO ---

def f_deletar_usuario(conn, username):
    """Função para deletar um usuário."""
    try:
        with conn.connect() as con:
            with con.begin():
                query = text("DELETE FROM usuarios WHERE username = :username")
                con.execute(query, {"username": username})
                st.success(f"Usuário '{username}' deletado com sucesso.")
                return True
    except Exception as e:
        st.error(f"Erro ao deletar usuário: {e}")
        return False

def render():
    st.markdown("<h3 style='text-align: left;'>Gerenciamento de Usuários</h3>", unsafe_allow_html=True)
    conn = get_connection()
    
    st.markdown("#### Criar Novo Usuário")
    with st.form("new_user_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            username = st.text_input("Nome de Usuário (login) *")
            role = st.selectbox("Função *", ROLES, index=0) 
        with col2:
            password = st.text_input("Senha *", type="password")
            confirm_password = st.text_input("Confirmar Senha *", type="password")
        
        # --- LÓGICA CONDICIONAL PARA NOME DE EXIBIÇÃO ---
        display_name = None
        if role == 'tecnico':
            display_name = st.selectbox(
                "Nome de Exibição (Técnico) *",
                sorted(TECNICOS),
                index=None,
                placeholder="Selecione o nome do técnico da lista"
            )
        elif role == 'admin':
            display_name = st.text_input("Nome de Exibição (Admin)", value=username)
        else: # administrativo
            display_name = st.text_input("Nome de Exibição (Administrativo)", value=username)
        # --- FIM DA LÓGICA ---

        submitted = st.form_submit_button("Criar Usuário", use_container_width=True, type="primary")
        
        if submitted:
            # --- ATUALIZAÇÃO DA VALIDAÇÃO ---
            if not all([username, password, confirm_password, role, display_name]):
                st.warning("Por favor, preencha todos os campos obrigatórios (*).")
            # --- FIM DA ATUALIZAÇÃO ---
            elif password != confirm_password:
                st.error("As senhas não coincidem.")
            else:
                is_valid, message = validate_password(password)
                if not is_valid:
                    st.error(f"Senha inválida: {message}")
                else:
                    if f_criar_usuario(conn, username, password, role, display_name):
                        st.rerun() 
                    
    st.markdown("---")
    
    st.markdown("#### Usuários Existentes")
    try:
        # Mostra a nova coluna na tabela
        df_users = pd.read_sql("SELECT id, username, role, display_name, data_registro FROM usuarios ORDER BY username", conn)
        df_users['data_registro'] = pd.to_datetime(df_users['data_registro']).dt.strftime('%d/%m/%Y %H:%M')
        st.dataframe(df_users, use_container_width=True)
        
        st.markdown("##### Deletar Usuário")
        current_user = st.session_state.get('username', '')
        user_list = [u for u in df_users['username'].tolist() if u != current_user]
        
        if not user_list:
            st.info("Não há outros usuários para deletar.")
        else:
            user_to_delete = st.selectbox(
                "Selecione um usuário para deletar",
                user_list,
                index=None,
                placeholder="Selecione um usuário..."
            )
            if st.button("Deletar Usuário Selecionado", type="secondary"):
                if user_to_delete:
                    if f_deletar_usuario(conn, user_to_delete):
                        st.rerun() 
                else:
                    st.warning("Por favor, selecione um usuário para deletar.")
    except Exception as e:
        st.error(f"Erro ao carregar lista de usuários: {e}")