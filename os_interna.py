import streamlit as st
import pandas as pd
from sqlalchemy import text
from datetime import date, datetime
import math

from database import get_connection, gerar_proximo_numero_os
from config import SECRETARIAS, TECNICOS, CATEGORIAS_INTERNA, EQUIPAMENTOS

def render():
    st.markdown("##### Ordens de Serviço Internas")
    st.text("Registre a ordem de serviço")

    conn = get_connection()
    
    secretarias_sorted = [SECRETARIAS[0]] + sorted(SECRETARIAS[1:])
    tecnicos_sorted = [TECNICOS[0]] + sorted(TECNICOS[1:])
    categorias_sorted = [CATEGORIAS_INTERNA[0]] + sorted(CATEGORIAS_INTERNA[1:])
    equipamentos_sorted = [EQUIPAMENTOS[0]] + sorted(EQUIPAMENTOS[1:])

    with st.form("nova_os_interna", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            secretaria = st.selectbox("Secretaria", secretarias_sorted)
            solicitante = st.text_input("Solicitante")
            solicitacao_cliente = st.text_area("Solicitação do Cliente")
            patrimonio = st.text_input("Número do Patrimônio")
            tecnico = st.selectbox("Técnico", tecnicos_sorted)
            data = st.date_input("Data de Entrada", value=date.today(), format="DD/MM/YYYY")

        with col2:
            setor = st.text_input("Setor")
            telefone = st.text_input("Telefone")
            categoria = st.selectbox("Categoria do Serviço", categorias_sorted)
            equipamento = st.selectbox("Equipamento", equipamentos_sorted)
            hora = st.time_input("Hora de Entrada", value=datetime.now().time())
        
        submitted = st.form_submit_button("Registrar ordem de serviço", use_container_width=True, type='primary')
        
        if submitted:
            # Validações
            if not all([setor, solicitante, telefone, solicitacao_cliente]):
                st.error("Por favor, preencha todos os campos de texto (Setor, Solicitante, Telefone, Solicitação).")
                return
            if "Selecione..." in [secretaria, tecnico, categoria, equipamento]:
                st.error("Por favor, selecione uma secretaria, técnico, categoria e equipamento válidos.")
                return

            try:
                with conn.connect() as con:
                    with con.begin(): 
                        con.execute(text("LOCK TABLE os_interna IN ACCESS EXCLUSIVE MODE"))
                        
                        numero_os = gerar_proximo_numero_os(con, "os_interna")
                        
                        con.execute(
                            text("""
                                INSERT INTO os_interna (numero, secretaria, setor, data, hora, solicitante, telefone, solicitacao_cliente, categoria, patrimonio, equipamento, status, tecnico)
                                VALUES (:numero, :secretaria, :setor, :data, :hora, :solicitante, :telefone, :solicitacao_cliente, :categoria, :patrimonio, :equipamento, 'EM ABERTO', :tecnico)
                            """),
                            {
                                "numero": numero_os, "secretaria": secretaria, "setor": setor, "data": data, "hora": hora,
                                "solicitante": solicitante, "telefone": telefone, "solicitacao_cliente": solicitacao_cliente,
                                "categoria": categoria, "patrimonio": patrimonio, "equipamento": equipamento,
                                "tecnico": tecnico
                            }
                        )
                st.toast(f"✅ OS Interna nº {numero_os} adicionada com sucesso!")

            except Exception as e:
                st.error(f"Ocorreu um erro ao registrar a OS: {e}")

    st.markdown("---")
    st.markdown("##### Ordens de serviço internas cadastradas: ")

    # Inicializa o estado da página se não existir
    if 'os_interna_page' not in st.session_state:
        st.session_state.os_interna_page = 1

    ITEMS_PER_PAGE = 15

    # 1. Consulta para contar o total de registros
    try:
        total_items_query = text("SELECT COUNT(id) FROM os_interna")
        with conn.connect() as con:
            total_items = con.execute(total_items_query).scalar()
    except Exception as e:
        st.error(f"Não foi possível contar os registros: {e}")
        total_items = 0

    total_pages = math.ceil(total_items / ITEMS_PER_PAGE) if total_items > 0 else 1

    # Garante que a página atual seja válida
    if st.session_state.os_interna_page > total_pages:
        st.session_state.os_interna_page = total_pages
    if st.session_state.os_interna_page < 1:
        st.session_state.os_interna_page = 1
    
    # 2. Consulta para buscar apenas os dados da página atual
    offset = (st.session_state.os_interna_page - 1) * ITEMS_PER_PAGE
    query = text(f"SELECT * FROM os_interna ORDER BY id DESC LIMIT :limit OFFSET :offset")
    
    df = pd.read_sql(query, conn, params={"limit": ITEMS_PER_PAGE, "offset": offset})

    date_cols = ['data', 'data_finalizada', 'data_retirada']
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%d/%m/%Y')
    
    st.dataframe(df)

    # 3. Controles de navegação da página
    st.markdown(" ")
    if total_pages > 1:
        col_nav1, col_nav2, col_nav3 = st.columns([1, 1, 1])
        if col_nav1.button("Anterior", key="prev_interna", disabled=(st.session_state.os_interna_page <= 1)):
            st.session_state.os_interna_page -= 1
            st.rerun()
        col_nav2.write(f"**Página {st.session_state.os_interna_page} de {total_pages}**")
        if col_nav3.button("Próxima", key="next_interna", disabled=(st.session_state.os_interna_page >= total_pages)):
            st.session_state.os_interna_page += 1
            st.rerun()
