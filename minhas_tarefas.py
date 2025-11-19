# CÓDIGO COMPLETO E CORRIGIDO PARA: sistema_os_crud-main/minhas_tarefas.py
import streamlit as st
import pandas as pd
from sqlalchemy import text
from database import get_connection
from datetime import datetime
import pytz

def render():
    display_name = st.session_state.get('display_name')
    username = st.session_state.get('username')
    
    if not display_name:
        st.error("Sessão inválida. Por favor, faça login novamente.")
        st.session_state.logged_in = False
        st.rerun()
        return

    conn = get_connection()

    st.title(f"Minhas Tarefas - {display_name}")
    st.markdown("---")

    # Obtenha dados das OS do técnico
    try:
        query = text("""
            SELECT 
                id, numero, 'Interna' as tipo, status, secretaria, setor, solicitante, 
                telefone, data, hora, equipamento, patrimonio, categoria, 
                solicitacao_cliente, servico_executado, data_finalizada
            FROM os_interna
            WHERE tecnico = :tech_name OR tecnico = :username
            UNION
            SELECT 
                id, numero, 'Externa' as tipo, status, secretaria, setor, solicitante, 
                telefone, data, hora, equipamento, patrimonio, categoria, 
                solicitacao_cliente, servico_executado, data_finalizada
            FROM os_externa
            WHERE tecnico = :tech_name OR tecnico = :username
            ORDER BY data DESC, hora DESC
        """)
        
        with conn.connect() as con:
            result = con.execute(query, {"tech_name": display_name, "username": username})
            rows = result.fetchall()
            columns = result.keys()
            df = pd.DataFrame(rows, columns=columns)
        
        if df.empty:
            st.warning("Nenhuma OS encontrada.")
            with st.expander("Debug - Informações do Técnico"):
                st.write(f"**Display Name:** {display_name}")
                st.write(f"**Username:** {username}")
            return
    except Exception as e:
        st.error(f"Erro ao buscar OS: {e}")
        st.exception(e)
        return

    # Exibição das estatísticas
    st.markdown("### Resumo de Minhas Tarefas")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total de OS", len(df))
    
    with col2:
        abertas = len(df[df['status'].isin(['EM ABERTO'])])
        st.metric("Em Aberto", abertas)
    
    with col3:
        aguardando_pecas = len(df[df['status'] == 'AGUARDANDO PEÇA(S)'])
        st.metric("Aguardando Peças", aguardando_pecas)
    
    with col4:
        finalizadas = len(df[df['status'].isin(['FINALIZADO', 'AGUARDANDO RETIRADA'])])
        st.metric("Finalizadas", finalizadas)

    st.markdown("---")

    # SEPARAR OS EM CATEGORIAS
    df_aberto = df[df['status'].isin(['EM ABERTO', 'AGUARDANDO PEÇA(S)'])]
    df_finalizado = df[df['status'].isin(['FINALIZADO', 'AGUARDANDO RETIRADA', 'ENTREGUE AO CLIENTE'])]
    
    # Obter laudos pendentes
    try:
        query_laudos = text("""
            SELECT id, numero_os, tipo_os, diagnostico, estado_conservacao, tecnico
            FROM laudos
            WHERE status = 'PENDENTE' AND tecnico = :tecnico
            ORDER BY id DESC
        """)
        with conn.connect() as con:
            result_laudos = con.execute(query_laudos, {"tecnico": display_name}).fetchall()
            if result_laudos:
                df_laudos_pendentes = pd.DataFrame(result_laudos, columns=result_laudos[0]._mapping.keys())
            else:
                df_laudos_pendentes = pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao buscar laudos pendentes: {e}")
        df_laudos_pendentes = pd.DataFrame()
    
    # CRIAR ABAS
    tab1, tab2, tab3 = st.tabs(["📋 OS Em Aberto", "📝 Laudos Pendentes", "✅ Últimas 5 Finalizadas"])
    
    # ================= ABA 1: OS EM ABERTO =================
    with tab1:
        st.markdown("### Ordens de Serviço Em Aberto")
        
        if len(df_aberto) == 0:
            st.warning("✅ Você não possui nenhuma OS em aberto! Ótimo trabalho!")
            st.info("📊 Todas as suas OS foram finalizadas ou estão aguardando peça(s).")
        else:
            st.info(f"📌 Você tem **{len(df_aberto)}** OS em aberto para trabalhar.")
            
            # Separar por status
            df_em_aberto = df[df['status'] == 'EM ABERTO']
            df_aguardando_pecas = df[df['status'] == 'AGUARDANDO PEÇA(S)']
            
            if len(df_em_aberto) > 0:
                st.markdown("#### 🔴 Em Aberto para Trabalho")
                for idx, row in df_em_aberto.iterrows():
                    display_expandable_card(row, idx, display_name)
            
            if len(df_aguardando_pecas) > 0:
                st.markdown("#### 🟠 Aguardando Peça(s)")
                st.info("Essas OS estão aguardando peças. Você pode continuar o trabalho quando as peças chegarem.")
                for idx, row in df_aguardando_pecas.iterrows():
                    display_expandable_card(row, idx, display_name)
    
    # ================= ABA 2: LAUDOS PENDENTES =================
    with tab2:
        st.markdown("### Laudos Técnicos Pendentes")
        
        if df_laudos_pendentes.empty:
            st.success("✅ Você não possui laudos pendentes!")
            st.info("📊 Todos os seus laudos foram processados.")
        else:
            st.warning(f"⚠️ Você tem **{len(df_laudos_pendentes)}** laudo(s) pendente(s).")
            st.markdown("---")
            
            # Exibir laudos como cards
            for idx, row in df_laudos_pendentes.iterrows():
                with st.container(border=True):
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        st.markdown(f"**OS:** {row['numero_os']} ({row['tipo_os']})")
                        st.markdown(f"**Estado de Conservação:** {row['estado_conservacao']}")
                    
                    with col2:
                        st.markdown(f"**ID Laudo:** {row['id']}")
                    
                    with col3:
                        if st.button("Visualizar", key=f"view_laudo_{row['id']}"):
                            st.session_state.view_laudo_id = row["id"]
                            st.session_state.current_page = "Laudos"
                            st.rerun()
                    
                    # Diagnóstico resumido
                    diagnostico_resumido = str(row['diagnostico'])[:100]
                    if len(str(row['diagnostico'])) > 100:
                        diagnostico_resumido += "..."
                    st.text(f"📋 {diagnostico_resumido}")
    
    # ================= ABA 3: ÚLTIMAS 5 FINALIZADAS =================
    with tab3:
        st.markdown("### Últimas 5 Ordens de Serviço Finalizadas")
        
        # Pegar as últimas 5 OS finalizadas
        df_finalizadas_ultimas = df_finalizado.head(5)
        
        if len(df_finalizadas_ultimas) == 0:
            st.info("📊 Você ainda não finalizou nenhuma OS.")
        else:
            st.success(f"🎉 Você finalizou **{len(df_finalizado)}** OS no total!")
            st.markdown("---")
            
            for idx, row in df_finalizadas_ultimas.iterrows():
                with st.container(border=True):
                    # Status com cor
                    status_icons = {
                        'EM ABERTO': '🔴',
                        'AGUARDANDO PEÇA(S)': '🟠',
                        'FINALIZADO': '🟢',
                        'AGUARDANDO RETIRADA': '🟡',
                        'ENTREGUE AO CLIENTE': '🔵'
                    }
                    status_icon = status_icons.get(row['status'], '⚪')
                    
                    # Formatar data
                    data_formatada = "N/A"
                    if pd.notna(row["data"]):
                        try:
                            data_formatada = pd.to_datetime(row["data"]).strftime("%d/%m/%Y")
                        except:
                            data_formatada = str(row["data"])
                    
                    data_finalizacao = "N/A"
                    if pd.notna(row["data_finalizada"]):
                        try:
                            data_finalizacao = pd.to_datetime(row["data_finalizada"]).strftime("%d/%m/%Y")
                        except:
                            data_finalizacao = str(row["data_finalizada"])
                    
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown(f"### {status_icon} OS #{row['numero']}")
                        st.markdown(f"**Tipo:** {row['tipo']} | **Secretaria:** {row['secretaria']}")
                        st.markdown(f"**Solicitante:** {row['solicitante'] if pd.notna(row['solicitante']) else 'N/A'}")
                        st.markdown(f"**Data da OS:** {data_formatada}")
                        st.markdown(f"**Data de Finalização:** {data_finalizacao}")
                        st.markdown(f"**Status:** {row['status']}")
                    
                    with col2:
                        st.markdown(f"**Equipamento:**\n{row['equipamento'] if pd.notna(row['equipamento']) else 'N/A'}")
                        st.markdown(f"\n**Patrimônio:**\n{row['patrimonio'] if pd.notna(row['patrimonio']) else 'N/A'}")
                    
                    # Descrição do serviço se houver
                    if pd.notna(row['servico_executado']) and str(row['servico_executado']).strip() != '':
                        st.markdown("**Serviço Executado:**")
                        st.text(str(row['servico_executado']))
    
    st.markdown("---")
    st.info("💡 Use as abas para navegar entre suas tarefas em aberto, laudos pendentes e histórico de finalizações.")

def display_expandable_card(row, idx, display_name):
    """Exibe um card expansível com as informações da OS"""
    
    status_icons = {
        'EM ABERTO': '🔴',
        'AGUARDANDO PEÇA(S)': '🟠',
        'FINALIZADO': '🟢',
        'AGUARDANDO RETIRADA': '🟡',
        'ENTREGUE AO CLIENTE': '🔵'
    }
    status_icon = status_icons.get(row['status'], '⚪')
    
    # Formatar data
    data_formatada = ""
    if pd.notna(row["data"]):
        try:
            data_formatada = pd.to_datetime(row["data"]).strftime("%d/%m/%Y")
        except:
            data_formatada = str(row["data"])
    
    titulo_expander = f"{status_icon} **OS #{row['numero']}** | {row['tipo']} | {row['secretaria']} | {data_formatada}"
    
    with st.expander(titulo_expander, expanded=False):
        col_info1, col_info2 = st.columns(2)
        
        with col_info1:
            st.markdown("#### Informações da OS")
            st.markdown(f"**Número:** {row['numero']}")
            st.markdown(f"**Tipo:** {row['tipo']}")
            st.markdown(f"**Status:** {row['status']}")
            st.markdown(f"**Data:** {data_formatada}")
            if pd.notna(row["hora"]):
                st.markdown(f"**Hora:** {row['hora']}")
        
        with col_info2:
            st.markdown("#### Localização")
            st.markdown(f"**Secretaria:** {row['secretaria']}")
            st.markdown(f"**Setor:** {row['setor'] if pd.notna(row['setor']) else 'N/A'}")
        
        st.divider()
        
        col_pessoa1, col_pessoa2 = st.columns(2)
        
        with col_pessoa1:
            st.markdown("#### Solicitante")
            st.markdown(f"**Nome:** {row['solicitante'] if pd.notna(row['solicitante']) else 'N/A'}")
            st.markdown(f"**Telefone:** {row['telefone'] if pd.notna(row['telefone']) else 'N/A'}")
        
        with col_pessoa2:
            st.markdown("#### Equipamento")
            st.markdown(f"**Nome:** {row['equipamento'] if pd.notna(row['equipamento']) else 'N/A'}")
            st.markdown(f"**Patrimônio:** {row['patrimonio'] if pd.notna(row['patrimonio']) else 'N/A'}")
            st.markdown(f"**Categoria:** {row['categoria'] if pd.notna(row['categoria']) else 'N/A'}")
        
        st.divider()
        
        st.markdown("#### Descrições")
        
        if pd.notna(row['solicitacao_cliente']) and str(row['solicitacao_cliente']).strip() != '':
            st.markdown("**Solicitação do Cliente:**")
            st.text_area(
                "solicitacao",
                value=str(row['solicitacao_cliente']),
                height=100,
                disabled=True,
                label_visibility="collapsed"
            )
        
        if pd.notna(row['servico_executado']) and str(row['servico_executado']).strip() != '':
            st.markdown("**Serviço Executado:**")
            st.text_area(
                "servico",
                value=str(row['servico_executado']),
                height=100,
                disabled=True,
                label_visibility="collapsed"
            )
        
        st.divider()
        st.markdown("#### Ações")
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("Finalizar/Dar Baixa", key=f"update_{row['id']}_{idx}"):
                st.session_state.baixa_os_id = row['id']
                st.session_state.baixa_os_tipo = row['tipo']
                st.session_state.baixa_os_numero = row['numero']
                st.session_state.current_page = "Dar Baixa"
                st.rerun()
        
        with col_btn2:
            if st.button("Registrar Laudo", key=f"laudo_{row['id']}_{idx}"):
                st.session_state.laudo_os_id = row['id']
                st.session_state.laudo_os_numero = row['numero']
                st.session_state.laudo_os_tipo = row['tipo']
                st.session_state.laudo_tecnico = display_name
                st.session_state.current_page = "Registrar Laudo"
                st.rerun()