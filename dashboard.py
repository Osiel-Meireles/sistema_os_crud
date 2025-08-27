import streamlit as st
import pandas as pd
from database import get_connection
from sqlalchemy import text
from datetime import datetime
# --- INÍCIO DA ALTERAÇÃO ---
# Importa as listas completas de secretarias e categorias
from config import TECNICOS, SECRETARIAS, CATEGORIAS_INTERNA, CATEGORIAS_EXTERNA
# --- FIM DA ALTERAÇÃO ---

def render():
    st.markdown("<h3 style='text-align: left;'>Dashboard de Indicadores</h3>", unsafe_allow_html=True)

    conn = get_connection()
    current_year = datetime.now().year

    try:
        # Query atualizada para buscar também secretaria e categoria
        query = text(f"""
            SELECT status, tecnico, data, secretaria, categoria FROM os_interna
            UNION ALL
            SELECT status, tecnico, data, secretaria, categoria FROM os_externa
        """)

        df = pd.read_sql(query, conn)
        
        # Converte a coluna de data e filtra pelo ano corrente
        df['data'] = pd.to_datetime(df['data'])
        df_anual = df[df['data'].dt.year == current_year].copy()

        # --- 1. Cálculos dos Indicadores Principais ---
        total_os_ano = len(df_anual)
        os_abertas = len(df_anual[df_anual['status'] == 'EM ABERTO'])
        os_finalizadas = len(df_anual[df_anual['status'].isin(['FINALIZADO', 'AGUARDANDO RETIRADA', 'ENTREGUE AO CLIENTE'])])
        os_aguardando_peca = len(df_anual[df_anual['status'] == 'AGUARDANDO PEÇA(S)'])

        # --- 2. Exibição dos Indicadores ---
        st.markdown(f"##### Indicadores de OS do Ano de {current_year}")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total de OS no Ano", total_os_ano)
        col2.metric("OS em Aberto", os_abertas)
        col3.metric("OS Finalizadas", os_finalizadas)
        col4.metric("Aguardando Peça(s)", os_aguardando_peca)

        st.markdown("---")

        # --- 3. Cálculo e Exibição do Quadro de Técnicos ---
        st.markdown("##### Ordens de Serviço por Técnico (Ano Corrente)")
        
        todos_tecnicos = [tec for tec in TECNICOS if tec != 'Selecione...']
        df_tecnicos = pd.DataFrame(todos_tecnicos, columns=['Técnico'])
        
        if not df_anual.empty:
            contagem_os_tecnicos = df_anual['tecnico'].value_counts().reset_index()
            contagem_os_tecnicos.columns = ['Técnico', 'Quantidade de OS']
            df_final_tecnicos = pd.merge(df_tecnicos, contagem_os_tecnicos, on='Técnico', how='left')
            df_final_tecnicos['Quantidade de OS'] = df_final_tecnicos['Quantidade de OS'].fillna(0).astype(int)
        else:
            df_final_tecnicos = df_tecnicos
            df_final_tecnicos['Quantidade de OS'] = 0
            
        st.dataframe(df_final_tecnicos.sort_values(by='Quantidade de OS', ascending=False), use_container_width=True)

        st.markdown("---")

        # --- INÍCIO DA ALTERAÇÃO ---
        # --- 4. Visualização por Secretaria e Categoria ---
        col_sec, col_cat = st.columns(2)

        with col_sec:
            st.markdown("##### Ordens de Serviço por Secretaria")
            todas_secretarias = [sec for sec in SECRETARIAS if sec != 'Selecione...']
            df_secretarias = pd.DataFrame(todas_secretarias, columns=['Secretaria'])

            if not df_anual.empty:
                contagem_os_secretarias = df_anual['secretaria'].value_counts().reset_index()
                contagem_os_secretarias.columns = ['Secretaria', 'Quantidade de OS']
                df_final_secretarias = pd.merge(df_secretarias, contagem_os_secretarias, on='Secretaria', how='left')
                df_final_secretarias['Quantidade de OS'] = df_final_secretarias['Quantidade de OS'].fillna(0).astype(int)
            else:
                df_final_secretarias = df_secretarias
                df_final_secretarias['Quantidade de OS'] = 0
            
            st.dataframe(df_final_secretarias.sort_values(by='Quantidade de OS', ascending=False), use_container_width=True)

        with col_cat:
            st.markdown("##### Ordens de Serviço por Categoria")
            # Combina as duas listas de categorias, remove duplicatas e o placeholder
            todas_categorias = list(set([cat for cat in CATEGORIAS_INTERNA + CATEGORIAS_EXTERNA if cat != 'Selecione...']))
            df_categorias = pd.DataFrame(todas_categorias, columns=['Categoria'])
            
            if not df_anual.empty:
                contagem_os_categorias = df_anual['categoria'].value_counts().reset_index()
                contagem_os_categorias.columns = ['Categoria', 'Quantidade de OS']
                df_final_categorias = pd.merge(df_categorias, contagem_os_categorias, on='Categoria', how='left')
                df_final_categorias['Quantidade de OS'] = df_final_categorias['Quantidade de OS'].fillna(0).astype(int)
            else:
                df_final_categorias = df_categorias
                df_final_categorias['Quantidade de OS'] = 0

            st.dataframe(df_final_categorias.sort_values(by='Quantidade de OS', ascending=False), use_container_width=True)
        # --- FIM DA ALTERAÇÃO ---

    except Exception as e:
        st.error(f"Ocorreu um erro ao carregar os dados do dashboard: {e}")
    finally:
        conn.dispose()