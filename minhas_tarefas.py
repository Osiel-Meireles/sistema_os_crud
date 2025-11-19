# CÓDIGO COMPLETO E CORRIGIDO PARA: sistema_os_crud-main/minhas_tarefas.py

import streamlit as st
import pandas as pd
from sqlalchemy import text
from database import get_connection
from config import STATUS_OPTIONS, CATEGORIAS, EQUIPAMENTOS
from datetime import datetime
import pytz

def f_atualizar_os_tecnico(conn, os_id, os_tipo, dados_atualizacao):
    """Atualiza uma OS específica (apenas campos permitidos para técnicos)."""
    table_name = "os_interna" if os_tipo == "Interna" else "os_externa"
    
    try:
        with conn.connect() as con:
            with con.begin():
                set_clause = []
                params = {"id": os_id}
                
                for key, value in dados_atualizacao.items():
                    if key != "id":
                        set_clause.append(f"{key} = :{key}")
                        params[key] = value
                
                if not set_clause:
                    st.error("Nenhum dado para atualizar.")
                    return False
                
                query = text(f"UPDATE {table_name} SET {', '.join(set_clause)} WHERE id = :id")
                con.execute(query, params)
                st.success(f"Ordem de Serviço atualizada com sucesso!")
                return True
    except Exception as e:
        st.error(f"Erro ao atualizar OS: {e}")
        return False

def buscar_tarefas_tecnico(conn, display_name):
    """Busca todas as OSs atribuídas ao técnico logado."""
    try:
        # Query para buscar OSs de ambas as tabelas
        query = text("""
            SELECT *, 'Interna' as tipo FROM os_interna 
            WHERE tecnico = :tecnico AND status != 'ENTREGUE AO CLIENTE'
            UNION ALL
            SELECT *, 'Externa' as tipo FROM os_externa 
            WHERE tecnico = :tecnico AND status != 'ENTREGUE AO CLIENTE'
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
                tipo_os_laudo = f"OS {row['tipo']}"
                query_laudo = text("""
                    SELECT COUNT(*) as total FROM laudos 
                    WHERE numero_os = :numero AND tipo_os = :tipo
                """)
                result_laudo = con.execute(query_laudo, {
                    "numero": row['numero'],
                    "tipo": tipo_os_laudo
                }).fetchone()
                
                if result_laudo[0] == 0:  # Não tem laudo
                    os_sem_laudo.append(row)
            
            return pd.DataFrame(os_sem_laudo) if os_sem_laudo else pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao buscar OS pendentes de laudo: {e}")
        return pd.DataFrame()

def buscar_os_recentes_finalizadas(conn, display_name, limite=5):
    """Busca as últimas OSs finalizadas do técnico."""
    try:
        query = text("""
            SELECT *, 'Interna' as tipo FROM os_interna 
            WHERE tecnico = :tecnico AND status = 'FINALIZADO'
            UNION ALL
            SELECT *, 'Externa' as tipo FROM os_externa 
            WHERE tecnico = :tecnico AND status = 'FINALIZADO'
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
    elif status == "FINALIZADO":
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
            key=f"solicitacao_{card_key}"  # ✅ KEY ÚNICA
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
            key=f"servico_{card_key}"  # ✅ KEY ÚNICA
        )
        
        st.markdown("---")
        
        # Botões de ação
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button(
                "Atualizar/Finalizar OS",
                use_container_width=True,
                key=f"btn_atualizar_{card_key}",  # ✅ KEY ÚNICA
                type="primary"
            ):
                st.session_state.os_para_atualizar = row.to_dict()
                st.session_state.os_para_atualizar_idx = idx
                st.rerun()
        
        with col2:
            if st.button(
                "Registrar Laudo para esta OS",
                use_container_width=True,
                key=f"btn_laudo_{card_key}"  # ✅ KEY ÚNICA
            ):
                # Preparar dados para página de laudos
                st.session_state.laudo_os_id = row.get('id')
                st.session_state.laudo_os_numero = row.get('numero')
                st.session_state.laudo_os_tipo = row.get('tipo')
                st.session_state.laudo_tecnico = display_name
                st.session_state.current_page = "Laudos"
                st.rerun()

def render_modal_atualizar_os(conn, display_name):
    """Renderiza modal para atualizar/finalizar OS."""
    if 'os_para_atualizar' not in st.session_state or st.session_state.os_para_atualizar is None:
        return
    
    os_data = st.session_state.os_para_atualizar
    
    @st.dialog("Atualizar/Finalizar Ordem de Serviço", width="large")
    def show_modal():
        st.markdown(f"### Atualizando OS #{os_data.get('numero', 'N/A')}")
        st.markdown(f"**Tipo:** {os_data.get('tipo')} | **Status Atual:** {os_data.get('status', 'N/A')}")
        st.markdown("---")
        
        with st.form("form_atualizar_os_tecnico"):
            # Status
            status_atual = os_data.get('status', 'EM ABERTO')
            if status_atual == "EM ABERTO":
                opcoes_status = ["EM ABERTO", "AGUARDANDO PEÇA(S)"]
            elif status_atual == "AGUARDANDO PEÇA(S)":
                opcoes_status = ["AGUARDANDO PEÇA(S)", "AGUARDANDO RETIRADA"]
            else:
                opcoes_status = [status_atual]
            
            status = st.selectbox(
                "Status *",
                opcoes_status,
                index=0
            )
            
            st.info("ℹ️ Técnicos podem alterar status de 'EM ABERTO' para 'AGUARDANDO PEÇA(S)' ou finalizar para 'AGUARDANDO RETIRADA'.")
            
            # Serviço Executado
            st.markdown("#### Descrição do Serviço")
            servico_executado = st.text_area(
                "Serviço Executado *",
                value=os_data.get('servico_executado', ''),
                height=150,
                placeholder="Descreva o serviço realizado...",
                key="text_servico_executado"
            )
            
            st.markdown("---")
            
            col1, col2 = st.columns(2)
            
            submitted = col1.form_submit_button(
                "Salvar Alterações",
                use_container_width=True,
                type="primary"
            )
            
            cancelar = col2.form_submit_button(
                "Cancelar",
                use_container_width=True
            )
            
            if submitted:
                if not servico_executado:
                    st.error("O campo 'Serviço Executado' é obrigatório.")
                else:
                    # Preparar dados para atualização
                    dados_atualizacao = {
                        "status": status,
                        "servico_executado": servico_executado
                    }
                    
                    # Se estiver finalizando, adicionar data de finalização
                    if status == "AGUARDANDO RETIRADA":
                        dados_atualizacao["status"] = "AGUARDANDO RETIRADA"
                        dados_atualizacao["data_finalizada"] = datetime.now(pytz.timezone('America/Sao_Paulo'))
                    
                    if f_atualizar_os_tecnico(
                        conn,
                        os_data.get('id'),
                        os_data.get('tipo'),
                        dados_atualizacao
                    ):
                        del st.session_state.os_para_atualizar
                        if 'os_para_atualizar_idx' in st.session_state:
                            del st.session_state.os_para_atualizar_idx
                        st.rerun()
            
            if cancelar:
                del st.session_state.os_para_atualizar
                if 'os_para_atualizar_idx' in st.session_state:
                    del st.session_state.os_para_atualizar_idx
                st.rerun()
    
    show_modal()

def render():
    """Função principal de renderização da página Minhas Tarefas."""
    st.markdown("## Minhas Tarefas")
    
    conn = get_connection()
    display_name = st.session_state.get("display_name", st.session_state.get("username", ""))
    
    # Renderizar modal de atualização se necessário
    render_modal_atualizar_os(conn, display_name)
    
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
    
    # Criar abas
    tab1, tab2, tab3 = st.tabs([
        "📋 OSs em Aberto",
        "📝 Pendentes de Laudo",
        "✅ Últimas Finalizadas"
    ])
    
    # ABA 1: OSs em Aberto
    with tab1:
        st.markdown("### Ordens de Serviço em Aberto")
        
        # Buscar OSs abertas e aguardando peças
        df_abertas = buscar_tarefas_tecnico(conn, display_name)
        
        if df_abertas.empty:
            st.success("🎉 Parabéns! Você não tem ordens de serviço em aberto no momento.")
            st.info("Todas as suas tarefas foram concluídas ou estão aguardando retirada.")
        else:
            st.info(f"Você tem **{len(df_abertas)}** ordem(ns) de serviço ativa(s).")
            
            # Exibir cards
            for idx, row in df_abertas.iterrows():
                display_expandable_card(row, idx, display_name)
    
    # ABA 2: Pendentes de Laudo
    with tab2:
        st.markdown("### OSs Aguardando Laudo de Avaliação")
        
        df_pendentes = buscar_os_pendentes_laudo(conn, display_name)
        
        if df_pendentes.empty:
            st.success("✅ Não há ordens de serviço pendentes de laudo.")
        else:
            st.warning(f"**{len(df_pendentes)}** OS(s) aguardando laudo de avaliação.")
            
            # Exibir em formato de tabela simplificado
            for idx, row in df_pendentes.iterrows():
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
    
    # ABA 3: Últimas Finalizadas
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
                        try:
                            data_fin = pd.to_datetime(row.get('data_finalizada'))
                            data_fmt = data_fin.strftime('%d/%m/%Y')
                            st.markdown(f"🟢 Finalizado")
                            st.caption(data_fmt)
                        except:
                            st.markdown("🟢 Finalizado")
                    
                    st.markdown("---")