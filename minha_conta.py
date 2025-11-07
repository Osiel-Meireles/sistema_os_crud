# CÓDIGO PARA O NOVO ARQUIVO: sistema_os_crud-main/minha_conta.py

import streamlit as st
from database import get_connection
from auth import validate_password, authenticate_user, update_user_password

def render():
    st.markdown("<h3 style='text-align: left;'>Minha Conta</h3>", unsafe_allow_html=True)
    
    conn = get_connection()
    username = st.session_state.get('username')
    
    if not username:
        st.error("Erro ao carregar dados do usuário. Por favor, faça login novamente.")
        st.session_state.logged_in = False
        st.rerun()
        return

    st.markdown(f"#### Alterar Senha para o Usuário: **{username}**")

    with st.form("change_password_form"):
        current_password = st.text_input("Senha Atual", type="password")
        new_password = st.text_input("Nova Senha", type="password")
        confirm_password = st.text_input("Confirmar Nova Senha", type="password")
        
        submitted = st.form_submit_button("Salvar Nova Senha", use_container_width=True, type="primary")

        if submitted:
            if not all([current_password, new_password, confirm_password]):
                st.warning("Por favor, preencha todos os campos.")
            
            # 1. Verificar se a senha atual está correta
            elif not authenticate_user(conn, username, current_password):
                st.error("A 'Senha Atual' está incorreta.")
            
            # 2. Verificar se as novas senhas coincidem
            elif new_password != confirm_password:
                st.error("A 'Nova Senha' e a 'Confirmação' não coincidem.")
            
            # 3. Verificar se a nova senha é forte
            else:
                is_valid, message = validate_password(new_password)
                if not is_valid:
                    st.error(f"Senha nova inválida: {message}")
                
                # 4. Se tudo estiver certo, atualizar a senha
                else:
                    if update_user_password(conn, username, new_password):
                        st.success("Sua senha foi alterada com sucesso!")
                    else:
                        st.error("Ocorreu um erro inesperado ao tentar alterar sua senha.")