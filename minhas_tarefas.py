import streamlit as st
import pandas as pd
from sqlalchemy import text
from database import get_connection
from config import STATUS_OPTIONS, CATEGORIAS, EQUIPAMENTOS
from datetime import datetime
import pytz
import math

def buscar_tarefas_tecnico(conn, display_name):
    """Busca todas as OSs atribuídas ao técnico logado (Apenas Pendentes)."""
    try:
        query = text("""
            SELECT *, 'Interna' as tipo FROM os_interna 
            WHERE tecnico = :tecnico AND status NOT IN ('ENTREGUE AO CLIENTE', 'AGUARDANDO RETIRADA', 'FINALIZADO')
            UNION ALL 
            SELECT *, 'Externa' as tipo FROM os_externa 
            WHERE tecnico = :tecnico AND status NOT IN ('ENTREGUE AO CLIENTE', 'AGUARDANDO RETIRADA', 'FINALIZADO')
            ORDER BY data DESC, hora DESC
        """)
        with conn.connect() as con:
            result = con.execute(query, {"tecnico": display_name})
            rows = result.fetchall()
            columns = result.keys()
            df = pd.DataFrame(rows, columns=columns)
        return df
    except Exception as e:
        st.error(f"Erro ao buscar tarefas: {e}")
        return pd.DataFrame()

def contar_os_abertas(conn, display_name):
    """Conta OSs em aberto atribuídas ao técnico."""
    try:
        query = text("""
            SELECT COUNT(*) as total FROM (
                SELECT id FROM os_interna WHERE tecnico = :tecnico AND status = 'EM ABERTO'
                UNION ALL 
                SELECT id FROM os_externa WHERE tecnico = :tecnico AND status = 'EM ABERTO'
            ) as combined
        """)
        with conn.connect() as con:
            result = con.execute(query, {"tecnico": display_name}).fetchone()
        return result[0] if result else 0
    except Exception:
        return 0

def contar_os_aguardando_pecas(conn, display_name):
    """Conta OSs aguardando peças atribuídas ao técnico."""
    try:
        query = text("""
            SELECT COUNT(*) as total FROM (
                SELECT id FROM os_interna WHERE tecnico = :tecnico AND status = 'AGUARDANDO PEÇA(S)'
                UNION ALL 
                SELECT id FROM os_externa WHERE tecnico = :tecnico AND status = 'AGUARDANDO PEÇA(S)'
            ) as combined
        """)
        with conn.connect() as con:
            result = con.execute(query, {"tecnico": display_name}).fetchone()
        return result[0] if result else 0
    except Exception:
        return 0

def buscar_os_pendentes_laudo(conn, display_name):
    """Busca OSs com status AGUARDANDO PEÇA(S) que ainda não têm laudo."""
    try:
        # ✅ CORREÇÃO: Query 1 com context manager próprio
        query_os = text("""
            SELECT id, numero, 'Interna' as tipo, secretaria, equipamento, status, data 
            FROM os_interna WHERE tecnico = :tecnico AND status = 'AGUARDANDO PEÇA(S)'
            UNION ALL 
            SELECT id, numero, 'Externa' as tipo, secretaria, equipamento, status, data 
            FROM os_externa WHERE tecnico = :tecnico AND status = 'AGUARDANDO PEÇA(S)'
            ORDER BY data DESC
        """)
        
        df_os = pd.DataFrame()
        os_sem_laudo = []
        
        # Buscar OSs aguardando peças
        with conn.connect() as con:
            result = con.execute(query_os, {"tecnico": display_name})
            rows = result.fetchall()
            columns = result.keys()
            df_os = pd.DataFrame(rows, columns=columns)
        
        # ✅ CORREÇÃO: NOVA conexão para cada verificação de laudo
        for _, row in df_os.iterrows():
            tipo_os_laudo = f"OS {row['tipo']}"
            query_laudo = text("""
                SELECT COUNT(*) as total FROM laudos 
                WHERE numero_os = :numero AND (tipo_os = :tipo OR tipo_os = :tipo_simples)
            """)
            
            with conn.connect() as con:  # ✅ NOVA conexão para cada query laudo
                result_laudo = con.execute(query_laudo, {
                    "numero": row['numero'], 
                    "tipo": tipo_os_laudo, 
                    "tipo_simples": row['tipo']
                }).fetchone()
                
                if result_laudo and result_laudo[0] == 0:
                    os_sem_laudo.append(row)
                    
        return pd.DataFrame(os_sem_laudo) if os_sem_laudo else pd.DataFrame()
        
    except Exception as e:
        st.error(f"Erro ao buscar OS pendentes de laudo: {e}")
        return pd.DataFrame()

def buscar_os_recentes_finalizadas(conn, display_name, limite=5):
    """Busca as últimas OSs finalizadas do técnico (Inclui Aguardando Retirada)."""
    try:
        query = text("""
            SELECT *, 'Interna' as tipo FROM os_interna 
            WHERE tecnico = :tecnico AND status IN ('FINALIZADO', 'AGUARDANDO RETIRADA', 'ENTREGUE AO CLIENTE')
            UNION ALL 
            SELECT *, 'Externa' as tipo FROM os_externa 
            WHERE tecnico = :tecnico AND status IN ('FINALIZADO', 'AGUARDANDO RETIRADA', 'ENTREGUE AO CLIENTE')
            ORDER BY data_finalizada DESC LIMIT :limite
        """)
        with conn.connect() as con:
            result = con.execute(query, {"tecnico": display_name, "limite": limite})
            rows = result.fetchall()
            columns = result.keys()
            df = pd.DataFrame(rows, columns=columns)
        return df
    except Exception as e:
        st.error(f"Erro ao buscar OS finalizadas: {e}")
        return pd.DataFrame()

def display_expandable_card(row, display_name):
    """Exibe um card expansível com informações da OS usando identificadores únicos."""
    # ✅ IDENTIFICADOR ÚNICO E ESTÁVEL por OS
    os_id = row.get('id')
    os_tipo = row.get('tipo', 'N/A')
    os_numero = row.get('numero', 'N/A')
    card_key = f"card_{os_tipo}_{os_id}_{os_numero}"
    
    status = row.get('status', 'N/A')
    if status == "EM ABERTO":
        status_emoji = "🔴"
    elif status == "AGUARDANDO PEÇA(S)":
        status_emoji = "🟠"
    elif status in ["FINALIZADO", "AGUARDANDO RETIRADA", "ENTREGUE AO CLIENTE"]:
        status_emoji = "🟢"
    else:
        status_emoji = "⚪"
    
    titulo = f"OS #{os_numero} - {row.get('secretaria', 'N/A')} - {status_emoji} {status}"
    
    # ✅ SEM key no expander (não suportado pelo Streamlit)
    with st.expander(titulo, expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"**Número:** {os_numero}")
            st.markdown(f"**Tipo:** {os_tipo}")
            st.markdown(f"**Patrimônio:** {row.get('patrimonio', 'N/A')}")
        with col2:
            st.markdown(f"**Secretaria:** {row.get('secretaria', 'N/A')}")
            st.markdown(f"**Setor:** {row.get('setor', 'N/A')}")
            st.markdown(f"**Categoria:** {row.get('categoria', 'N/A')}")
        with col3:
            st.markdown(f"**Equipamento:** {row.get('equipamento', 'N/A')}")
            st.markdown(f"**Marca/Modelo:** {row.get('descricao', 'N/A')}")
        
        try:
            data_formatada = pd.to_datetime(row.get('data')).strftime('%d/%m/%Y')
            st.markdown(f"**Data:** {data_formatada}")
        except:
            st.markdown(f"**Data:** {row.get('data', 'N/A')}")
        
        st.markdown("---")
        st.markdown("**Solicitação do Cliente:**")
        st.text_area(
            "Solicitação", 
            value=row.get('solicitacao_cliente', '') or '', 
            disabled=True, 
            height=100, 
            label_visibility="collapsed", 
            key=f"solicitacao_{card_key}"
        )
        
        st.markdown("**Serviço Executado / Descrição:**")
        texto_servico = f"{row.get('servico_executado', '') or ''}\n{row.get('servico_executado_extra', '') or ''}".strip()
        st.text_area(
            "Serviço", 
            value=texto_servico, 
            disabled=True, 
            height=100, 
            label_visibility="collapsed", 
            key=f"servico_{card_key}"
        )
        
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button(
                "Atualizar/Finalizar OS", 
                use_container_width=True, 
                key=f"btn_atualizar_{card_key}",
                type="primary"
            ):
                st.session_state.baixa_os_numero = os_numero
                st.session_state.baixa_os_tipo = os_tipo
                st.session_state.baixa_os_id = os_id
                st.session_state.current_page = "Dar Baixa"
                st.rerun()
        with col2:
            if st.button(
                "Registrar Laudo para esta OS", 
                use_container_width=True, 
                key=f"btn_laudo_{card_key}"
            ):
                st.session_state.laudo_os_id = os_id
                st.session_state.laudo_os_numero = os_numero
                st.session_state.laudo_os_tipo = os_tipo
                st.session_state.laudo_tecnico = display_name
                st.session_state.current_page = "Laudos"
                st.rerun()

def render_pagination_controls(page_var_name, total_pages):
    current_page = st.session_state.get(page_var_name, 1)
    col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
    
    with col1:
        if st.button("⏮️ Primeira", disabled=(current_page == 1), key=f"first_{page_var_name}"):
            st.session_state[page_var_name] = 1
            st.rerun()
    with col2:
        if st.button("◀️ Anterior", disabled=(current_page == 1), key=f"prev_{page_var_name}"):
            st.session_state[page_var_name] -= 1
            st.rerun()
    with col3:
        st.markdown(
            f"<div style='text-align: center;'>Página {current_page} de {total_pages}</div>",
            unsafe_allow_html=True,
        )
    with col4:
        if st.button("Próxima ▶️", disabled=(current_page >= total_pages), key=f"next_{page_var_name}"):
            st.session_state[page_var_name] += 1
            st.rerun()
    with col5:
        if st.button("⏭️ Última", disabled=(current_page >= total_pages), key=f"last_{page_var_name}"):
            st.session_state[page_var_name] = total_pages
            st.rerun()

def render():
    st.markdown("## Minhas Tarefas")
    
    conn = get_connection()
    display_name = st.session_state.get('display_name', st.session_state.get('username', ''))
    
    total_abertas = contar_os_abertas(conn, display_name)
    total_aguardando_pecas = contar_os_aguardando_pecas(conn, display_name)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("OSs em Aberto", total_abertas)
    with col2:
        st.metric("Aguardando Peças", total_aguardando_pecas)
    with col3:
        total_ativas = total_abertas + total_aguardando_pecas
        st.metric("Total Ativo", total_ativas)
    
    st.markdown("---")
    
    ITEMS_PER_PAGE = 5
    tab1, tab2, tab3 = st.tabs(["OSs em Aberto", "Pendentes de Laudo", "Últimas Finalizadas"])
    
    with tab1:
        st.markdown("### Ordens de Serviço em Aberto")
        df_abertas = buscar_tarefas_tecnico(conn, display_name)
        
        if df_abertas.empty:
            st.success("✅ Parabéns! Você não tem ordens de serviço em aberto no momento.")
        else:
            if "tarefas_page" not in st.session_state:
                st.session_state.tarefas_page = 1
            
            total_items = len(df_abertas)
            total_pages = math.ceil(total_items / ITEMS_PER_PAGE)
            
            if st.session_state.tarefas_page > total_pages:
                st.session_state.tarefas_page = total_pages
            if st.session_state.tarefas_page < 1:
                st.session_state.tarefas_page = 1
            
            start_idx = (st.session_state.tarefas_page - 1) * ITEMS_PER_PAGE
            end_idx = start_idx + ITEMS_PER_PAGE
            df_page = df_abertas.iloc[start_idx:end_idx]
            
            st.info(f"📋 Exibindo {len(df_page)} de {total_items} ordens | Página {st.session_state.tarefas_page} de {total_pages}")
            
            for _, row in df_page.iterrows():
                display_expandable_card(row, display_name)
            
            if total_pages > 1:
                st.markdown("---")
                render_pagination_controls("tarefas_page", total_pages)
    
    with tab2:
        st.markdown("### OSs Aguardando Laudo de Avaliação")
        df_pendentes = buscar_os_pendentes_laudo(conn, display_name)
        
        if df_pendentes.empty:
            st.success("✅ Não há ordens de serviço pendentes de laudo.")
        else:
            if "pendentes_page" not in st.session_state:
                st.session_state.pendentes_page = 1
            
            total_items = len(df_pendentes)
            total_pages = math.ceil(total_items / ITEMS_PER_PAGE)
            
            if st.session_state.pendentes_page > total_pages:
                st.session_state.pendentes_page = total_pages
            if st.session_state.pendentes_page < 1:
                st.session_state.pendentes_page = 1
            
            start_idx = (st.session_state.pendentes_page - 1) * ITEMS_PER_PAGE
            end_idx = start_idx + ITEMS_PER_PAGE
            df_page = df_pendentes.iloc[start_idx:end_idx]
            
            st.warning(f"⚠️ {total_items} OSs aguardando laudo | Página {st.session_state.pendentes_page} de {total_pages}")
            
            for _, row in df_page.iterrows():
                card_id = f"pendente_{row.get('id')}_{row.get('numero')}"
                col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
                with col1:
                    st.markdown(f"**OS #{row.get('numero')}**")
                    st.caption(row.get('tipo'))
                with col2:
                    st.markdown(f"**{row.get('secretaria')}**")
                    st.caption(row.get('equipamento', 'N/A'))
                with col3:
                    st.markdown(f"**{row.get('status')}**")
                    try:
                        data_fmt = pd.to_datetime(row.get('data')).strftime('%d/%m/%Y')
                        st.caption(data_fmt)
                    except:
                        st.caption(row.get('data', 'N/A'))
                with col4:
                    if st.button("📋 Laudo", key=f"btn_laudo_pendente_{card_id}", use_container_width=True):
                        st.session_state.laudo_os_id = row.get('id')
                        st.session_state.laudo_os_numero = row.get('numero')
                        st.session_state.laudo_os_tipo = row.get('tipo')
                        st.session_state.laudo_tecnico = display_name
                        st.session_state.current_page = "Laudos"
                        st.rerun()
            
            if total_pages > 1:
                st.markdown("---")
                render_pagination_controls("pendentes_page", total_pages)
    
    with tab3:
        st.markdown("### Últimas 5 OSs Finalizadas")
        df_finalizadas = buscar_os_recentes_finalizadas(conn, display_name, limite=5)
        
        if df_finalizadas.empty:
            st.info("ℹ️ Nenhuma ordem de serviço finalizada recentemente.")
        else:
            st.success(f"✅ {len(df_finalizadas)} OSs finalizadas recentemente.")
            for _, row in df_finalizadas.iterrows():
                col1, col2, col3, col4 = st.columns([1, 2, 2, 2])
                with col1:
                    st.markdown(f"**{row.get('numero')}**")
                with col2:
                    st.markdown(f"**{row.get('secretaria', 'N/A')}**")
                    st.caption(row.get('tipo'))
                with col3:
                    st.markdown(f"**{row.get('equipamento', 'N/A')}**")
                    st.caption(row.get('categoria', 'N/A'))
                with col4:
                    status = row.get('status')
                    try:
                        data_fin = pd.to_datetime(row.get('data_finalizada'))
                        data_fmt = data_fin.strftime('%d/%m/%Y')
                        st.markdown(f"**{status}**")
                        st.caption(data_fmt)
                    except:
                        st.markdown(f"**{status}**")

if __name__ == "__main__":
    render()