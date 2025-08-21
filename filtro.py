import streamlit as st
import pandas as pd
from database import get_connection
from sqlalchemy import text
from import_export import exportar_filtrados_para_excel

def render():
    st.markdown("<h3 style='text-align: left;'>Filtrar Ordens de Serviço</h3>", unsafe_allow_html=True)

    secretarias = ["Todas", "SAÚDE", "EDUCAÇÃO", "INFRAESTRUTURA", "ADMINISTRAÇÃO", "CIDADANIA", "GOVERNO", "SEGURANÇA", "FAZENDA", "ESPORTES"]
    tecnicos = ["Todos", "ANTONY CAUÃ", "MAYKON RODOLFO", "DIEGO CARDOSO", "ROMÉRIO CIRQUEIRA", "DIEL BATISTA", "JOSAFÁ MEDEIROS", "VALMIR FRANCISCO"]
    status_options = ["Todos", "EM ABERTO", "FINALIZADO"]

    tipo_os = st.selectbox("Tipo de OS", ["Ambas", "OS Interna", "OS Externa"])
    secretaria = st.selectbox("Secretaria", secretarias)

    # Inicializa o dataframe de resultados no estado da sessão
    if 'df_filtrado' not in st.session_state:
        st.session_state.df_filtrado = pd.DataFrame()

    col1, col2 = st.columns(2)

    with col1:
        with st.form("filtro_por_data"):
            st.markdown("#### Filtrar por Período e Outros Campos")
            data_inicio = st.date_input("Data de Início")
            data_fim = st.date_input("Data de Fim")
            status = st.selectbox("Status", status_options)
            tecnico = st.selectbox("Técnico", tecnicos)
            submitted_data = st.form_submit_button("Filtrar")

    with col2:
        with st.form("filtro_por_numero"):
            st.markdown("#### Filtrar por Número")
            numero_os = st.text_input("Número da OS")
            submitted_numero = st.form_submit_button("Filtrar")

    if submitted_data or submitted_numero:
        conn = get_connection()
        
        try:
            with conn.connect() as con:
                params = {
                    "secretaria": secretaria,
                }
                
                where_clauses = []

                if submitted_numero and numero_os:
                    where_clauses.append("numero = :numero_os")
                    params["numero_os"] = numero_os
                
                if submitted_data:
                    # Adiciona os filtros de data, status e técnico
                    if data_inicio and data_fim:
                        where_clauses.append("data BETWEEN :data_inicio AND :data_fim")
                        params["data_inicio"] = str(data_inicio)
                        params["data_fim"] = str(data_fim)
                    if status != "Todos":
                        where_clauses.append("status = :status")
                        params["status"] = status
                    if tecnico != "Todos":
                        where_clauses.append("tecnico = :tecnico")
                        params["tecnico"] = tecnico
                
                if secretaria != "Todas":
                    where_clauses.append("secretaria = :secretaria")
                
                where_string = " AND ".join(where_clauses)
                if where_string:
                    where_string = " WHERE " + where_string
                
                base_query_interna = """
                    SELECT numero, secretaria, setor, data, hora, solicitante, telefone, equipamento, descricao, status, data_finalizada, data_retirada, retirada_por, tecnico, solicitacao_cliente, categoria, patrimonio, servico_executado, 'Interna' as tipo
                    FROM os_interna
                """
                
                base_query_externa = """
                    SELECT numero, secretaria, setor, data, hora, solicitante, telefone, equipamento, descricao, status, data_finalizada, data_retirada, retirada_por, tecnico, solicitacao_cliente, categoria, patrimonio, servico_executado, 'Externa' as tipo
                    FROM os_externa
                """

                df_final = pd.DataFrame()
                
                if tipo_os == "OS Interna" or tipo_os == "Ambas":
                    query_interna = base_query_interna + where_string
                    df_interna = pd.read_sql(text(query_interna), con, params=params)
                    df_final = pd.concat([df_final, df_interna])
                
                if tipo_os == "OS Externa" or tipo_os == "Ambas":
                    query_externa = base_query_externa + where_string
                    df_externa = pd.read_sql(text(query_externa), con, params=params)
                    df_final = pd.concat([df_final, df_externa])
                
                st.session_state.df_filtrado = df_final.reset_index(drop=True)
                
        except Exception as e:
            st.error(f"Ocorreu um erro ao executar a consulta: {e}")
            st.session_state.df_filtrado = pd.DataFrame()


    if st.session_state.df_filtrado.empty:
        st.info("Não há dados com esses filtros.")
    else:
        st.dataframe(st.session_state.df_filtrado)
        excel_file = exportar_filtrados_para_excel(st.session_state.df_filtrado)
        st.download_button(
            label="Exportar para Excel",
            data=excel_file,
            file_name="dados_filtrados.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type='primary'
        )