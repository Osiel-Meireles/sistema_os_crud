# CÓDIGO COMPLETO PARA: sistema_os_crud-main/filtro.py
import streamlit as st
import pandas as pd
from database import get_connection
from sqlalchemy import text
from config import (
    SECRETARIAS, TECNICOS, STATUS_OPTIONS, EQUIPAMENTOS, CATEGORIAS
)
from import_export import exportar_filtrados_para_excel
import base64
import math
import pytz
from datetime import datetime

def f_deletar_os(conn, os_id, os_type):
    """Deleta uma OS específica do banco de dados."""
    table_name = "os_interna" if os_type == "Interna" else "os_externa"
    try:
        with conn.connect() as con:
            with con.begin():
                query = text(f"DELETE FROM {table_name} WHERE id = :id")
                con.execute(query, {"id": os_id})
        st.success(f"OS (ID: {os_id}) deletada com sucesso.")
        return True
    except Exception as e:
        st.error(f"Erro ao deletar OS: {e}")
        return False

def display_os_details(os_data):
    """Exibe os detalhes de uma OS."""
    st.markdown(f"#### Detalhes Completos da OS: {os_data.get('numero', 'N/A')}")
    
    col_map = {
        "numero": "Número",
        "tipo": "Tipo",
        "status": "Status",
        "secretaria": "Secretaria",
        "setor": "Setor",
        "solicitante": "Solicitante",
        "telefone": "Telefone",
        "data": "Data de Entrada",
        "hora": "Hora de Entrada",
        "tecnico": "Técnico",
        "equipamento": "Equipamento",
        "patrimonio": "Patrimônio",
        "categoria": "Categoria",
        "data_finalizada": "Data de Finalização",
        "data_retirada": "Data de Retirada",
        "registrado_por": "Registrado Por"
    }
    
    display_data = []
    for col, label in col_map.items():
        if col in os_data and pd.notna(os_data[col]):
            value = os_data[col]
            if col == 'data' and value:
                try:
                    value = pd.to_datetime(value).strftime('%d/%m/%Y')
                except (ValueError, TypeError):
                    pass
            if col == 'hora' and value:
                try:
                    value = pd.to_datetime(str(value)).strftime('%H:%M:%S')
                except (ValueError, TypeError):
                    pass
            if col in ['data_finalizada', 'data_retirada'] and value:
                try:
                    value = pd.to_datetime(value, utc=True).tz_convert('America/Sao_Paulo').strftime('%d/%m/%Y %H:%M:%S')
                except (ValueError, TypeError):
                    pass
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
    
    if os_data.get('laudo_pdf') is not None and len(os_data.get('laudo_pdf')) > 0:
        st.markdown("---")
        st.markdown("#### Laudo Técnico (Anexo PDF Antigo)")
        pdf_data = bytes(os_data['laudo_pdf']) if isinstance(os_data['laudo_pdf'], memoryview) else os_data['laudo_pdf']
        st.download_button(
            label=f"Baixar Laudo PDF ({os_data.get('laudo_filename')})",
            data=pdf_data,
            file_name=os_data.get('laudo_filename'),
            mime="application/pdf"
        )

def render_modal_detalhes_os(conn):
    if 'view_os_id' not in st.session_state or st.session_state.view_os_id is None:
        return
    
    try:
        os_data = st.session_state.df_filtrado.iloc[st.session_state.view_os_id]
    except IndexError:
        st.error("Erro ao carregar dados da OS. Tente filtrar novamente.")
        st.session_state.view_os_id = None
        return
    except Exception as e:
        st.error(f"Erro inesperado: {e}")
        st.session_state.view_os_id = None
        return
    
    @st.dialog("Detalhes Completos da Ordem de Serviço", width="large")
    def show_modal():
        display_os_details(os_data)
        
        st.markdown("---")
        st.markdown("#### Laudos de Avaliação Associados")
        
        tipo_os_laudo = f"OS {os_data.get('tipo')}"
        numero_os = os_data.get('numero')
        laudos_registrados = []
        
        try:
            query_laudos = text("SELECT * FROM laudos WHERE numero_os = :num AND tipo_os = :tipo ORDER BY id DESC")
            with conn.connect() as con:
                results = con.execute(query_laudos, {"num": numero_os, "tipo": tipo_os_laudo}).fetchall()
                laudos_registrados = [r._mapping for r in results]
        except Exception as e:
            st.error(f"Erro ao buscar laudos: {e}")
        
        if not laudos_registrados:
            st.info("Nenhum laudo de avaliação registrado para esta OS.")
        else:
            fuso_sp = pytz.timezone('America/Sao_Paulo')
            for laudo in laudos_registrados:
                data_reg = laudo['data_registro'].astimezone(fuso_sp).strftime('%d/%m/%Y %H:%M')
                exp_title = f"Laudo ID {laudo['id']} - {laudo.get('estado_conservacao')} ({laudo['status']}) - Reg. {data_reg}"
                
                with st.expander(exp_title):
                    st.markdown(f"**Técnico:** {laudo['tecnico']}")
                    st.markdown(f"**Estado de Conservação:** {laudo.get('estado_conservacao')}")
                    st.markdown(f"**Equipamento Completo:** {laudo.get('equipamento_completo')}")
                    st.markdown("**Diagnóstico:**")
                    st.text_area(f"diag_{laudo['id']}", laudo.get('diagnostico', ''), height=100, disabled=True, label_visibility="collapsed")
                    
                    if laudo.get('observacoes'):
                        st.markdown("**Observações:**")
                        st.text_area(f"obs_{laudo['id']}", laudo['observacoes'], height=80, disabled=True, label_visibility="collapsed")
        
        st.markdown("---")
        if st.button("Fechar Detalhes", use_container_width=True, key="close_modal_filter"):
            st.session_state.view_os_id = None
            st.rerun()
    
    show_modal()

def render_modal_delete_os(conn):
    if 'delete_os_data' not in st.session_state or st.session_state.delete_os_data is None:
        return
    
    data = st.session_state.delete_os_data
    
    @st.dialog("Confirmar Exclusão", width="large")
    def show_modal():
        st.warning(f"**Você tem certeza que deseja deletar a OS {data.get('numero')}?**")
        st.markdown("Esta ação não pode ser desfeita.")
        st.markdown(f"**Tipo:** {data.get('tipo')}")
        st.markdown(f"**Secretaria:** {data.get('secretaria')}")
        st.markdown(f"**Solicitante:** {data.get('solicitante')}")
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        if col1.button("Confirmar Exclusão", type="primary", use_container_width=True):
            if f_deletar_os(conn, data.get('id'), data.get('tipo')):
                del st.session_state.delete_os_data
                st.session_state.df_filtrado = pd.DataFrame()
                st.rerun()
        
        if col2.button("Cancelar", use_container_width=True):
            del st.session_state.delete_os_data
            st.rerun()
    
    show_modal()

def render():
    st.markdown("## Filtro de Ordens de Serviço")
    conn = get_connection()
    role = st.session_state.get("role", "")
    
    # Verificar permissão para deletar
    pode_deletar = role in ["admin", "administrativo"]
    
    render_modal_detalhes_os(conn)
    
    # Só mostrar modal de deleção se usuário tem permissão
    if pode_deletar:
        render_modal_delete_os(conn)
    
    with st.expander("Filtros de Pesquisa", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            f_tipo = st.selectbox("Tipo de OS", ["Todos", "Interna", "Externa"])
            f_status = st.multiselect("Status", STATUS_OPTIONS)
            f_secretaria = st.multiselect("Secretaria", SECRETARIAS)
        
        with col2:
            f_tecnico = st.multiselect("Técnico", TECNICOS)
            f_categoria = st.multiselect("Categoria", CATEGORIAS)
            f_equipamento = st.multiselect("Equipamento", EQUIPAMENTOS)
        
        col_data1, col_data2 = st.columns(2)
        with col_data1:
            f_data_inicio = st.date_input("Data Inicial")
        with col_data2:
            f_data_fim = st.date_input("Data Final")
        
        filtrar = st.button("Aplicar Filtros", use_container_width=True, type="primary")
    
    if filtrar or 'df_filtrado' in st.session_state:
        if filtrar:
            where_clauses = []
            params = {}
            
            if f_tipo != "Todos":
                tipo_col = "tipo"
                where_clauses.append(f"{tipo_col} = :tipo")
                params["tipo"] = f_tipo
            
            if f_status:
                placeholders = ','.join([f":st{i}" for i in range(len(f_status))])
                where_clauses.append(f"status IN ({placeholders})")
                for i, st_val in enumerate(f_status):
                    params[f"st{i}"] = st_val
            
            if f_secretaria:
                placeholders = ','.join([f":sec{i}" for i in range(len(f_secretaria))])
                where_clauses.append(f"secretaria IN ({placeholders})")
                for i, sec in enumerate(f_secretaria):
                    params[f"sec{i}"] = sec
            
            if f_tecnico:
                placeholders = ','.join([f":tec{i}" for i in range(len(f_tecnico))])
                where_clauses.append(f"tecnico IN ({placeholders})")
                for i, tec in enumerate(f_tecnico):
                    params[f"tec{i}"] = tec
            
            if f_categoria:
                placeholders = ','.join([f":cat{i}" for i in range(len(f_categoria))])
                where_clauses.append(f"categoria IN ({placeholders})")
                for i, cat in enumerate(f_categoria):
                    params[f"cat{i}"] = cat
            
            if f_equipamento:
                placeholders = ','.join([f":eq{i}" for i in range(len(f_equipamento))])
                where_clauses.append(f"equipamento IN ({placeholders})")
                for i, eq in enumerate(f_equipamento):
                    params[f"eq{i}"] = eq
            
            if f_data_inicio:
                where_clauses.append("data >= :data_inicio")
                params["data_inicio"] = f_data_inicio
            
            if f_data_fim:
                where_clauses.append("data <= :data_fim")
                params["data_fim"] = f_data_fim
            
            query_interna = "SELECT *, 'Interna' as tipo FROM os_interna"
            query_externa = "SELECT *, 'Externa' as tipo FROM os_externa"
            
            if where_clauses:
                where_str = " WHERE " + " AND ".join(where_clauses)
                query_interna += where_str
                query_externa += where_str
            
            if f_tipo == "Interna":
                query_final = query_interna
            elif f_tipo == "Externa":
                query_final = query_externa
            else:
                query_final = f"({query_interna}) UNION ALL ({query_externa})"
            
            query_final += " ORDER BY data DESC, hora DESC"
            
            try:
                with conn.connect() as con:
                    result = con.execute(text(query_final), params)
                    rows = result.fetchall()
                    columns = result.keys()
                    df = pd.DataFrame(rows, columns=columns)
                
                st.session_state.df_filtrado = df
                st.session_state.filtro_page = 1  # CORRIGIDO: usa filtro_page ao invés de current_page
            except Exception as e:
                st.error(f"Erro ao executar filtro: {e}")
                st.exception(e)
                return
        
        df = st.session_state.df_filtrado
        
        if df.empty:
            st.info("Nenhuma OS encontrada com os filtros aplicados.")
            return
        
        st.success(f"**{len(df)} OS(s) encontrada(s)**")
        
        if len(df) > 0:
            excel_data = exportar_filtrados_para_excel(df)
            if excel_data:
                b64 = base64.b64encode(excel_data).decode()
                href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="os_filtradas.xlsx">Baixar Excel</a>'
                st.markdown(href, unsafe_allow_html=True)
        
        # PAGINAÇÃO CORRIGIDA
        if 'filtro_page' not in st.session_state:
            st.session_state.filtro_page = 1
        
        ITEMS_PER_PAGE = 10
        total_items = len(df)
        total_pages = math.ceil(total_items / ITEMS_PER_PAGE)
        
        if st.session_state.filtro_page > total_pages:
            st.session_state.filtro_page = total_pages
        if st.session_state.filtro_page < 1:
            st.session_state.filtro_page = 1
        
        start_idx = (st.session_state.filtro_page - 1) * ITEMS_PER_PAGE
        end_idx = start_idx + ITEMS_PER_PAGE
        df_page = df.iloc[start_idx:end_idx]
        
        st.markdown("---")
        st.info(f"Exibindo **{len(df_page)}** de **{total_items}** OS (Página {st.session_state.filtro_page}/{total_pages})")
        
        cols_header = st.columns((1, 1, 1.5, 1.5, 1, 1.5, 1.5))
        headers = ["Número", "Tipo", "Secretaria", "Solicitante", "Status", "Data", "Ações"]
        
        for col, header in zip(cols_header, headers):
            col.markdown(f"**{header}**")
        
        st.markdown("<hr style='margin-top: 0; margin-bottom: 0;'>", unsafe_allow_html=True)
        
        for idx, row in df_page.iterrows():
            cols_row = st.columns((1, 1, 1.5, 1.5, 1, 1.5, 1.5))
            
            cols_row[0].write(str(row.get('numero', 'N/A')))
            cols_row[1].write(str(row.get('tipo', 'N/A')))
            cols_row[2].write(str(row.get('secretaria', 'N/A')))
            cols_row[3].write(str(row.get('solicitante', 'N/A')))
            cols_row[4].write(str(row.get('status', 'N/A')))
            
            data_valor = row.get('data')
            if pd.notna(data_valor):
                try:
                    data_formatada = pd.to_datetime(data_valor).strftime('%d/%m/%Y')
                    cols_row[5].write(data_formatada)
                except:
                    cols_row[5].write(str(data_valor))
            else:
                cols_row[5].write('N/A')
            
            action_col = cols_row[6]
            col_b1, col_b2 = action_col.columns(2)
            
            if col_b1.button("👁️", key=f"view_{idx}", use_container_width=True, help="Visualizar"):
                st.session_state.view_os_id = idx
                st.rerun()
            
            # Só mostrar botão deletar se tem permissão
            if pode_deletar:
                if col_b2.button("🗑️", key=f"del_{idx}", use_container_width=True, type="secondary", help="Deletar"):
                    st.session_state.delete_os_data = dict(row)
                    st.rerun()
            
            st.markdown("<hr style='margin-top: 0; margin-bottom: 0;'>", unsafe_allow_html=True)
        
        st.markdown("---")
        if total_pages > 1:
            col_nav1, col_nav2, col_nav3 = st.columns([1, 1, 1])
            
            if col_nav1.button("← Anterior", key="prev_page", disabled=(st.session_state.filtro_page <= 1)):
                st.session_state.filtro_page -= 1
                st.rerun()
            
            col_nav2.markdown(f"**Página {st.session_state.filtro_page} de {total_pages}**")
            
            if col_nav3.button("Próxima →", key="next_page", disabled=(st.session_state.filtro_page >= total_pages)):
                st.session_state.filtro_page += 1
                st.rerun()