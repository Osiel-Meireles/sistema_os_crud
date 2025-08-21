import streamlit as st
from database import init_db
import os_interna, os_externa, filtro, dar_baixa
import import_export

st.set_page_config(layout="wide")
st.image("Secretaria_da_Fazenda-removebg-preview.png",
         width=600)
st.markdown("<h2 style='text-align: left;'>Sistema de Registro de Ordens de Serviço</h2>", unsafe_allow_html=True)



if 'page' not in st.session_state:
    st.session_state.page = "Home"


st.markdown(
    """
    <style>
    .stButton > button {
        text-align: left !important;
    }
    </style>
    """, unsafe_allow_html=True
)


st.sidebar.markdown("<h3 style='text-align: left;'>Navegação</h3>", unsafe_allow_html=True)

if st.sidebar.button("Tela Inicial", use_container_width=True):
    st.session_state.page = "Home"

if st.sidebar.button("OS Interna", use_container_width=True):
    st.session_state.page = "OS Interna"

if st.sidebar.button("OS Externa", use_container_width=True):
    st.session_state.page = "OS Externa"

if st.sidebar.button("Filtrar OS", use_container_width=True):
    st.session_state.page = "Filtrar OS"

if st.sidebar.button("Dar Baixa em OS", use_container_width=True):
    st.session_state.page = "Dar Baixa em OS"


if st.session_state.page == "Home":
    st.markdown("<h3 style='text-align: left;'>Bem-vindo(a)!</h3>", unsafe_allow_html=True)
    st.write("Selecione uma das opções abaixo para começar.")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Ordens de Serviço Internas", use_container_width=True):
            st.session_state.page = "OS Interna"
        if st.button("Filtrar Ordens de Serviço", use_container_width=True):
            st.session_state.page = "Filtrar OS"

    with col2:
        if st.button("Ordens de Serviço Externas", use_container_width=True):
            st.session_state.page = "OS Externa"
        if st.button("Dar Baixa em OS", use_container_width=True):
            st.session_state.page = "Dar Baixa em OS"

elif st.session_state.page == "OS Interna":
    os_interna.render()
elif st.session_state.page == "OS Externa":
    os_externa.render()
elif st.session_state.page == "Filtrar OS":
    filtro.render()
elif st.session_state.page == "Dar Baixa em OS":
    dar_baixa.render()