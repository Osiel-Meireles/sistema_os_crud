import streamlit as st
import pandas as pd
from database import get_connection
from sqlalchemy import text
from config import (
    SECRETARIAS, TECNICOS, STATUS_OPTIONS, EQUIPAMENTOS,
    CATEGORIAS_INTERNA, CATEGORIAS_EXTERNA
)
from import_export import exportar_filtrados_para_excel
import base64
import math

def display_os_details(os_data):
    """
    Exibe os detalhes de uma OS, mostrando informações de entrega apenas se o status for apropriado.
    """
    st.markdown(f"#### Detalhes Completos da OS: {os_data.get('numero', 'N/A')}")

    col_map = {
        "numero": "Número", "tipo": "Tipo", "status": "Status", "secretaria": "Secretaria",
        "setor": "Setor", "solicitante": "Solicitante", "telefone": "Telefone",
        "data": "Data de Entrada", "hora": "Hora de Entrada", "tecnico": "Técnico",
        "equipamento": "Equipamento", "patrimonio": "Patrimônio", "categoria": "Categoria",
        "data_finalizada": "Data de Finalização",
        "data_retirada": "Data de Retirada"
    }
    
    display_data = []
    for col, label in col_map.items():
        if col in os_data and pd.notna(os_data[col]):
            value = os_data[col]
            # Formatação para datas
            if col in ['data', 'data_finalizada'] and value:
                try: value = pd.to_datetime(value).strftime('%d/%m/%Y')
                except (ValueError, TypeError): pass
            
            # --- LÓGICA DE FUSO HORÁRIO ATUALIZADA ---
            if col == 'data_retirada' and value:
                try:
                    # Lê a data como UTC e converte para o fuso de São Paulo
                    value = pd.to_datetime(value, utc=True).tz_convert('America/Sao_Paulo').strftime('%d/%m/%Y %H:%M:%S')
                except (ValueError, TypeError): pass
            
            display_data.append([f"**{label}**", value])

    st.table(pd.DataFrame(display_data, columns=["Campo", "Valor"]))

    st.markdown("**Solicitação do Cliente:**")
    st.text_area("solicitacao_exp", value=os_data.get('solicitacao_cliente', '') or "", disabled=True, label_visibility="collapsed", height=100)

    st.markdown("**Serviço Executado / Descrição:**")
    texto_completo = f"{os_data.get('servico_executado', '') or ''}\n{os_data.get('descricao', '') or ''}".strip()
    st.text_area("servico_exp", value=texto_completo, disabled=True, label_visibility="collapsed", height=100)
    
    if os_data.get('status') == 'ENTREGUE AO CLIENTE':
        st.markdown("---")
        st.markdown("#### Informações da Entrega")
        retirada_por = os_data.get('retirada_por')
        if pd.notna(retirada_por):
            st.write(f"**Nome do recebedor:** {retirada_por}")

# O resto do arquivo (função render) permanece o mesmo.
# ...
def render():
    st.markdown("<h3 style='text-align: left;'>Filtrar Ordens de Serviço</h3>", unsafe_allow_html=True)
    categorias_combinadas = sorted(list(set(CATEGORIAS_INTERNA[1:] + CATEGORIAS_EXTERNA[1:])))
    secretarias_filtro = ["Todas"] + sorted(SECRETARIAS[1:])
    tecnicos_filtro = ["Todos"] + sorted(TECNICOS[1:])
    equipamentos_filtro = ["Todos"] + sorted(EQUIPAMENTOS[1:])
    categorias_filtro = ["Todas"] + categorias_combinadas

    if 'df_filtrado' not in st.session_state:
        st.session_state.df_filtrado = pd.DataFrame()
    
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 1
    if 'selected_os_index' not in st.session_state:
        st.session_state.selected_os_index = None

    with st.form("filtro_os"):
        st.markdown("#### Preencha os campos para buscar")
        col1, col2, col3 = st.columns(3)
        with col1:
            tipo_os = st.selectbox("Tipo de OS", ["Ambas", "OS Interna", "OS Externa"])
            data_inicio = st.date_input("Data de Início", value=None)
        with col2:
            status = st.selectbox("Status", STATUS_OPTIONS)
            data_fim = st.date_input("Data de Fim", value=None)
        with col3:
            secretaria = st.selectbox("Secretaria", secretarias_filtro)
            numero_os = st.text_input("Número da OS (opcional)")
        with st.expander("Mais Filtros..."):
            exp_col1, exp_col2, exp_col3 = st.columns(3)
            with exp_col1: tecnico = st.selectbox("Técnico", tecnicos_filtro)
            with exp_col2: categoria = st.selectbox("Categoria do Serviço", categorias_filtro)
            with exp_col3: equipamento = st.selectbox("Equipamento", equipamentos_filtro)
            patrimonio = st.text_input("Número do Patrimônio (opcional)")
        submitted = st.form_submit_button("Filtrar", type="primary")

    if submitted:
        conn = get_connection()
        try:
            with conn.connect() as con:
                params = {}
                where_clauses = []
                if numero_os:
                    where_clauses.append("numero ILIKE :numero_os")
                    params["numero_os"] = f"%{numero_os}%"
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
                if where_clauses: where_string = " WHERE " + " AND ".join(where_clauses)
                base_query = " SELECT *, '{}' as tipo FROM {} "
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
                st.session_state.current_page = 1
                st.session_state.selected_os_index = None
        except Exception as e:
            st.error(f"Ocorreu um erro ao executar a consulta: {e}")
            st.session_state.df_filtrado = pd.DataFrame()

    if not st.session_state.df_filtrado.empty:
        st.markdown("---")
        st.markdown("#### Resultados da Busca")
        df_display = st.session_state.df_filtrado.copy()
        ITEMS_PER_PAGE = 20
        total_items = len(df_display)
        total_pages = math.ceil(total_items / ITEMS_PER_PAGE)
        
        if st.session_state.current_page > total_pages:
            st.session_state.current_page = total_pages
        if st.session_state.current_page < 1:
            st.session_state.current_page = 1
        
        start_idx = (st.session_state.current_page - 1) * ITEMS_PER_PAGE
        end_idx = start_idx + ITEMS_PER_PAGE
        df_paginated = df_display.iloc[start_idx:end_idx].copy()

        # Formatação das colunas de data
        if 'data' in df_paginated.columns:
            df_paginated['data'] = pd.to_datetime(df_paginated['data'], errors='coerce').dt.strftime('%d/%m/%Y')
        if 'data_finalizada' in df_paginated.columns:
            df_paginated['data_finalizada'] = pd.to_datetime(df_paginated['data_finalizada'], errors='coerce').dt.strftime('%d/%m/%Y')
        
        # --- LÓGICA DE FUSO HORÁRIO ATUALIZADA ---
        if 'data_retirada' in df_paginated.columns:
            # Lê a data como UTC e converte para o fuso de São Paulo
            df_paginated['data_retirada'] = pd.to_datetime(df_paginated['data_retirada'], utc=True, errors='coerce').dt.tz_convert('America/Sao_Paulo').dt.strftime('%d/%m/%Y %H:%M:%S')

        cols_header = st.columns((0.7, 1.5, 1.5, 2, 2.5, 2.5, 1.5, 1.5))
        headers = ["Ação", "Número", "Tipo", "Status", "Secretaria", "Solicitante", "Data", "Finalizada"]
        for col, header in zip(cols_header, headers):
            col.markdown(f"**{header}**")
        st.markdown("<hr style='margin-top: 0; margin-bottom: 0;'>", unsafe_allow_html=True)

        for index, row in df_paginated.iterrows():
            cols_row = st.columns((0.7, 1.5, 1.5, 2, 2.5, 2.5, 1.5, 1.5))
            if cols_row[0].button("👁️", key=f"detail_{index}", help="Ver detalhes da OS"):
                st.session_state.selected_os_index = index if st.session_state.selected_os_index != index else None
                st.rerun()
            cols_row[1].write(row.get("numero", "N/A"))
            cols_row[2].write(row.get("tipo", "N/A"))
            cols_row[3].write(row.get("status", "N/A"))
            cols_row[4].write(row.get("secretaria", "N/A"))
            cols_row[5].write(row.get("solicitante", "N/A"))
            cols_row[6].write(row.get("data", "N/A"))
            cols_row[7].write(row.get("data_finalizada", ""))
            
            if st.session_state.selected_os_index == index:
                with st.expander(" ", expanded=True):
                    display_os_details(st.session_state.df_filtrado.iloc[index])
                    if st.button("Fechar Detalhes", key=f"close_{index}", use_container_width=True):
                        st.session_state.selected_os_index = None
                        st.rerun()
            st.markdown("<hr style='margin-top: 0; margin-bottom: 0;'>", unsafe_allow_html=True)
        st.markdown(" ")
        
        if total_pages > 1:
            col_nav1, col_nav2, col_nav3 = st.columns([1, 1, 1])
            if col_nav1.button("Anterior", disabled=(st.session_state.current_page <= 1)):
                st.session_state.current_page -= 1
                st.session_state.selected_os_index = None
                st.rerun()
            col_nav2.write(f"**Página {st.session_state.current_page} de {total_pages}**")
            if col_nav3.button("Próxima", disabled=(st.session_state.current_page >= total_pages)):
                st.session_state.current_page += 1
                st.session_state.selected_os_index = None
                st.rerun()

        st.markdown("---")
        col_b1, col_b2, _ = st.columns([1, 1, 4])
        if col_b1.button("Limpar Resultados"):
            st.session_state.df_filtrado = pd.DataFrame()
            st.session_state.selected_os_index = None
            st.session_state.current_page = 1
            st.rerun()
        excel_bytes = exportar_filtrados_para_excel(st.session_state.df_filtrado)
        col_b2.download_button("Exportar para Excel", excel_bytes, "dados_filtrados.xlsx")
    elif submitted:
        st.info("Não foram encontrados dados com os filtros aplicados.")
