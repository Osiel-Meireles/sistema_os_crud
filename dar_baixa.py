# CÓDIGO COMPLETO E CORRIGIDO PARA: sistema_os_crud-main/dar_baixa.py
import streamlit as st
import pandas as pd
from database import get_connection
from sqlalchemy import text
from datetime import datetime
import pytz
from config import STATUS_OPTIONS

def f_buscar_os_para_baixa(conn, tipo_os, numero_os):
    """Busca uma OS específica no banco de dados para dar baixa."""
    if not numero_os:
        st.error("O campo 'Número da OS' é obrigatório.")
        return None
    
    table_name = "os_interna" if tipo_os == "Interna" else "os_externa"
    query = text(f"""
        SELECT id, numero, secretaria, setor, equipamento, status, solicitante, 
               patrimonio, categoria, tecnico, data, solicitacao_cliente
        FROM {table_name}
        WHERE numero = :numero
    """)
    
    try:
        with conn.connect() as con:
            result = con.execute(query, {"numero": numero_os}).fetchone()
            if result:
                os_data = dict(result._mapping)
                st.session_state.os_baixa_encontrada = os_data
                st.session_state.os_baixa_encontrada['numero_os'] = numero_os
                st.session_state.os_baixa_encontrada['tipo_os'] = tipo_os
                return os_data
            else:
                st.warning(f"OS {tipo_os} com número {numero_os} não encontrada.")
                if 'os_baixa_encontrada' in st.session_state:
                    del st.session_state.os_baixa_encontrada
                return None
    except Exception as e:
        st.error(f"Erro ao buscar OS: {e}")
        if 'os_baixa_encontrada' in st.session_state:
            del st.session_state.os_baixa_encontrada
        return None

def f_dar_baixa(conn, table_name, os_id, dados_baixa, role):
    """Atualiza o status da OS para baixa/finalização."""
    try:
        with conn.connect() as con:
            with con.begin():
                # REGRA DE NEGÓCIO: Se técnico escolheu "FINALIZADO", muda para "AGUARDANDO RETIRADA"
                if role == "tecnico" and dados_baixa.get("status") == "FINALIZADO":
                    dados_baixa["status"] = "AGUARDANDO RETIRADA"
                
                # Construir query UPDATE
                set_clause = []
                params = {"id": os_id}
                for key, value in dados_baixa.items():
                    if key != "id":
                        set_clause.append(f"{key} = :{key}")
                        params[key] = value
                
                if not set_clause:
                    st.error("Nenhum dado para atualizar.")
                    return False
                
                query = text(f"UPDATE {table_name} SET {', '.join(set_clause)} WHERE id = :id")
                con.execute(query, params)
        
        # Mensagem baseada no perfil
        if role == "tecnico":
            st.success("OS finalizada! Status alterado para 'AGUARDANDO RETIRADA'")
        else:
            st.success(f"Baixa registrada com sucesso!")
        return True
    except Exception as e:
        st.error(f"Erro ao registrar baixa: {e}")
        return False

def render():
    st.title("Dar Baixa - Finalizar Ordem de Serviço")
    
    conn = get_connection()
    role = st.session_state.get('role', '')
    
    # Verificar se veio de Minhas Tarefas com OS pré-selecionada
    baixa_os_id = st.session_state.get('baixa_os_id')
    baixa_os_numero = st.session_state.get('baixa_os_numero')
    baixa_os_tipo = st.session_state.get('baixa_os_tipo', 'Interna')
    
    st.markdown("---")
    
    # Exibir informação de permissões
    if role == "tecnico":
        st.info("Como técnico, você pode finalizar a OS. O status será automaticamente alterado para 'AGUARDANDO RETIRADA'.")
    elif role in ["admin", "administrativo"]:
        st.info("Como administrador, você pode registrar a retirada e informar quem retirou o equipamento.")
    
    st.markdown("---")
    
    # Seção de pesquisa/seleção de OS
    st.markdown("### Selecionar Ordem de Serviço para Baixa")
    
    col1, col2 = st.columns(2)
    with col1:
        tipo_os_options = ["Interna", "Externa"]
        tipo_os_index = tipo_os_options.index(baixa_os_tipo) if baixa_os_tipo in tipo_os_options else 0
        
        tipo_os = st.selectbox(
            "Tipo de OS",
            tipo_os_options,
            index=tipo_os_index,
            key="select_tipo_os_baixa"
        )
    
    with col2:
        numero_os = st.text_input(
            "Número da OS",
            value=baixa_os_numero if baixa_os_numero else "",
            placeholder="Ex: 1-25",
            key="input_numero_os_baixa"
        )
    
    # Se veio de Minhas Tarefas, já buscar automaticamente
    if baixa_os_id and baixa_os_numero and 'os_baixa_encontrada' not in st.session_state:
        f_buscar_os_para_baixa(conn, tipo_os, baixa_os_numero)
    
    if st.button("Buscar OS", use_container_width=True):
        f_buscar_os_para_baixa(conn, tipo_os, numero_os)
    
    os_encontrada = st.session_state.get('os_baixa_encontrada')
    
    if os_encontrada:
        # Validação: Se é técnico, só pode dar baixa em suas próprias OS
        display_name = st.session_state.get('display_name', '')
        if role == "tecnico" and os_encontrada.get('tecnico') != display_name:
            st.error("Você só pode dar baixa em suas próprias Ordens de Serviço.")
            st.warning(f"Esta OS está atribuída a: {os_encontrada.get('tecnico')}")
            st.session_state.pop('os_baixa_encontrada', None)
            return
        
        st.markdown("---")
        st.success("OS Encontrada para Dar Baixa!")
        
        # Exibir informações da OS
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Número", os_encontrada.get('numero_os', 'N/A'))
        with col2:
            st.metric("Tipo", os_encontrada.get('tipo_os', 'N/A'))
        with col3:
            st.metric("Status Atual", os_encontrada.get('status', 'N/A'))
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Secretaria:** {os_encontrada.get('secretaria', 'N/A')}")
            st.write(f"**Setor:** {os_encontrada.get('setor', 'N/A')}")
            st.write(f"**Técnico:** {os_encontrada.get('tecnico', 'N/A')}")
        with col2:
            st.write(f"**Equipamento:** {os_encontrada.get('equipamento', 'N/A')}")
            st.write(f"**Patrimônio:** {os_encontrada.get('patrimonio', 'N/A')}")
            st.write(f"**Solicitante:** {os_encontrada.get('solicitante', 'N/A')}")
        
        # Formatar data
        data_formatada = "N/A"
        if pd.notna(os_encontrada.get('data')):
            try:
                data_formatada = pd.to_datetime(os_encontrada.get('data')).strftime("%d/%m/%Y")
            except:
                data_formatada = str(os_encontrada.get('data'))
        
        st.write(f"**Data da OS:** {data_formatada}")
        
        if os_encontrada.get('solicitacao_cliente'):
            st.markdown("**Solicitação do Cliente:**")
            st.text(str(os_encontrada.get('solicitacao_cliente')))
        
        st.markdown("---")
        st.markdown("### Registrar Baixa da OS")
        
        with st.form("form_dar_baixa"):
            col1, col2 = st.columns(2)
            
            with col1:
                # REGRA: Técnicos podem apenas finalizar
                if role == "tecnico":
                    status_options = ["FINALIZADO"]
                    status_novo = st.selectbox(
                        "Novo Status *",
                        status_options,
                        key="select_status_baixa_tecnico"
                    )
                    st.caption("Técnico: Ao salvar, o status será automaticamente alterado para 'AGUARDANDO RETIRADA'")
                else:
                    # Admin/Administrativo podem escolher qualquer status
                    status_novo = st.selectbox(
                        "Novo Status *",
                        STATUS_OPTIONS,
                        index=STATUS_OPTIONS.index(os_encontrada.get('status', 'EM ABERTO')) if os_encontrada.get('status') in STATUS_OPTIONS else 0,
                        key="select_status_baixa_admin"
                    )
            
            with col2:
                data_finalizacao = st.date_input(
                    "Data de Finalização *",
                    value=datetime.now().date(),
                    key="date_finalizacao_baixa"
                )
            
            observacoes_finalizacao = st.text_area(
                "Observações da Finalização",
                height=150,
                placeholder="Descreva observações sobre a finalização da OS...",
                key="textarea_obs_baixa"
            )
            
            # REGRA: Apenas admin/administrativo podem registrar retirada
            if role in ["admin", "administrativo"]:
                st.divider()
                st.markdown("#### Registro de Retirada (Apenas Admin/Administrativo)")
                
                retirada_por = st.text_input(
                    "Retirado por (Nome de quem retirou o equipamento) *",
                    placeholder="Nome completo da pessoa que retirou",
                    key="input_retirada_por"
                )
                
                data_retirada = st.date_input(
                    "Data da Retirada",
                    value=datetime.now().date(),
                    key="date_retirada"
                )
            else:
                # Técnicos não veem campo de retirada
                retirada_por = None
                st.info("O registro de retirada será preenchido apenas por administradores.")
            
            submitted = st.form_submit_button("Registrar Baixa", use_container_width=True, type="primary")
            
            if submitted:
                # Validações
                if not status_novo or not data_finalizacao:
                    st.error("Preencha todos os campos obrigatórios (marcados com *).")
                elif role in ["admin", "administrativo"] and not retirada_por:
                    st.error("Como administrador, você deve informar quem retirou o equipamento.")
                else:
                    # Determinar tabela baseado no tipo
                    table_name = "os_interna" if os_encontrada.get('tipo_os') == "Interna" else "os_externa"
                    
                    dados_baixa = {
                        "status": status_novo,
                        "data_finalizada": data_finalizacao if data_finalizacao else None,
                        "descricao": observacoes_finalizacao if observacoes_finalizacao else None,
                    }
                    
                    # Adicionar retirada_por apenas se for admin/administrativo
                    if role in ["admin", "administrativo"] and retirada_por:
                        dados_baixa["retirada_por"] = retirada_por
                    
                    if f_dar_baixa(conn, table_name, os_encontrada.get('id'), dados_baixa, role):
                        # Limpar estado e voltar
                        st.session_state.baixa_os_id = None
                        st.session_state.baixa_os_numero = None
                        st.session_state.baixa_os_tipo = None
                        if 'os_baixa_encontrada' in st.session_state:
                            del st.session_state.os_baixa_encontrada
                        st.session_state.current_page = "Minhas Tarefas"
                        st.rerun()
    else:
        st.info("Busque por uma OS para registrar a baixa.")
    
    st.markdown("---")
    
    if st.button("Voltar para Minhas Tarefas"):
        st.session_state.baixa_os_id = None
        st.session_state.baixa_os_numero = None
        st.session_state.baixa_os_tipo = None
        if 'os_baixa_encontrada' in st.session_state:
            del st.session_state.os_baixa_encontrada
        st.session_state.current_page = "Minhas Tarefas"
        st.rerun()