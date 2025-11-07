# CÓDIGO ATUALIZADO PARA: sistema_os_crud-main/dashboard.py

import streamlit as st
import pandas as pd
from database import get_connection
from sqlalchemy import text
from datetime import datetime, date
import pytz # Para lidar com fusos horários
from config import TECNICOS, SECRETARIAS, CATEGORIAS

def render():
    st.markdown("<h3 style='text-align: left;'>Dashboard de Indicadores</h3>", unsafe_allow_html=True)

    conn = get_connection()
    fuso_sp = pytz.timezone('America/Sao_Paulo')

    try:
        # --- 1. QUERY ATUALIZADA ---
        # Buscamos também 'data_finalizada' para calcular o TMA
        query = text(f"""
            SELECT status, tecnico, data, secretaria, categoria, data_finalizada FROM os_interna
            UNION ALL
            SELECT status, tecnico, data, secretaria, categoria, data_finalizada FROM os_externa
        """)

        df_base = pd.read_sql(query, conn)
        
        if df_base.empty:
            st.info("Ainda não há Ordens de Serviço registradas no sistema.")
            st.stop()

        # --- 2. PREPARAÇÃO INICIAL DOS DADOS ---
        # Converte colunas de data/hora, tratando fuso horário e erros
        df_base['data'] = pd.to_datetime(df_base['data'], errors='coerce')
        df_base['data_finalizada'] = pd.to_datetime(df_base['data_finalizada'], utc=True, errors='coerce').dt.tz_convert(fuso_sp).dt.tz_localize(None)

        # --- 3. FILTROS INTERATIVOS ---
        st.markdown("---")
        st.markdown("#### Filtros do Dashboard")
        
        col_f1, col_f2, col_f3 = st.columns(3)
        
        with col_f1:
            # Define o range de datas com base nos dados
            data_min = df_base['data'].min().date() if not df_base['data'].isnull().all() else date.today()
            data_max = df_base['data'].max().date() if not df_base['data'].isnull().all() else date.today()
            
            data_inicio = st.date_input("Data de Início", data_min, format="DD/MM/YYYY")
        
        with col_f2:
            data_fim = st.date_input("Data de Fim", data_max, format="DD/MM/YYYY")
        
        with col_f3:
            # Popula o filtro de técnico com base nos dados reais
            tecnicos_disponiveis = ["Todos"] + sorted(list(df_base['tecnico'].dropna().unique()))
            tecnico_selecionado = st.selectbox("Filtrar por Técnico", tecnicos_disponiveis)

        # Validação de datas
        if data_inicio > data_fim:
            st.error("A Data de Início não pode ser maior que a Data de Fim.")
            st.stop()

        # --- 4. APLICAÇÃO DOS FILTROS ---
        df_filtrado = df_base[
            (df_base['data'] >= pd.to_datetime(data_inicio)) &
            (df_base['data'] <= pd.to_datetime(data_fim) + pd.Timedelta(days=1)) # Garante inclusão do dia todo
        ]
        
        if tecnico_selecionado != "Todos":
            df_filtrado = df_filtrado[df_filtrado['tecnico'] == tecnico_selecionado]

        if df_filtrado.empty:
            st.warning("Nenhum dado encontrado para os filtros selecionados.")
            st.stop()

        # --- 5. CÁLCULO DAS MÉTRICAS PRINCIPAIS ---
        total_os = len(df_filtrado)
        os_abertas = len(df_filtrado[df_filtrado['status'] == 'EM ABERTO'])
        os_finalizadas_count = len(df_filtrado[df_filtrado['status'].isin(['FINALIZADO', 'AGUARDANDO RETIRADA', 'ENTREGUE AO CLIENTE'])])
        os_aguardando_peca = len(df_filtrado[df_filtrado['status'] == 'AGUARDANDO PEÇA(S)'])

        # --- 6. CÁLCULO DO TEMPO MÉDIO DE ATENDIMENTO (TMA) ---
        df_finalizadas_tma = df_filtrado[pd.notna(df_filtrado['data_finalizada'])].copy()
        
        tma_display = "N/A"
        if not df_finalizadas_tma.empty:
            # Calcula o tempo de atendimento em dias (como float)
            df_finalizadas_tma['tempo_atendimento_dias'] = (
                df_finalizadas_tma['data_finalizada'] - df_finalizadas_tma['data']
            ).dt.total_seconds() / (3600 * 24) # Converte segundos para dias
            
            # Filtra valores negativos (caso data de entrada seja errada)
            df_finalizadas_tma = df_finalizadas_tma[df_finalizadas_tma['tempo_atendimento_dias'] >= 0]
            
            tma_dias = df_finalizadas_tma['tempo_atendimento_dias'].mean()
            if pd.notna(tma_dias):
                tma_display = f"{tma_dias:.1f} dias"

        # --- 7. EXIBIÇÃO DAS MÉTRICAS ---
        st.markdown(f"##### Indicadores de OS (Período Selecionado)")
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Total de OS no Período", total_os)
        col2.metric("OS em Aberto", os_abertas)
        col3.metric("OS Finalizadas", os_finalizadas_count)
        col4.metric("Aguardando Peça(s)", os_aguardando_peca)
        col5.metric("Tempo Médio de Atendimento", tma_display)

        st.markdown("---")

        # --- 8. GRÁFICOS VISUAIS (substituindo tabelas) ---
        
        col_graf_1, col_graf_2 = st.columns(2)

        with col_graf_1:
            # GRÁFICO 1: OS por Técnico
            st.markdown("##### Ordens de Serviço por Técnico")
            todos_tecnicos = sorted(TECNICOS)
            df_tecnicos = pd.DataFrame(todos_tecnicos, columns=['Técnico'])
            
            contagem_os_tecnicos = df_filtrado['tecnico'].value_counts().reset_index()
            contagem_os_tecnicos.columns = ['Técnico', 'Quantidade de OS']
            
            df_final_tecnicos = pd.merge(df_tecnicos, contagem_os_tecnicos, on='Técnico', how='left')
            df_final_tecnicos['Quantidade de OS'] = df_final_tecnicos['Quantidade de OS'].fillna(0).astype(int)
            
            # Remove técnicos com 0 OS para um gráfico mais limpo
            df_final_tecnicos = df_final_tecnicos[df_final_tecnicos['Quantidade de OS'] > 0]
            
            if df_final_tecnicos.empty:
                st.info("Nenhuma OS para técnicos no período.")
            else:
                # Prepara para st.bar_chart (index como label)
                df_chart_tecnicos = df_final_tecnicos.sort_values(by='Quantidade de OS', ascending=False).set_index('Técnico')
                st.bar_chart(df_chart_tecnicos['Quantidade de OS'])

            # GRÁFICO 2: TMA por Técnico (NOVO!)
            st.markdown("##### Tempo Médio de Atendimento por Técnico (em dias)")
            if df_finalizadas_tma.empty:
                st.info("Nenhuma OS finalizada para calcular o TMA por técnico.")
            else:
                tma_por_tecnico = df_finalizadas_tma.groupby('tecnico')['tempo_atendimento_dias'].mean().sort_values()
                st.bar_chart(tma_por_tecnico)

        with col_graf_2:
            # GRÁFICO 3: OS por Secretaria
            st.markdown("##### Ordens de Serviço por Secretaria")
            todas_secretarias = sorted(SECRETARIAS)
            df_secretarias = pd.DataFrame(todas_secretarias, columns=['Secretaria'])

            contagem_os_secretarias = df_filtrado['secretaria'].value_counts().reset_index()
            contagem_os_secretarias.columns = ['Secretaria', 'Quantidade de OS']
            
            df_final_secretarias = pd.merge(df_secretarias, contagem_os_secretarias, on='Secretaria', how='left')
            df_final_secretarias['Quantidade de OS'] = df_final_secretarias['Quantidade de OS'].fillna(0).astype(int)
            
            df_final_secretarias = df_final_secretarias[df_final_secretarias['Quantidade de OS'] > 0]
            
            if df_final_secretarias.empty:
                st.info("Nenhuma OS para secretarias no período.")
            else:
                df_chart_secretarias = df_final_secretarias.sort_values(by='Quantidade de OS', ascending=False).set_index('Secretaria')
                st.bar_chart(df_chart_secretarias['Quantidade de OS'])

            # GRÁFICO 4: OS por Categoria
            st.markdown("##### Ordens de Serviço por Categoria")
            todas_categorias = sorted(CATEGORIAS)
            df_categorias = pd.DataFrame(todas_categorias, columns=['Categoria'])
            
            contagem_os_categorias = df_filtrado['categoria'].value_counts().reset_index()
            contagem_os_categorias.columns = ['Categoria', 'Quantidade de OS']
            
            df_final_categorias = pd.merge(df_categorias, contagem_os_categorias, on='Categoria', how='left')
            df_final_categorias['Quantidade de OS'] = df_final_categorias['Quantidade de OS'].fillna(0).astype(int)
            
            df_final_categorias = df_final_categorias[df_final_categorias['Quantidade de OS'] > 0]
            
            if df_final_categorias.empty:
                st.info("Nenhuma OS para categorias no período.")
            else:
                df_chart_categorias = df_final_categorias.sort_values(by='Quantidade de OS', ascending=False).set_index('Categoria')
                st.bar_chart(df_chart_categorias['Quantidade de OS'])

    except Exception as e:
        st.error(f"Ocorreu um erro ao carregar os dados do dashboard: {e}")
    finally:
        if 'conn' in locals():
            conn.dispose()