# CÓDIGO COMPLETO PARA: sistema_os_crud-main/gerenciar_usuarios.py
import streamlit as st
import pandas as pd
from sqlalchemy import text
from database import get_connection
from auth import hash_password, validate_password

def render():
    st.title("Gerenciamento de Usuários")
    
    conn = get_connection()
    
    if st.session_state.get("role") != "admin":
        st.error("Acesso negado. Apenas administradores podem gerenciar usuários.")
        return
    
    tab1, tab2 = st.tabs(["Criar Usuário", "Listar Usuários"])
    
    with tab1:
        render_create_user(conn)
    
    with tab2:
        render_list_users(conn)

def render_create_user(conn):
    st.markdown("### Criar Novo Usuário")
    
    with st.form("create_user_form"):
        st.markdown("#### Informações do Usuário")
        
        col1, col2 = st.columns(2)
        with col1:
            username = st.text_input("Nome de Usuário *", placeholder="Ex: joao.silva", help="Usado para login no sistema")
            display_name = st.text_input("Nome de Exibição *", placeholder="Ex: João Silva", help="Nome que aparecerá no sistema")
        
        with col2:
            role = st.selectbox(
                "Perfil de Acesso *",
                ["admin", "tecnico", "administrativo", "tecnico_recarga"],
                format_func=lambda x: {
                    "admin": "Administrador",
                    "tecnico": "Técnico",
                    "administrativo": "Administrativo",
                    "tecnico_recarga": "Técnico de Recarga"
                }[x]
            )
        
        password = st.text_input("Senha *", type="password", placeholder="Mínimo 8 caracteres", help="Deve conter maiúscula, minúscula, número e caractere especial")
        password_confirm = st.text_input("Confirmar Senha *", type="password", placeholder="Digite a senha novamente")
        
        st.markdown("---")
        st.markdown("#### Descrição dos Perfis:")
        st.markdown("""
        - **Administrador:** Acesso completo ao sistema, incluindo gerenciamento de usuários
        - **Técnico:** Acesso a OS, equipamentos, recargas e laudos
        - **Técnico de Recarga:** Acesso específico para gerenciar recargas de impressoras e visualizar equipamentos
        - **Administrativo:** Acesso a visualização e edição de OS
        """)
        
        submitted = st.form_submit_button("Criar Usuário", use_container_width=True, type="primary")
        
        if submitted:
            erros = []
            
            if not username or not display_name or not password:
                erros.append("Todos os campos obrigatórios devem ser preenchidos.")
            
            if password != password_confirm:
                erros.append("As senhas não coincidem.")
            
            if password:
                is_valid, msg = validate_password(password)
                if not is_valid:
                    erros.append(msg)
            
            if username:
                try:
                    with conn.connect() as con:
                        result = con.execute(text("SELECT id FROM usuarios WHERE username = :username"), {"username": username}).fetchone()
                        if result:
                            erros.append(f"O usuário '{username}' já existe.")
                except Exception as e:
                    erros.append(f"Erro ao verificar usuário: {e}")
            
            if erros:
                for erro in erros:
                    st.error(erro)
            else:
                try:
                    password_hash = hash_password(password)
                    with conn.connect() as con:
                        with con.begin():
                            query = text("""
                                INSERT INTO usuarios (username, password_hash, role, display_name)
                                VALUES (:username, :password_hash, :role, :display_name)
                            """)
                            con.execute(query, {
                                "username": username,
                                "password_hash": password_hash,
                                "role": role,
                                "display_name": display_name
                            })
                    
                    st.success(f"Usuário '{username}' criado com sucesso!")
                    st.info(f"**Perfil:** {role} | **Nome:** {display_name}")
                    st.rerun()
                
                except Exception as e:
                    st.error(f"Erro ao criar usuário: {e}")

def render_list_users(conn):
    st.markdown("### Usuários Cadastrados")
    
    try:
        with conn.connect() as con:
            result = con.execute(text("""
                SELECT id, username, role, display_name, data_registro
                FROM usuarios ORDER BY data_registro DESC
            """))
            rows = result.fetchall()
            columns = result.keys()
            df_users = pd.DataFrame(rows, columns=columns)
        
        if df_users.empty:
            st.info("Nenhum usuário cadastrado.")
            return
        
        st.write(f"**Total de usuários:** {len(df_users)}")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Admins", len(df_users[df_users['role'] == 'admin']))
        with col2:
            st.metric("Técnicos", len(df_users[df_users['role'] == 'tecnico']))
        with col3:
            st.metric("Téc. Recarga", len(df_users[df_users['role'] == 'tecnico_recarga']))
        with col4:
            st.metric("Administrativos", len(df_users[df_users['role'] == 'administrativo']))
        
        st.markdown("---")
        
        cols_header = st.columns((1.5, 2, 1.5, 2, 1.5))
        headers = ["Usuário", "Nome de Exibição", "Perfil", "Data de Registro", "Ações"]
        
        for col, header in zip(cols_header, headers):
            col.markdown(f"**{header}**")
        
        st.markdown("<hr style='margin-top: 0; margin-bottom: 0;'>", unsafe_allow_html=True)
        
        for idx, row in df_users.iterrows():
            user_id = row['id']
            cols_row = st.columns((1.5, 2, 1.5, 2, 1.5))
            
            cols_row[0].write(str(row['username']))
            cols_row[1].write(str(row.get('display_name', 'N/A')))
            
            role_display = {
                "admin": "Administrador",
                "tecnico": "Técnico",
                "administrativo": "Administrativo",
                "tecnico_recarga": "Téc. Recarga"
            }.get(row['role'], row['role'])
            cols_row[2].write(role_display)
            
            cols_row[3].write(str(row.get('data_registro', 'N/A'))[:19])
            
            current_user = st.session_state.get('username')
            if row['username'] == current_user:
                cols_row[4].write("(Você)")
            else:
                if cols_row[4].button("🗑️", key=f"del_user_{user_id}", help="Deletar usuário"):
                    st.session_state.delete_user_id = user_id
                    st.session_state.delete_user_data = dict(row)
                    st.rerun()
            
            st.markdown("<hr style='margin-top: 0; margin-bottom: 0;'>", unsafe_allow_html=True)
    
    except Exception as e:
        st.error(f"Erro ao listar usuários: {e}")
    
    if 'delete_user_id' in st.session_state:
        user_id = st.session_state.delete_user_id
        user_data = st.session_state.get('delete_user_data', {})
        
        st.warning("Confirmação de Exclusão")
        st.write(f"Tem certeza que deseja deletar o usuário **{user_data.get('username', 'N/A')}**?")
        
        col1, col2 = st.columns(2)
        if col1.button("Sim, Deletar", type="primary", use_container_width=True):
            try:
                with conn.connect() as con:
                    with con.begin():
                        con.execute(text("DELETE FROM usuarios WHERE id = :id"), {"id": user_id})
                st.success("Usuário deletado com sucesso.")
                del st.session_state.delete_user_id
                if 'delete_user_data' in st.session_state:
                    del st.session_state.delete_user_data
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao deletar usuário: {e}")
        
        if col2.button("Cancelar", use_container_width=True):
            del st.session_state.delete_user_id
            if 'delete_user_data' in st.session_state:
                del st.session_state.delete_user_data
            st.rerun()