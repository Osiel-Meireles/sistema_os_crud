# CÓDIGO COMPLETO E CORRIGIDO PARA: sistema_os_crud-main/laudos.py
import streamlit as st
import pandas as pd
from sqlalchemy import text
from database import get_connection
from config import TECNICOS, STATUS_LAUDO
from datetime import datetime
import pytz

TECNICOS_LAUDO = sorted(TECNICOS)

def f_buscar_os(conn, tipo_os, numero_os):
    """Busca uma OS específica no banco de dados."""
    if not numero_os:
        st.error("O campo 'Número da OS' é obrigatório.")
        return None
    
    table_name = "os_interna" if tipo_os == "Interna" else "os_externa"
    query = text(f"""
        SELECT id, numero, secretaria, setor, equipamento, status, solicitante, patrimonio
        FROM {table_name}
        WHERE numero = :numero
    """)
    
    try:
        with conn.connect() as con:
            result = con.execute(query, {"numero": numero_os}).fetchone()
            if result:
                os_data = dict(result._mapping)
                st.session_state.os_encontrada = os_data
                st.session_state.os_encontrada['numero_os'] = numero_os
                st.session_state.os_encontrada['tipo_os'] = tipo_os
                return os_data
            else:
                st.warning(f"OS {tipo_os} com número {numero_os} não encontrada.")
                if 'os_encontrada' in st.session_state:
                    del st.session_state.os_encontrada
                return None
    except Exception as e:
        st.error(f"Erro ao buscar OS: {e}")
        if 'os_encontrada' in st.session_state:
            del st.session_state.os_encontrada
        return None

def f_registrar_laudo(conn, data):
    """Insere o laudo de avaliação técnica."""
    try:
        with conn.connect() as con:
            with con.begin():
                query_laudo = text("""
                    INSERT INTO laudos (
                        tipo_os, numero_os, estado_conservacao, diagnostico,
                        equipamento_completo, observacoes, tecnico, status
                    ) VALUES (
                        :tipo_os, :numero_os, :estado_conservacao, :diagnostico,
                        :equipamento_completo, :observacoes, :tecnico, 'PENDENTE'
                    )
                """)
                con.execute(query_laudo, data)
                
                # Atualizar status da OS para AGUARDANDO PEÇA(S)
                tipo_os = data.get('tipo_os')  # "OS Interna" ou "OS Externa"
                numero_os = data.get('numero_os')
                
                # Determinar qual tabela usar
                if "Interna" in tipo_os:
                    table_name = "os_interna"
                else:
                    table_name = "os_externa"
                
                query_update_os = text(f"""
                    UPDATE {table_name}
                    SET status = 'AGUARDANDO PEÇA(S)'
                    WHERE numero = :numero
                """)
                con.execute(query_update_os, {"numero": numero_os})
        
        st.success("Laudo de Avaliação Técnica registrado com sucesso!")
        st.info("O status da Ordem de Serviço foi alterado para 'AGUARDANDO PEÇA(S)'")
        if 'os_encontrada' in st.session_state:
            del st.session_state.os_encontrada
        return True
    except Exception as e:
        st.error(f"Erro ao registrar o laudo: {e}")
        return False

def f_atualizar_status_laudo(conn, laudo_id, novo_status):
    """Atualiza o status de um laudo."""
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
    """Exibe modal com detalhes do laudo."""
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
        st.markdown(f"**ID do Laudo:** {laudo['id']}")
        st.markdown(f"**Número da OS:** {laudo['numero_os']} ({laudo['tipo_os']})")
        st.markdown(f"**Status:** {laudo['status']}")
        
        st.divider()
        
        st.markdown(f"**Estado de Conservação:** {laudo.get('estado_conservacao', 'N/A')}")
        st.markdown(f"**Equipamento Completo:** {laudo.get('equipamento_completo', 'N/A')}")
        
        st.markdown("**Diagnóstico Técnico:**")
        st.text_area(
            "modal_diag",
            value=laudo.get('diagnostico', ''),
            height=150,
            disabled=True,
            label_visibility="collapsed"
        )
        
        if laudo.get('observacoes'):
            st.markdown("**Observações:**")
            st.text_area(
                "modal_obs",
                value=laudo['observacoes'],
                height=100,
                disabled=True,
                label_visibility="collapsed"
            )
        
        st.markdown(f"**Técnico Responsável:** {laudo['tecnico']}")
        
        fuso_sp = pytz.timezone('America/Sao_Paulo')
        data_reg = laudo['data_registro'].astimezone(fuso_sp).strftime('%d/%m/%Y %H:%M:%S')
        st.markdown(f"**Data de Registro:** {data_reg}")
        
        if laudo['data_atendimento']:
            data_at = laudo['data_atendimento'].astimezone(fuso_sp).strftime('%d/%m/%Y %H:%M:%S')
            st.markdown(f"**Última Atualização:** {data_at}")
        
        st.divider()
        st.markdown("#### Atualizar Status do Laudo")
        
        try:
            current_status_index = STATUS_LAUDO.index(laudo['status'])
        except ValueError:
            current_status_index = 0
        
        novo_status = st.selectbox(
            "Selecione o novo status",
            STATUS_LAUDO,
            index=current_status_index,
            key="modal_status_select"
        )
        
        col_b1, col_b2 = st.columns(2)
        if col_b1.button("Salvar Novo Status", type="primary", use_container_width=True):
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

def render():
    st.title("Laudos Técnicos")
    conn = get_connection()
    
    render_modal_detalhes(conn)
    
    # Verificar se veio de Minhas Tarefas com OS pré-selecionada
    laudo_os_id = st.session_state.get('laudo_os_id')
    laudo_os_numero = st.session_state.get('laudo_os_numero')
    laudo_os_tipo = st.session_state.get('laudo_os_tipo', 'Interna')
    
    st.markdown("---")
    
    # CRIAR ABAS
    tab1, tab2 = st.tabs(["Registrar Laudo", "Consulta de Laudos"])
    
    # ================= ABA 1: REGISTRAR LAUDO =================
    with tab1:
        # Seção de pesquisa/seleção de OS
        st.markdown("### Selecionar Ordem de Serviço")
        
        col1, col2 = st.columns(2)
        with col1:
            # Se veio pré-selecionado, usar esse valor como padrão
            tipo_os_options = ["Interna", "Externa"]
            tipo_os_index = tipo_os_options.index(laudo_os_tipo) if laudo_os_tipo in tipo_os_options else 0
            
            tipo_os = st.selectbox(
                "Tipo de OS",
                tipo_os_options,
                index=tipo_os_index,
                key="select_tipo_os_laudo"
            )
        
        with col2:
            numero_os = st.text_input(
                "Número da OS",
                value=laudo_os_numero if laudo_os_numero else "",
                placeholder="Ex: 1-25",
                key="input_numero_os_laudo"
            )
        
        # Se veio de Minhas Tarefas, já buscar automaticamente
        if laudo_os_id and laudo_os_numero and 'os_encontrada' not in st.session_state:
            f_buscar_os(conn, tipo_os, laudo_os_numero)
        
        if st.button("Buscar OS", use_container_width=True):
            f_buscar_os(conn, tipo_os, numero_os)
        
        os_encontrada = st.session_state.get('os_encontrada')
        
        if os_encontrada:
            st.markdown("---")
            st.success("OS Encontrada!")
            
            # Exibir informações da OS
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Número", os_encontrada.get('numero_os', 'N/A'))
            with col2:
                st.metric("Tipo", os_encontrada.get('tipo_os', 'N/A'))
            with col3:
                st.metric("Status", os_encontrada.get('status', 'N/A'))
            
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Secretaria:** {os_encontrada.get('secretaria', 'N/A')}")
                st.write(f"**Setor:** {os_encontrada.get('setor', 'N/A')}")
                st.write(f"**Solicitante:** {os_encontrada.get('solicitante', 'N/A')}")
            with col2:
                st.write(f"**Equipamento:** {os_encontrada.get('equipamento', 'N/A')}")
                st.write(f"**Patrimônio:** {os_encontrada.get('patrimonio', 'N/A')}")
            
            st.markdown("---")
            st.markdown("### Dados do Laudo Técnico")
            
            with st.form("form_laudo"):
                col1, col2 = st.columns(2)
                with col1:
                    estado_conservacao = st.selectbox(
                        "Estado de Conservação *",
                        ["Funcionando", "Com Defeito", "Danificado", "Para Reciclagem"]
                    )
                with col2:
                    equipamento_completo = st.selectbox(
                        "Equipamento Completo? *",
                        ["Sim", "Não", "Parcialmente"]
                    )
                
                diagnostico = st.text_area(
                    "Diagnóstico Técnico *",
                    height=150,
                    placeholder="Descreva o diagnóstico técnico da OS..."
                )
                
                observacoes = st.text_area(
                    "Observações Adicionais",
                    height=100,
                    placeholder="Observações opcionais..."
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    # Puxar automaticamente o técnico logado se veio de Minhas Tarefas
                    tecnico_logado = st.session_state.get('laudo_tecnico')
                    
                    if tecnico_logado:
                        # Se veio de Minhas Tarefas, mostrar o técnico logado (desabilitado)
                        st.write(f"**Técnico Responsável:** {tecnico_logado}")
                        tecnico = tecnico_logado
                    else:
                        # Se foi busca manual, permitir seleção
                        tecnico = st.selectbox(
                            "Técnico Responsável *",
                            TECNICOS_LAUDO
                        )
                with col2:
                    st.empty()
                
                submitted = st.form_submit_button("Registrar Laudo", use_container_width=True, type="primary")
                
                if submitted:
                    if not diagnostico or not estado_conservacao or not equipamento_completo or not tecnico:
                        st.error("Preencha todos os campos obrigatórios (marcados com *).")
                    else:
                        dados_laudo = {
                            "tipo_os": os_encontrada.get('tipo_os'),
                            "numero_os": os_encontrada.get('numero_os'),
                            "estado_conservacao": estado_conservacao,
                            "diagnostico": diagnostico,
                            "equipamento_completo": equipamento_completo,
                            "observacoes": observacoes if observacoes else None,
                            "tecnico": tecnico
                        }
                        
                        if f_registrar_laudo(conn, dados_laudo):
                            st.session_state.laudo_os_id = None
                            st.session_state.laudo_os_numero = None
                            st.session_state.laudo_os_tipo = None
                            st.session_state.laudo_tecnico = None
                            st.session_state.current_page = "Minhas Tarefas"
                            st.rerun()
        else:
            st.info("Busque por uma OS para continuar.")
    
    # ================= ABA 2: CONSULTA DE LAUDOS =================
    with tab2:
        st.markdown("### Consulta de Laudos Técnicos")
        
        with st.expander("Filtros de Pesquisa"):
            col1, col2 = st.columns(2)
            with col1:
                f_tipo_os = st.multiselect("Tipo de OS", ["Interna", "Externa"], key="filter_tipo_os")
                f_status = st.multiselect("Status do Laudo", STATUS_LAUDO, key="filter_status")
            with col2:
                f_tecnico = st.multiselect("Técnico", TECNICOS_LAUDO, key="filter_tecnico")
                f_numero_os = st.text_input("Número da OS", key="filter_numero_os")
            
            filtrar = st.button("Aplicar Filtros", use_container_width=True)
        
        if filtrar or 'df_laudos_filtrados' in st.session_state:
            if filtrar:
                query_base = "SELECT id, numero_os, tipo_os, diagnostico, estado_conservacao, status, tecnico FROM laudos"
                where_clauses = []
                params = {}
                
                if f_tipo_os:
                    placeholders = ','.join([f":tipo{i}" for i in range(len(f_tipo_os))])
                    where_clauses.append(f"tipo_os IN ({placeholders})")
                    for i, t in enumerate(f_tipo_os):
                        params[f"tipo{i}"] = t
                
                if f_status:
                    placeholders = ','.join([f":status{i}" for i in range(len(f_status))])
                    where_clauses.append(f"status IN ({placeholders})")
                    for i, s in enumerate(f_status):
                        params[f"status{i}"] = s
                
                if f_tecnico:
                    placeholders = ','.join([f":tec{i}" for i in range(len(f_tecnico))])
                    where_clauses.append(f"tecnico IN ({placeholders})")
                    for i, t in enumerate(f_tecnico):
                        params[f"tec{i}"] = t
                
                if f_numero_os:
                    where_clauses.append("numero_os ILIKE :numero_os")
                    params["numero_os"] = f"%{f_numero_os}%"
                
                if where_clauses:
                    query_base += " WHERE " + " AND ".join(where_clauses)
                
                query_base += " ORDER BY id DESC"
                
                try:
                    with conn.connect() as con:
                        df_laudos = pd.read_sql(text(query_base), con, params=params)
                    st.session_state.df_laudos_filtrados = df_laudos
                except Exception as e:
                    st.error(f"Erro ao filtrar laudos: {e}")
                    return
            
            df_laudos = st.session_state.get('df_laudos_filtrados', pd.DataFrame())
            
            if df_laudos.empty:
                st.info("Nenhum laudo encontrado.")
            else:
                st.markdown(f"**{len(df_laudos)} Laudo(s) encontrado(s)**")
                
                cols_header = st.columns((0.5, 1, 1, 2, 1.5, 1, 0.8))
                headers = ["ID", "OS", "Tipo", "Diagnóstico", "Estado", "Status", ""]
                for col, header in zip(cols_header, headers):
                    col.markdown(f"**{header}**")
                
                st.markdown("<hr style='margin-top: 0; margin-bottom: 0;'>", unsafe_allow_html=True)
                
                for idx, row in df_laudos.iterrows():
                    cols = st.columns((0.5, 1, 1, 2, 1.5, 1, 0.8))
                    cols[0].write(str(row["id"]))
                    cols[1].write(str(row["numero_os"]))
                    cols[2].write(str(row["tipo_os"]))
                    
                    diagnostico_resumido = str(row["diagnostico"])[:40] + "..." if len(str(row["diagnostico"])) > 40 else str(row["diagnostico"])
                    cols[3].write(diagnostico_resumido)
                    
                    cols[4].write(str(row.get("estado_conservacao", "N/A")))
                    cols[5].write(str(row["status"]))
                    
                    if cols[6].button("👁️", key=f"view_{row['id']}", help="Ver detalhes do laudo", use_container_width=True):
                        st.session_state.view_laudo_id = row["id"]
                        st.rerun()
                    
                    st.markdown("<hr style='margin-top: 0; margin-bottom: 0;'>", unsafe_allow_html=True)