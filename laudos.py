# CÓDIGO ATUALIZADO E COMPLETO PARA: sistema_os_crud-main/laudos.py

import streamlit as st
import pandas as pd
from sqlalchemy import text
from database import get_connection
from config import TECNICOS, COMPONENTES_LAUDO, STATUS_LAUDO
import re
from datetime import datetime
import pytz

TECNICOS_LAUDO = sorted(TECNICOS)

def f_buscar_os(conn, tipo_os, numero_os):
    if not numero_os:
        st.error("O campo 'Número da OS' é obrigatório.")
        return None
    table_name = "os_interna" if tipo_os == "OS Interna" else "os_externa"
    query = text(f"SELECT secretaria, equipamento, status, solicitante FROM {table_name} WHERE numero = :numero")
    try:
        with conn.connect() as con:
            result = con.execute(query, {"numero": numero_os}).fetchone()
        if result:
            st.session_state.os_encontrada = dict(result._mapping)
            st.session_state.os_encontrada['numero_os'] = numero_os
            st.session_state.os_encontrada['tipo_os'] = tipo_os
        else:
            st.warning(f"{tipo_os} com número {numero_os} não encontrada.")
            if 'os_encontrada' in st.session_state:
                del st.session_state.os_encontrada
        return st.session_state.get('os_encontrada')
    except Exception as e:
        st.error(f"Erro ao buscar OS: {e}")
        if 'os_encontrada' in st.session_state:
            del st.session_state.os_encontrada
        return None

def f_registrar_laudo(conn, data):
    try:
        with conn.connect() as con:
            with con.begin(): 
                query_laudo = text("""
                    INSERT INTO laudos (tipo_os, numero_os, componente, especificacao, link_compra, observacoes, tecnico, status)
                    VALUES (:tipo_os, :numero_os, :componente, :especificacao, :link_compra, :observacoes, :tecnico, 'PENDENTE')
                """)
                con.execute(query_laudo, data)
                table_name = "os_interna" if data['tipo_os'] == "OS Interna" else "os_externa"
                query_update_os = text(f"""
                    UPDATE {table_name}
                    SET status = 'AGUARDANDO PEÇA(S)'
                    WHERE numero = :numero_os
                """)
                con.execute(query_update_os, {"numero_os": data['numero_os']})
        st.success("Laudo registrado com sucesso!")
        st.info(f"O status da OS {data['numero_os']} foi atualizado para 'AGUARDANDO PEÇA(S)'.")
        if 'os_encontrada' in st.session_state:
            del st.session_state.os_encontrada
        return True
    except Exception as e:
        st.error(f"Erro ao registrar o laudo: {e}")
        return False

def f_atualizar_status_laudo(conn, laudo_id, novo_status):
    try:
        data_atendimento = datetime.now(pytz.utc)
        with conn.connect() as con:
            with con.begin():
                query = text("""
                    UPDATE laudos
                    SET status = :status, data_atendimento = :data
                    WHERE id = :id
                """)
                con.execute(query, {"status": novo_status, "data": data_atendimento, "id": laudo_id})
        st.toast("Status do laudo atualizado!")
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar status: {e}")
        return False

def render_modal_detalhes(conn):
    if 'view_laudo_id' not in st.session_state or st.session_state.view_laudo_id is None:
        return
    laudo_id = st.session_state.view_laudo_id
    try:
        query = text("SELECT * FROM laudos WHERE id = :id")
        with conn.connect() as con:
            laudo_data = con.execute(query, {"id": laudo_id}).fetchone()
        if not laudo_data:
            st.error("Não foi possível carregar os dados do laudo.")
            st.session_state.view_laudo_id = None
            return
        laudo = laudo_data._mapping
    except Exception as e:
        st.error(f"Erro ao buscar detalhes do laudo: {e}")
        st.session_state.view_laudo_id = None
        return

    @st.dialog("Detalhes do Laudo Técnico", dismissible=False)
    def show_modal():
        
        # --- ALTERAÇÃO AQUI: Mapa de status simplificado ---
        status_map = {
            "PENDENTE": ("#FFA500", "circle-half"), # Laranja
            "APROVADO": ("#008000", "check-circle-fill"), # Verde
            "NEGADO": ("#FF0000", "x-circle-fill"), # Vermelho
        }
        # --- FIM DA ALTERAÇÃO ---
        
        color, icon = status_map.get(laudo['status'], ("#808080", "question-circle")) 

        st.markdown(f"Status: <span style='color:{color}; font-weight:bold;'> <i class='bi bi-{icon}'></i> {laudo['status']}</span>", unsafe_allow_html=True)
        st.markdown(f"**ID do Laudo:** {laudo['id']}")
        st.markdown(f"**Número da OS:** {laudo['numero_os']} ({laudo['tipo_os']})")
        st.markdown(f"**Componente:** {laudo['componente']}")
        st.markdown("**Especificação Técnica:**")
        st.text_area("modal_espec", value=laudo['especificacao'], height=150, disabled=True, label_visibility="collapsed")
        if laudo['link_compra']:
            st.markdown(f"**Link de Compra:** [Acessar Link]({laudo['link_compra']})")
        st.markdown(f"**Técnico Responsável:** {laudo['tecnico']}")
        fuso_sp = pytz.timezone('America/Sao_Paulo')
        data_reg = laudo['data_registro'].astimezone(fuso_sp).strftime('%d/%m/%Y')
        hora_reg = laudo['data_registro'].astimezone(fuso_sp).strftime('%H:%M:%S')
        st.markdown(f"**Data de Registro:** {data_reg} | **Hora:** {hora_reg}")
        if laudo['data_atendimento']:
            data_at = laudo['data_atendimento'].astimezone(fuso_sp).strftime('%d/%m/%Y')
            hora_at = laudo['data_atendimento'].astimezone(fuso_sp).strftime('%H:%M:%S')
            st.markdown(f"**Última Atualização:** {data_at} | **Hora:** {hora_at}")
        if laudo['observacoes']:
            st.markdown("**Observações:**")
            st.text_area("modal_obs", value=laudo['observacoes'], height=100, disabled=True, label_visibility="collapsed")

        st.markdown("---")
        st.markdown("#### Atualizar Status do Laudo")
        try:
            current_status_index = STATUS_LAUDO.index(laudo['status'])
        except ValueError:
            current_status_index = 0 
        
        # O selectbox de atualização agora só mostrará "PENDENTE", "APROVADO", "NEGADO"
        novo_status = st.selectbox("Selecione o novo status", STATUS_LAUDO, index=current_status_index, key="modal_status_select")
        
        col_b1, col_b2 = st.columns([1, 1])
        if col_b1.button("Salvar Novo Status", use_container_width=True, type="primary"):
            if novo_status != laudo['status']:
                if f_atualizar_status_laudo(get_connection(), laudo_id, novo_status):
                    st.session_state.view_laudo_id = None 
                    st.rerun() 
            else:
                st.toast("O status selecionado é o mesmo status atual.")
        if col_b2.button("Fechar", use_container_width=True):
            st.session_state.view_laudo_id = None
            st.rerun()
    show_modal()

def render_consulta_laudos(conn):
    st.markdown("---")
    st.markdown("#### Consulta de Laudos Técnicos")
    with st.expander("Aplicar Filtros"):
        col1, col2 = st.columns(2)
        with col1:
            f_tipo_os = st.multiselect("Tipo de OS", ["OS Interna", "OS Externa"])
            # O filtro de status agora só mostrará os 3 status
            f_status = st.multiselect("Status do Laudo", STATUS_LAUDO)
            f_componente = st.multiselect("Componente", sorted(COMPONENTES_LAUDO))
        with col2:
            f_tecnico = st.multiselect("Técnico", TECNICOS_LAUDO)
            f_numero_os = st.text_input("Pesquisar por Número OS")
            f_especificacao = st.text_input("Pesquisar por Especificação")
    query_base = "SELECT id, numero_os, tipo_os, componente, status, tecnico FROM laudos"
    where_clauses = []
    params = {}
    if f_tipo_os:
        where_clauses.append("tipo_os IN :tipo_os")
        params["tipo_os"] = tuple(f_tipo_os)
    if f_status:
        where_clauses.append("status IN :status")
        params["status"] = tuple(f_status)
    if f_componente:
        where_clauses.append("componente IN :componente")
        params["componente"] = tuple(f_componente)
    if f_tecnico:
        where_clauses.append("tecnico IN :tecnico")
        params["tecnico"] = tuple(f_tecnico)
    if f_numero_os:
        where_clauses.append("numero_os ILIKE :numero_os")
        params["numero_os"] = f"%{f_numero_os}%"
    if f_especificacao:
        where_clauses.append("especificacao ILIKE :especificacao")
        params["especificacao"] = f"%{f_especificacao}%"
    if where_clauses:
        query_base += " WHERE " + " AND ".join(where_clauses)
    query_base += " ORDER BY id DESC"
    try:
        df_laudos = pd.read_sql(text(query_base), conn, params=params)
        if df_laudos.empty:
            st.info("Nenhum laudo encontrado com os filtros aplicados.")
            return
        st.markdown("##### Laudos Encontrados")
        cols_header = st.columns((0.5, 1, 1, 2, 1.5, 1.5, 1))
        headers = ["ID", "OS", "Tipo", "Componente", "Status", "Técnico", "Ação"]
        for col, header in zip(cols_header, headers):
            col.markdown(f"**{header}**")
        st.markdown("<hr style='margin-top: 0; margin-bottom: 0;'>", unsafe_allow_html=True)
        for index, row in df_laudos.iterrows():
            cols_row = st.columns((0.5, 1, 1, 2, 1.5, 1.5, 1))
            cols_row[0].write(row.get("id"))
            cols_row[1].write(row.get("numero_os"))
            cols_row[2].write(row.get("tipo_os"))
            cols_row[3].write(row.get("componente"))
            cols_row[4].write(row.get("status"))
            cols_row[5].write(row.get("tecnico"))
            if cols_row[6].button("Ver Detalhes", key=f"detail_{row.get('id')}", use_container_width=True):
                st.session_state.view_laudo_id = row.get("id")
                st.rerun() 
            st.markdown("<hr style='margin-top: 0; margin-bottom: 0;'>", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Erro ao consultar laudos: {e}")

def render():
    st.markdown("<h3 style='text-align: left;'>Registro de Laudo Técnico</h3>", unsafe_allow_html=True)
    
    display_name = st.session_state.get('display_name')
    if not display_name:
        st.error("Sessão inválida. Por favor, faça login novamente.")
        st.session_state.logged_in = False
        st.rerun()
        return

    conn = get_connection()

    numero_preenchido = st.session_state.get('laudo_os_preenchido', None)
    if numero_preenchido:
        st.session_state.numero_os_input = numero_preenchido['numero']
        st.session_state.tipo_os_index = 0 if numero_preenchido['tipo'] == 'Interna' else 1
        del st.session_state.laudo_os_preenchido
        f_buscar_os(conn, numero_preenchido['tipo_os_completo'], numero_preenchido['numero'])

    st.markdown("""
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
    """, unsafe_allow_html=True)
    
    st.markdown("##### 1. Buscar Ordem de Serviço")
    with st.form("busca_os_form", border=False):
        col1, col2 = st.columns([1, 1])
        with col1:
            tipo_os = st.selectbox("Tipo de OS *", ["OS Interna", "OS Externa"], 
                                   index=st.session_state.get('tipo_os_index', 0))
        with col2:
            numero_os = st.text_input("Número da OS *", 
                                      placeholder="Ex: 1-25", 
                                      value=st.session_state.get('numero_os_input', ''))
        submitted_search = st.form_submit_button("Buscar OS", use_container_width=True, type="primary")
    
    if submitted_search:
        st.session_state.tipo_os_index = ["OS Interna", "OS Externa"].index(tipo_os)
        st.session_state.numero_os_input = numero_os
        f_buscar_os(conn, tipo_os, numero_os)
        st.rerun() 
    
    if 'os_encontrada' in st.session_state:
        os_data = st.session_state.os_encontrada
        st.markdown("##### 2. Informações da OS")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Secretaria", os_data.get('secretaria', 'N/A'))
        col2.metric("Equipamento", os_data.get('equipamento', 'N/A'))
        col3.metric("Status da OS", os_data.get('status', 'N/A'))
        col4.metric("Solicitante", os_data.get('solicitante', 'N/A'))
        
        st.markdown("##### 3. Formulário do Laudo")
        with st.form("laudo_form"):
            st.markdown(f"**Registrando Laudo para OS:** {os_data['numero_os']} ({os_data['tipo_os']})")
            st.session_state.laudo_form_data = {
                "tipo_os": os_data['tipo_os'],
                "numero_os": os_data['numero_os']
            }
            componente = st.selectbox(
                "Componente a Substituir *", sorted(COMPONENTES_LAUDO),
                index=None, placeholder="Selecione o componente..."
            )
            especificacao = st.text_area("Especificação do Componente *", 
                                         placeholder="Ex: SSD SATA 120GB Marca Kingston A400", 
                                         height=120)
            link_compra = st.text_input("Link de Compra (Opcional)", 
                                        placeholder="https://exemplo.com/produto")
            observacoes = st.text_area("Observações (Opcional)", 
                                       placeholder="Informações adicionais sobre o laudo", 
                                       height=120)
            
            tecnico_nome_correto = display_name
            for t in TECNICOS_LAUDO:
                if t.upper() == display_name.upper():
                    tecnico_nome_correto = t
                    break
            
            st.text_input("Técnico Responsável", value=tecnico_nome_correto, disabled=True)
            
            submitted_laudo = st.form_submit_button("Registrar Laudo", use_container_width=True)
            
            if submitted_laudo:
                erros = []
                if not componente:
                    erros.append("O campo 'Componente' é obrigatório.")
                if not especificacao:
                    erros.append("O campo 'Especificação' é obrigatório.")
                if link_compra and not (link_compra.startswith("http://") or link_compra.startswith("https://")):
                    erros.append("O 'Link de Compra' deve ser uma URL válida (ex: https://...)")
                if erros:
                    for erro in erros:
                        st.error(erro)
                else:
                    form_data = st.session_state.laudo_form_data
                    form_data.update({
                        "componente": componente,
                        "especificacao": especificacao,
                        "link_compra": link_compra if link_compra else None,
                        "observacoes": observacoes if observacoes else None,
                        "tecnico": tecnico_nome_correto 
                    })
                    if f_registrar_laudo(conn, form_data):
                        st.session_state.tipo_os_index = 0
                        st.session_state.numero_os_input = ''
                        st.rerun()
    
    render_consulta_laudos(conn)
    render_modal_detalhes(conn)