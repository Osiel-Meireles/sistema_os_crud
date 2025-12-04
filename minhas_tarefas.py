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
        # Query atualizada: Exclui 'AGUARDANDO RETIRADA', 'FINALIZADO' e 'ENTREGUE AO CLIENTE'
        # Assim, mostra apenas o que requer ação real do técnico (EM ABERTO, AGUARDANDO PEÇAS)
        query = text("""
            SELECT *, 'Interna' as tipo FROM os_interna 
            WHERE tecnico = :tecnico 
            AND status NOT IN ('ENTREGUE AO CLIENTE', 'AGUARDANDO RETIRADA', 'FINALIZADO')
            UNION ALL
            SELECT *, 'Externa' as tipo FROM os_externa 
            WHERE tecnico = :tecnico 
            AND status NOT IN ('ENTREGUE AO CLIENTE', 'AGUARDANDO RETIRADA', 'FINALIZADO')
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
                SELECT id FROM os_interna 
                WHERE tecnico = :tecnico AND status = 'EM ABERTO'
                UNION ALL
                SELECT id FROM os_externa 
                WHERE tecnico = :tecnico AND status = 'EM ABERTO'
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
                SELECT id FROM os_interna 
                WHERE tecnico = :tecnico AND status = 'AGUARDANDO PEÇA(S)'
                UNION ALL
                SELECT id FROM os_externa 
                WHERE tecnico = :tecnico AND status = 'AGUARDANDO PEÇA(S)'
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
        # Primeiro buscar todas as OSs AGUARDANDO PEÇA(S) do técnico
        query_os = text("""
            SELECT id, numero, 'Interna' as tipo, secretaria, equipamento, status, data
            FROM os_interna 
            WHERE tecnico = :tecnico AND status = 'AGUARDANDO PEÇA(S)'
            UNION ALL
            SELECT id, numero, 'Externa' as tipo, secretaria, equipamento, status, data
            FROM os_externa 
            WHERE tecnico = :tecnico AND status = 'AGUARDANDO PEÇA(S)'
            ORDER BY data DESC
        """)
        
        with conn.connect() as con:
            result = con.execute(query_os, {"tecnico": display_name})
            rows = result.fetchall()
            columns = result.keys()
            df_os = pd.DataFrame(rows, columns=columns)
            
            # Para cada OS, verificar se já tem laudo
            os_sem_laudo = []
            for _, row in df_os.iterrows():
                tipo_os_laudo = f"OS {row['tipo']}" # Mantido conforme lógica original do laudo
                # Correção preventiva: Verificar se a lógica de laudos usa "OS Interna" ou "Interna"
                # Assumindo que usa "OS Interna" baseado no código original de laudos.py
                
                query_laudo = text("""
                    SELECT COUNT(*) as total FROM laudos 
                    WHERE numero_os = :numero 
                    AND (tipo_os = :tipo OR tipo_os = :tipo_simples)
                """)
                result_laudo = con.execute(query_laudo, {
                    "numero": row['numero'],
                    "tipo": tipo_os_laudo,
                    "tipo_simples": row['tipo'] # Fallback para compatibilidade
                }).fetchone()
                
                if result_laudo[0] == 0:  # Não tem laudo
                    os_sem_laudo.append(row)
            
            return pd.DataFrame(os_sem_laudo) if os_sem_laudo else pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao buscar OS pendentes de laudo: {e}")
        return pd.DataFrame()

def buscar_os_recentes_finalizadas(conn, display_name, limite=5):
    """Busca as últimas OSs finalizadas do técnico (Inclui Aguardando Retirada)."""
    try:
        # Query atualizada: Inclui 'FINALIZADO', 'AGUARDANDO RETIRADA' e 'ENTREGUE AO CLIENTE'
        query = text("""
            SELECT *, 'Interna' as tipo FROM os_interna 
            WHERE tecnico = :tecnico 
            AND status IN ('FINALIZADO', 'AGUARDANDO RETIRADA', 'ENTREGUE AO CLIENTE')
            UNION ALL
            SELECT *, 'Externa' as tipo FROM os_externa 
            WHERE tecnico = :tecnico 
            AND status IN ('FINALIZADO', 'AGUARDANDO RETIRADA', 'ENTREGUE AO CLIENTE')
            ORDER BY data_finalizada DESC
            LIMIT :limite
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

def display_expandable_card(row, idx, display_name):
    """Exibe um card expansível com informações da OS."""
    
    # Criar identificador único baseado no índice e ID da OS
    os_id = row.get('id', idx)
    card_key = f"card_{idx}_{os_id}"
    
    # Título do card com status colorido
    status = row.get('status', 'N/A')
    if status == "EM ABERTO":
        status_emoji = "🔴"
    elif status == "AGUARDANDO PEÇA(S)":
        status_emoji = "🟠"
    elif status in ["FINALIZADO", "AGUARDANDO RETIRADA", "ENTREGUE AO CLIENTE"]:
        status_emoji = "🟢"
    else:
        status_emoji = "⚪"
    
    titulo = f"OS #{row.get('numero', 'N/A')} - {row.get('secretaria', 'N/A')} - {status_emoji} {status}"
    
    with st.expander(titulo, expanded=False):
        # Informações básicas em colunas
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"**Número:** {row.get('numero', 'N/A')}")
            st.markdown(f"**Tipo:** {row.get('tipo', 'N/A')}")
            st.markdown(f"**Patrimônio:** {row.get('patrimonio', 'N/A')}")
        
        with col2:
            st.markdown(f"**Secretaria:** {row.get('secretaria', 'N/A')}")
            st.markdown(f"**Setor:** {row.get('setor', 'N/A')}")
            st.markdown(f"**Categoria:** {row.get('categoria', 'N/A')}")
        
        with col3:
            st.markdown(f"**Status:** {status}")
            st.markdown(f"**Equipamento:** {row.get('equipamento', 'N/A')}")
            try:
                data_formatada = pd.to_datetime(row.get('data')).strftime('%d/%m/%Y')
                st.markdown(f"**Data:** {data_formatada}")
            except:
                st.markdown(f"**Data:** {row.get('data', 'N/A')}")
        
        st.markdown("---")
        
        # Solicitação do Cliente
        st.markdown("**Solicitação do Cliente:**")
        st.text_area(
            "Solicitação",
            value=row.get('solicitacao_cliente', '') or '',
            disabled=True,
            height=100,
            label_visibility="collapsed",
            key=f"solicitacao_{card_key}"
        )
        
        # Serviço Executado / Descrição
        st.markdown("**Serviço Executado / Descrição:**")
        texto_servico = f"{row.get('servico_executado', '') or ''}\n{row.get('descricao', '') or ''}".strip()
        st.text_area(
            "Serviço",
            value=texto_servico,
            disabled=True,
            height=100,
            label_visibility="collapsed",
            key=f"servico_{card_key}"
        )
        
        st.markdown("---")
        
        # Botões de ação
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button(
                "Atualizar/Finalizar OS",
                use_container_width=True,
                key=f"btn_atualizar_{card_key}",
                type="primary"
            ):
                # Armazenar dados da OS para busca automática em Dar Baixa
                st.session_state.baixa_os_numero = row.get('numero')
                st.session_state.baixa_os_tipo = row.get('tipo')
                st.session_state.baixa_os_id = row.get('id')
                st.session_state.current_page = "Dar Baixa"
                st.rerun()
        
        with col2:
            if st.button(
                "Registrar Laudo para esta OS",
                use_container_width=True,
                key=f"btn_laudo_{card_key}"
            ):
                # Preparar dados para página de laudos
                st.session_state.laudo_os_id = row.get('id')
                st.session_state.laudo_os_numero = row.get('numero')
                st.session_state.laudo_os_tipo = row.get('tipo')
                st.session_state.laudo_tecnico = display_name
                st.session_state.current_page = "Laudos"
                st.rerun()

def render_pagination_controls(page_var_name, total_pages):
    """Renderiza controles de paginação reutilizáveis."""
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
        st.markdown(f"<div style='text-align: center'>Página {current_page} de {total_pages}</div>", 
                   unsafe_allow_html=True)
    
    with col4:
        if st.button("Próxima ▶️", disabled=(current_page == total_pages), key=f"next_{page_var_name}"):
            st.session_state[page_var_name] += 1
            st.rerun()
    
    with col5:
        if st.button("Última ⏭️", disabled=(current_page == total_pages), key=f"last_{page_var_name}"):
            st.session_state[page_var_name] = total_pages
            st.rerun()

def render():
    """Função principal de renderização da página Minhas Tarefas."""
    st.markdown("## Minhas Tarefas")
    
    conn = get_connection()
    display_name = st.session_state.get("display_name", st.session_state.get("username", ""))
    
    # Buscar estatísticas
    total_abertas = contar_os_abertas(conn, display_name)
    total_aguardando_pecas = contar_os_aguardando_pecas(conn, display_name)
    
    # Dashboard de estatísticas
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("OSs em Aberto", total_abertas, help="Ordens de Serviço aguardando atendimento")
    
    with col2:
        st.metric("Aguardando Peças", total_aguardando_pecas, help="Ordens aguardando chegada de peças")
    
    with col3:
        total_ativas = total_abertas + total_aguardando_pecas
        st.metric("Total Ativo", total_ativas, help="Total de OSs que requerem ação")
    
    st.markdown("---")
    
    # Definir itens por página
    ITEMS_PER_PAGE = 5
    
    # Criar abas
    tab1, tab2, tab3 = st.tabs([
        "📋 OSs em Aberto",
        "📝 Pendentes de Laudo",
        "✅ Últimas Finalizadas"
    ])
    
    # ABA 1: OSs em Aberto (COM PAGINAÇÃO)
    with tab1:
        st.markdown("### Ordens de Serviço em Aberto")
        
        # Buscar OSs abertas e aguardando peças
        df_abertas = buscar_tarefas_tecnico(conn, display_name)
        
        if df_abertas.empty:
            st.success("🎉 Parabéns! Você não tem ordens de serviço em aberto no momento.")
            st.info("Todas as suas tarefas foram concluídas ou estão aguardando retirada.")
        else:
            # Inicializar página se não existir
            if 'tarefas_page' not in st.session_state:
                st.session_state.tarefas_page = 1
            
            # Calcular paginação
            total_items = len(df_abertas)
            total_pages = math.ceil(total_items / ITEMS_PER_PAGE)
            
            # Validar página atual
            if st.session_state.tarefas_page > total_pages:
                st.session_state.tarefas_page = total_pages
            if st.session_state.tarefas_page < 1:
                st.session_state.tarefas_page = 1
            
            # Calcular índices
            start_idx = (st.session_state.tarefas_page - 1) * ITEMS_PER_PAGE
            end_idx = start_idx + ITEMS_PER_PAGE
            df_page = df_abertas.iloc[start_idx:end_idx]
            
            # Mostrar informação de paginação
            st.info(f"Exibindo **{len(df_page)}** de **{total_items}** ordem(ns) (Página {st.session_state.tarefas_page}/{total_pages})")
            
            # Exibir cards da página atual
            for idx_real, (idx, row) in enumerate(df_page.iterrows()):
                display_expandable_card(row, idx, display_name)
            
            # Controles de paginação
            if total_pages > 1:
                st.markdown("---")
                render_pagination_controls('tarefas_page', total_pages)
    
    # ABA 2: Pendentes de Laudo (COM PAGINAÇÃO)
    with tab2:
        st.markdown("### OSs Aguardando Laudo de Avaliação")
        
        df_pendentes = buscar_os_pendentes_laudo(conn, display_name)
        
        if df_pendentes.empty:
            st.success("✅ Não há ordens de serviço pendentes de laudo.")
        else:
            # Inicializar página se não existir
            if 'pendentes_page' not in st.session_state:
                st.session_state.pendentes_page = 1
            
            # Calcular paginação
            total_items = len(df_pendentes)
            total_pages = math.ceil(total_items / ITEMS_PER_PAGE)
            
            # Validar página atual
            if st.session_state.pendentes_page > total_pages:
                st.session_state.pendentes_page = total_pages
            if st.session_state.pendentes_page < 1:
                st.session_state.pendentes_page = 1
            
            # Calcular índices
            start_idx = (st.session_state.pendentes_page - 1) * ITEMS_PER_PAGE
            end_idx = start_idx + ITEMS_PER_PAGE
            df_page = df_pendentes.iloc[start_idx:end_idx]
            
            # Mostrar informação
            st.warning(f"**{total_items}** OS(s) aguardando laudo (Página {st.session_state.pendentes_page}/{total_pages})")
            
            # Exibir em formato de tabela simplificado
            for idx, row in df_page.iterrows():
                card_id = f"pendente_{idx}_{row.get('id')}"
                
                with st.container():
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
                        if st.button(
                            "📝 Laudo",
                            key=f"btn_laudo_pendente_{card_id}",
                            use_container_width=True
                        ):
                            st.session_state.laudo_os_id = row.get('id')
                            st.session_state.laudo_os_numero = row.get('numero')
                            st.session_state.laudo_os_tipo = row.get('tipo')
                            st.session_state.laudo_tecnico = display_name
                            st.session_state.current_page = "Laudos"
                            st.rerun()
                    
                    st.markdown("---")
            
            # Controles de paginação
            if total_pages > 1:
                render_pagination_controls('pendentes_page', total_pages)
    
    # ABA 3: Últimas Finalizadas (SEM PAGINAÇÃO - máximo 5)
    with tab3:
        st.markdown("### Últimas 5 OSs Finalizadas")
        
        df_finalizadas = buscar_os_recentes_finalizadas(conn, display_name, limite=5)
        
        if df_finalizadas.empty:
            st.info("Nenhuma ordem de serviço finalizada recentemente.")
        else:
            st.success(f"**{len(df_finalizadas)}** OS(s) finalizadas recentemente.")
            
            # Exibir em formato de tabela
            for idx, row in df_finalizadas.iterrows():
                with st.container():
                    col1, col2, col3, col4 = st.columns([1, 2, 2, 2])
                    
                    with col1:
                        st.markdown(f"**#{row.get('numero')}**")
                    
                    with col2:
                        st.markdown(f"{row.get('secretaria', 'N/A')}")
                        st.caption(row.get('tipo'))
                    
                    with col3:
                        st.markdown(f"{row.get('equipamento', 'N/A')}")
                        st.caption(row.get('categoria', 'N/A'))
                    
                    with col4:
                        status = row.get('status')
                        try:
                            data_fin = pd.to_datetime(row.get('data_finalizada'))
                            data_fmt = data_fin.strftime('%d/%m/%Y')
                            st.markdown(f"🟢 {status}")
                            st.caption(data_fmt)
                        except:
                            st.markdown(f"🟢 {status}")
                    
                    st.markdown("---")