# CÓDIGO ATUALIZADO E COMPLETO PARA: sistema_os_crud-main/minhas_tarefas.py

import streamlit as st
import pandas as pd
from sqlalchemy import text
from database import get_connection
from datetime import datetime
import pytz 

def render():
    display_name = st.session_state.get('display_name')
    if not display_name:
        st.error("Sessão inválida. Por favor, faça login novamente.")
        st.session_state.logged_in = False
        st.rerun()
        return

    st.markdown(f"<h3 style='text-align: left;'>Painel de Tarefas: {display_name}</h3>", unsafe_allow_html=True)
    st.write("Acompanhe suas ordens de serviço e laudos pendentes.")

    conn = get_connection()
    df_os_abertas = pd.DataFrame()
    df_laudos_pendentes = pd.DataFrame()
    df_os_finalizadas = pd.DataFrame()

    try:
        # --- ALTERAÇÃO AQUI: Query 1 (Abertas) ---
        # Adicionamos setor e equipamento à consulta
        query_os = text("""
            SELECT numero, 'Interna' as tipo, data, hora, secretaria, setor, equipamento, solicitante, solicitacao_cliente
            FROM os_interna
            WHERE UPPER(tecnico) = UPPER(:display_name) AND status = 'EM ABERTO'
            UNION ALL
            SELECT numero, 'Externa' as tipo, data, hora, secretaria, setor, equipamento, solicitante, solicitacao_cliente
            FROM os_externa
            WHERE UPPER(tecnico) = UPPER(:display_name) AND status = 'EM ABERTO'
            ORDER BY data ASC, hora ASC
        """)
        df_os_abertas = pd.read_sql(query_os, conn, params={"display_name": display_name})
        # --- FIM DA ALTERAÇÃO ---

        # Query 2: Buscar laudos pendentes (Inalterada)
        query_laudos = text("""
            SELECT id, numero_os, tipo_os, componente, status, data_registro
            FROM laudos
            WHERE UPPER(tecnico) = UPPER(:display_name) AND status = 'PENDENTE'
            ORDER BY data_registro ASC
        """)
        df_laudos_pendentes = pd.read_sql(query_laudos, conn, params={"display_name": display_name})

        # Query 3: Buscar OS Finalizadas (Inalterada)
        query_finalizadas = text("""
            SELECT numero, 'Interna' as tipo, data, data_finalizada, secretaria, setor, equipamento, status, servico_executado
            FROM os_interna
            WHERE UPPER(tecnico) = UPPER(:display_name) AND status IN ('FINALIZADO', 'AGUARDANDO RETIRADA', 'ENTREGUE AO CLIENTE')
            UNION ALL
            SELECT numero, 'Externa' as tipo, data, data_finalizada, secretaria, setor, equipamento, status, servico_executado
            FROM os_externa
            WHERE UPPER(tecnico) = UPPER(:display_name) AND status IN ('FINALIZADO', 'AGUARDANDO RETIRADA', 'ENTREGUE AO CLIENTE')
            ORDER BY data_finalizada DESC
            LIMIT 10
        """)
        df_os_finalizadas = pd.read_sql(query_finalizadas, conn, params={"display_name": display_name})

    except Exception as e:
        st.error(f"Erro ao buscar tarefas: {e}")
    finally:
        conn.dispose()

    # --- MÉTRICAS ---
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    col1.metric("Minhas OS em Aberto", len(df_os_abertas))
    col2.metric("Meus Laudos Pendentes", len(df_laudos_pendentes))
    col3.metric("Total OS Finalizadas (Histórico)", len(df_os_finalizadas))
    st.markdown("---")

    # --- ABAS DE TAREFAS ---
    tab1, tab2, tab3 = st.tabs([
        "Minhas Ordens de Serviço (Abertas)", 
        "Meus Laudos Pendentes",
        "Minhas Últimas OS Finalizadas"
    ])

    with tab1:
        if df_os_abertas.empty:
            st.success("Você não possui nenhuma Ordem de Serviço em aberto no momento.")
        else:
            st.markdown(f"Você tem **{len(df_os_abertas)}** OS em aberto. As mais antigas estão no topo.")
            
            for _, os in df_os_abertas.iterrows():
                data_formatada = pd.to_datetime(os['data']).strftime('%d/%m/%Y')
                
                with st.container(border=True):
                    # --- ALTERAÇÃO AQUI: Layout do Card Atualizado ---
                    st.markdown(f"##### **OS {os['numero']} ({os['tipo']})** | Aberta em: {data_formatada}")
                    st.markdown(f"**Local:** {os.get('secretaria', 'N/A')} / {os.get('setor', 'N/A')}")
                    st.markdown(f"**Equipamento:** {os.get('equipamento', 'N/A')}")
                    st.markdown(f"**Solicitante:** {os.get('solicitante', 'N/A')}")
                    # --- FIM DA ALTERAÇÃO ---

                    with st.expander("Ver Solicitação do Cliente"):
                        st.text_area(
                            "Solicitação",
                            value=os['solicitacao_cliente'],
                            disabled=True,
                            height=100,
                            key=f"desc_{os['numero']}"
                        )
                    
                    st.markdown(" ") 
                    
                    btn_col1, btn_col2 = st.columns(2)
                    
                    if btn_col1.button("Atualizar/Finalizar OS", key=f"upd_{os['numero']}", use_container_width=True):
                        st.session_state.page = "Dar Baixa em OS" 
                        st.session_state.numero_os_preenchido = os['numero']
                        st.toast(f"Carregando OS {os['numero']}...") 
                        st.rerun()
                        
                    if btn_col2.button("Registrar Laudo para esta OS", key=f"laudo_{os['numero']}", use_container_width=True):
                        st.session_state.page = "Laudos"
                        st.session_state.laudo_os_preenchido = {
                            'numero': os['numero'],
                            'tipo': os['tipo'], 
                            'tipo_os_completo': f"OS {os['tipo']}" 
                        }
                        st.toast(f"Carregando OS {os['numero']} para registrar laudo...") 
                        st.rerun()
                
                st.markdown(" ") 

    with tab2:
        if df_laudos_pendentes.empty:
            st.success("Você não possui laudos com status 'PENDENTE'.")
        else:
            st.markdown("Estes são os laudos que você registrou e que ainda estão pendentes de análise/aprovação.")
            df_laudos_pendentes['data_registro'] = pd.to_datetime(df_laudos_pendentes['data_registro']).dt.strftime('%d/%m/%Y %H:%M')
            st.dataframe(
                df_laudos_pendentes[['numero_os', 'tipo_os', 'componente', 'status', 'data_registro']],
                use_container_width=True
            )

    with tab3:
        if df_os_finalizadas.empty:
            st.info("Nenhuma OS finalizada por você foi encontrada no histórico recente.")
        else:
            st.markdown("As 10 últimas ordens de serviço que você finalizou:")
            fuso_sp = pytz.timezone('America/Sao_Paulo')

            for _, os in df_os_finalizadas.iterrows():
                data_fim_formatada = "N/A"
                if pd.notna(os['data_finalizada']):
                    data_fim_formatada = pd.to_datetime(os['data_finalizada']).astimezone(fuso_sp).strftime('%d/%m/%Y %H:%M')

                with st.container(border=True):
                    st.markdown(f"**OS {os['numero']} ({os['tipo']})** | **Status:** {os['status']}")
                    st.markdown(f"**Local:** {os.get('secretaria', 'N/A')} / {os.get('setor', 'N/A')}")
                    st.markdown(f"**Equipamento:** {os.get('equipamento', 'N/A')}")
                    st.markdown(f"**Finalizada em:** {data_fim_formatada}")
                    
                    with st.expander("Ver Serviço Executado"):
                        st.text_area(
                            "Serviço",
                            value=os.get('servico_executado', 'Nenhum serviço registrado.'),
                            disabled=True,
                            height=100,
                            key=f"serv_{os['numero']}"
                        )
                st.markdown(" ")