# CÓDIGO COMPLETO E CORRIGIDO PARA: sistema_os_crud-main/editar_os.py
import streamlit as st
import pandas as pd
from sqlalchemy import text
from database import get_connection
from datetime import datetime, date
import pytz
from config import SECRETARIAS, STATUS_OPTIONS, EQUIPAMENTOS, CATEGORIAS, TECNICOS

def f_atualizar_os(conn, table_name, os_id, dados):
    """Atualiza uma OS específica no banco de dados."""
    try:
        with conn.connect() as con:
            with con.begin():
                # Construir query UPDATE dinamicamente
                set_clause = []
                params = {"id": os_id}
                for key, value in dados.items():
                    if key != "id":
                        set_clause.append(f"{key} = :{key}")
                        params[key] = value
                
                if not set_clause:
                    st.error("Nenhum dado para atualizar.")
                    return False
                
                query = text(f"UPDATE {table_name} SET {', '.join(set_clause)} WHERE id = :id")
                con.execute(query, params)
        
        st.success(f"Ordem de Serviço (ID: {os_id}) atualizada com sucesso!")
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar OS: {e}")
        return False

def get_os_by_id(conn, os_id, table_name):
    """Obtém uma OS específica pelo ID."""
    try:
        with conn.connect() as con:
            query = text(f"SELECT * FROM {table_name} WHERE id = :id")
            result = con.execute(query, {"id": os_id}).fetchone()
            return result._mapping if result else None
    except Exception:
        return None

def render():
    st.title("Atualizar Ordem de Serviço")
    
    conn = get_connection()
    role = st.session_state.get("role", "")
    
    # Verificar permissão
    if role not in ["admin", "administrativo"]:
        st.error("Acesso Negado: Você não tem permissão para editar Ordens de Serviço.")
        st.info("Apenas administradores podem editar OS.")
        return
    
    # Verificar se uma OS foi selecionada para atualizar
    update_os_id = st.session_state.get('update_os_id')
    update_os_tipo = st.session_state.get('update_os_tipo', 'Interna')
    
    if not update_os_id:
        st.error("Nenhuma Ordem de Serviço selecionada para edição.")
        st.info("Volte para 'Minhas Tarefas' e selecione uma OS para atualizar.")
        
        if st.button("Voltar para Minhas Tarefas"):
            st.session_state.current_page = "Minhas Tarefas"
            st.rerun()
        return
    
    # Determinar tabela baseado no tipo
    table_name = "os_interna" if update_os_tipo == "Interna" else "os_externa"
    
    # Buscar dados da OS
    os_data = get_os_by_id(conn, update_os_id, table_name)
    
    if not os_data:
        st.error(f"Ordem de Serviço (ID: {update_os_id}) não encontrada.")
        if st.button("Voltar"):
            st.session_state.update_os_id = None
            st.session_state.current_page = "Minhas Tarefas"
            st.rerun()
        return
    
    # Exibir informações da OS
    st.markdown(f"### Editando OS #{os_data.get('numero', 'N/A')}")
    st.markdown(f"**Tipo:** {os_data.get('tipo', update_os_tipo)} | **Status Atual:** {os_data.get('status', 'N/A')}")
    st.markdown("---")
    
    # Formulário de edição
    with st.form("form_editar_os"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status = st.selectbox(
                "Status *",
                STATUS_OPTIONS,
                index=STATUS_OPTIONS.index(os_data.get('status', 'EM ABERTO')) if os_data.get('status') in STATUS_OPTIONS else 0
            )
        
        with col2:
            secretaria = st.selectbox(
                "Secretaria *",
                sorted(SECRETARIAS),
                index=sorted(SECRETARIAS).index(os_data.get('secretaria')) if os_data.get('secretaria') in sorted(SECRETARIAS) else 0
            )
        
        with col3:
            setor = st.text_input(
                "Setor",
                value=os_data.get('setor', ''),
                placeholder="Ex: TI, Administrativo"
            )
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            tecnico = st.selectbox(
                "Técnico *",
                sorted(TECNICOS),
                index=sorted(TECNICOS).index(os_data.get('tecnico')) if os_data.get('tecnico') in sorted(TECNICOS) else 0
            )
        
        with col2:
            equipamento = st.text_input(
                "Equipamento",
                value=os_data.get('equipamento', ''),
                placeholder="Ex: Desktop, Impressora"
            )
        
        with col3:
            patrimonio = st.text_input(
                "Patrimônio",
                value=os_data.get('patrimonio', ''),
                placeholder="Ex: PA-2024-001"
            )
        
        col1, col2 = st.columns(2)
        
        with col1:
            categoria = st.selectbox(
                "Categoria",
                [''] + sorted(CATEGORIAS),
                index=([''] + sorted(CATEGORIAS)).index(os_data.get('categoria', '')) if os_data.get('categoria') else 0
            )
        
        with col2:
            data_finalizada = st.date_input(
                "Data de Finalização",
                value=pd.to_datetime(os_data.get('data_finalizada')).date() if pd.notna(os_data.get('data_finalizada')) else None
            )
        
        st.markdown("#### Descrição do Serviço")
        servico_executado = st.text_area(
            "Serviço Executado",
            value=os_data.get('servico_executado', ''),
            height=150,
            placeholder="Descreva o serviço realizado..."
        )
        
        submitted = st.form_submit_button("Salvar Alterações", use_container_width=True, type="primary")
        
        if submitted:
            if not secretaria or not tecnico or not status:
                st.error("Preencha todos os campos obrigatórios (marcados com *).")
            else:
                dados_atualizacao = {
                    "status": status,
                    "secretaria": secretaria,
                    "setor": setor if setor else None,
                    "tecnico": tecnico,
                    "equipamento": equipamento if equipamento else None,
                    "patrimonio": patrimonio if patrimonio else None,
                    "categoria": categoria if categoria else None,
                    "servico_executado": servico_executado if servico_executado else None,
                    "data_finalizada": data_finalizada if data_finalizada else None,
                }
                
                if f_atualizar_os(conn, table_name, update_os_id, dados_atualizacao):
                    # Limpar estado e voltar
                    st.session_state.update_os_id = None
                    st.session_state.update_os_tipo = None
                    st.session_state.current_page = "Minhas Tarefas"
                    st.rerun()
    
    st.markdown("---")
    if st.button("Cancelar"):
        st.session_state.update_os_id = None
        st.session_state.update_os_tipo = None
        st.session_state.current_page = "Minhas Tarefas"
        st.rerun()