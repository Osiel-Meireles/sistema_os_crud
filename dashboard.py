import streamlit as st
import pandas as pd
from database import get_connection
from sqlalchemy import text
from datetime import datetime
from config import TECNICOS # Importa a lista de técnicos

def render():
    st.markdown("<h3 style='text-align: left;'>Dashboard de Indicadores</h3>", unsafe_allow_html=True)

    conn = get_connection()
    current_year = datetime.now().year

    try:
        # Query para unir as duas tabelas e buscar os dados de uma só vez
        query = text(f"""
            SELECT status, tecnico, data FROM os_interna
            UNION ALL
            SELECT status, tecnico, data FROM os_externa
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
            contagem_os = df_anual['tecnico'].value_counts().reset_index()
            contagem_os.columns = ['Técnico', 'Quantidade de OS']
            
            df_final_tecnicos = pd.merge(df_tecnicos, contagem_os, on='Técnico', how='left')
            
            df_final_tecnicos['Quantidade de OS'] = df_final_tecnicos['Quantidade de OS'].fillna(0).astype(int)
        else:
            df_final_tecnicos = df_tecnicos
            df_final_tecnicos['Quantidade de OS'] = 0
            
        st.dataframe(df_final_tecnicos.sort_values(by='Quantidade de OS', ascending=False), use_container_width=True)

    except Exception as e:
        st.error(f"Ocorreu um erro ao carregar os dados do dashboard: {e}")
    finally:
        conn.dispose()