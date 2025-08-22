import streamlit as st
import pandas as pd
from database import get_connection
from sqlalchemy import text
from config import (
    SECRETARIAS, TECNICOS, STATUS_OPTIONS, EQUIPAMENTOS,
    CATEGORIAS_INTERNA, CATEGORIAS_EXTERNA
)
from import_export import exportar_filtrados_para_excel

def render():
    st.markdown("<h3 style='text-align: left;'>Filtrar Ordens de Serviço</h3>", unsafe_allow_html=True)

    categorias_combinadas = sorted(list(set(CATEGORIAS_INTERNA[1:] + CATEGORIAS_EXTERNA[1:])))

    secretarias_filtro = ["Todas"] + sorted(SECRETARIAS[1:])
    tecnicos_filtro = ["Todos"] + sorted(TECNICOS[1:])
    equipamentos_filtro = ["Todos"] + sorted(EQUIPAMENTOS[1:])
    categorias_filtro = ["Todas"] + categorias_combinadas

    if 'df_filtrado' not in st.session_state:
        st.session_state.df_filtrado = pd.DataFrame()

    with st.form("filtro_os"):
        st.markdown("#### Preencha os campos para buscar")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            tipo_os = st.selectbox("Tipo de OS", ["Ambas", "OS Interna", "OS Externa"])
            secretaria = st.selectbox("Secretaria", secretarias_filtro)
            status = st.selectbox("Status", STATUS_OPTIONS)

        with col2:
            data_inicio = st.date_input("Data de Início")
            data_fim = st.date_input("Data de Fim")
            tecnico = st.selectbox("Técnico", tecnicos_filtro)

        with col3:
            categoria = st.selectbox("Categoria do Serviço", categorias_filtro)
            equipamento = st.selectbox("Equipamento", equipamentos_filtro)
            numero_os = st.text_input("Número da OS (opcional)")
            # --- CAMPO ADICIONADO ----
            patrimonio = st.text_input("Número do Patrimônio (opcional)")

        submitted = st.form_submit_button("Filtrar")

    if submitted:
        conn = get_connection()
        
        try:
            with conn.connect() as con:
                params = {}
                where_clauses = []

                if numero_os:
                    where_clauses.append("numero ILIKE :numero_os")
                    params["numero_os"] = f"%{numero_os}%"
                
                # --- LÓGICA ADICIONADA ---
                if patrimonio:
                    where_clauses.append("patrimonio ILIKE :patrimonio")
                    params["patrimonio"] = f"%{patrimonio}%"

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
                    params["secretaria"] = secretaria

                if categoria != "Todas":
                    where_clauses.append("categoria = :categoria")
                    params["categoria"] = categoria

                if equipamento != "Todos":
                    where_clauses.append("equipamento = :equipamento")
                    params["equipamento"] = equipamento
                
                where_string = ""
                if where_clauses:
                    where_string = " WHERE " + " AND ".join(where_clauses)
                
                base_query = """
                    SELECT numero, secretaria, setor, data, hora, solicitante, telefone, equipamento, descricao, status, data_finalizada, data_retirada, retirada_por, tecnico, solicitacao_cliente, categoria, patrimonio, servico_executado, '{}' as tipo
                    FROM {}
                """

                df_final = pd.DataFrame()
                
                if tipo_os == "OS Interna" or tipo_os == "Ambas":
                    query_interna = base_query.format("Interna", "os_interna") + where_string
                    df_interna = pd.read_sql(text(query_interna), con, params=params)
                    df_final = pd.concat([df_final, df_interna])
                
                if tipo_os == "OS Externa" or tipo_os == "Ambas":
                    query_externa = base_query.format("Externa", "os_externa") + where_string
                    df_externa = pd.read_sql(text(query_externa), con, params=params)
                    df_final = pd.concat([df_final, df_externa])
                
                st.session_state.df_filtrado = df_final.reset_index(drop=True)
                
        except Exception as e:
            st.error(f"Ocorreu um erro ao executar a consulta: {e}")
            st.session_state.df_filtrado = pd.DataFrame()

    if not st.session_state.df_filtrado.empty:
        st.markdown("---")
        st.markdown("#### Resultados da Busca")
        
        df_display = st.session_state.df_filtrado.copy()
        
        date_cols = ['data', 'data_finalizada', 'data_retirada']
        for col in date_cols:
            if col in df_display.columns:
                df_display[col] = pd.to_datetime(df_display[col], errors='coerce').dt.strftime('%d/%m/%Y')

        st.dataframe(df_display)

        # --- NOVO BLOCO DE CÓDIGO PARA EXPORTAÇÃO ---
        # Converte o DataFrame para bytes no formato Excel
        excel_bytes = exportar_filtrados_para_excel(st.session_state.df_filtrado)
        
        # Cria o botão de download
        st.download_button(
            label="Exportar para Excel",
            data=excel_bytes,
            file_name="dados_filtrados.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        # --- FIM DO NOVO BLOCO DE CÓDIGO ---

    elif submitted:
        st.info("Não foram encontrados dados com os filtros aplicados.")