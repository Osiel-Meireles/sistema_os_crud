# CÓDIGO COMPLETO E ATUALIZADO PARA: sistema_os_crud-main/dashboard.py
import streamlit as st
import pandas as pd
from database import get_connection
from sqlalchemy import text
from datetime import datetime, date
import pytz
from config import TECNICOS, SECRETARIAS, CATEGORIAS


def render():
    st.markdown("<h3 style='text-align: left;'>Dashboard de Indicadores</h3>", unsafe_allow_html=True)

    conn = get_connection()
    fuso_sp = pytz.timezone('America/Sao_Paulo')
    role = st.session_state.get("role", "")
    is_admin_role = role in ["admin", "administrativo"]

    try:
        # --- 1. QUERY ATUALIZADA ---
        # Buscamos também 'data_finalizada' para calcular o TMA
        query = text("""
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

        # --- 3. CÁLCULO DAS MÉTRICAS GERAIS (SEM FILTRO) ---
        total_os = len(df_base)
        os_abertas = len(df_base[df_base['status'] == 'EM ABERTO'])
        os_finalizadas_count = len(df_base[df_base['status'].isin(['FINALIZADO', 'AGUARDANDO RETIRADA', 'ENTREGUE AO CLIENTE'])])
        os_aguardando_peca = len(df_base[df_base['status'] == 'AGUARDANDO PEÇA(S)'])

        # Cálculo do TMA geral
        df_finalizadas_tma_geral = df_base[pd.notna(df_base['data_finalizada'])].copy()
        
        tma_display = "N/A"
        if not df_finalizadas_tma_geral.empty:
            df_finalizadas_tma_geral['tempo_atendimento_dias'] = (
                df_finalizadas_tma_geral['data_finalizada'] - df_finalizadas_tma_geral['data']
            ).dt.total_seconds() / (3600 * 24)
            
            df_finalizadas_tma_geral = df_finalizadas_tma_geral[df_finalizadas_tma_geral['tempo_atendimento_dias'] >= 0]
            
            tma_dias = df_finalizadas_tma_geral['tempo_atendimento_dias'].mean()
            if pd.notna(tma_dias):
                tma_display = f"{tma_dias:.1f} dias"

        # --- 4. EXIBIÇÃO DAS MÉTRICAS GERAIS ---
        st.markdown("---")
        st.markdown("##### Indicadores Gerais de OS")
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Total de OS", total_os)
        col2.metric("OS em Aberto", os_abertas)
        col3.metric("OS Finalizadas", os_finalizadas_count)
        
        # MÉTRICA COM FLAG DE ATENÇÃO
        if os_aguardando_peca > 0:
            col4.metric("⚠️ Aguardando Peça(s)", os_aguardando_peca, 
                       delta="Requer atenção", delta_color="inverse")
        else:
            col4.metric("✅ Aguardando Peça(s)", 0)
        
        col5.metric("Tempo Médio de Atendimento", tma_display)

        # --- 5. VERIFICAÇÃO DE OSs AGUARDANDO PEÇAS (APÓS MÉTRICAS) ---
        if is_admin_role:
            try:
                with conn.connect() as con:
                    total_aguardando_pecas_interna = con.execute(
                        text("SELECT COUNT(*) FROM os_interna WHERE status = 'AGUARDANDO PEÇA(S)'")
                    ).scalar()
                    total_aguardando_pecas_externa = con.execute(
                        text("SELECT COUNT(*) FROM os_externa WHERE status = 'AGUARDANDO PEÇA(S)'")
                    ).scalar()
                    total_aguardando_pecas = total_aguardando_pecas_interna + total_aguardando_pecas_externa
                
                # Botão de alerta para OSs laudadas
                if total_aguardando_pecas > 0:
                    st.markdown("---")
                    st.warning(
                        f"⚠️ **Atenção:** Existem {total_aguardando_pecas} Ordem(ns) de Serviço com laudo técnico aguardando peça(s)."
                    )
                    
                    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
                    with col_btn2:
                        if st.button(
                            f"🔍 Verificar {total_aguardando_pecas} OS(s) Laudada(s)",
                            type="primary",
                            use_container_width=True,
                            help="Exibir todas as Ordens de Serviço que estão aguardando peça(s)"
                        ):
                            st.session_state["mostrar_os_laudadas"] = True
                            st.rerun()
                
                # Modal/Expander para mostrar OSs laudadas
                if st.session_state.get("mostrar_os_laudadas", False):
                    with st.expander("📋 Ordens de Serviço Aguardando Peça(s)", expanded=True):
                        # QUERY ATUALIZADA COM SETOR (DEPARTAMENTO)
                        query_laudadas = text("""
                            SELECT 
                                numero,
                                'Interna' as tipo,
                                secretaria,
                                setor,
                                solicitante,
                                equipamento,
                                tecnico,
                                data,
                                status
                            FROM os_interna
                            WHERE status = 'AGUARDANDO PEÇA(S)'
                            
                            UNION ALL
                            
                            SELECT 
                                numero,
                                'Externa' as tipo,
                                secretaria,
                                setor,
                                solicitante,
                                equipamento,
                                tecnico,
                                data,
                                status
                            FROM os_externa
                            WHERE status = 'AGUARDANDO PEÇA(S)'
                            
                            ORDER BY data DESC
                        """)
                        
                        with conn.connect() as con:
                            result = con.execute(query_laudadas)
                            rows = result.fetchall()
                            columns = result.keys()
                            df_laudadas = pd.DataFrame(rows, columns=columns)
                        
                        if not df_laudadas.empty:
                            st.info(f"📊 Total: {len(df_laudadas)} OS(s) aguardando peça(s)")
                            
                            # Cabeçalho com Departamento e Laudo
                            cols_header = st.columns([0.8, 0.8, 1.2, 1, 1.2, 1, 1, 0.8, 0.6])
                            headers = ["Número", "Tipo", "Secretaria", "Departamento", "Solicitante", "Equipamento", "Técnico", "Data", "Laudo"]
                            
                            for col, header in zip(cols_header, headers):
                                col.markdown(f"**{header}**")
                            
                            st.markdown("---")
                            
                            # Linhas com departamento e botão de laudo
                            for idx, row in df_laudadas.iterrows():
                                cols = st.columns([0.8, 0.8, 1.2, 1, 1.2, 1, 1, 0.8, 0.6])
                                
                                cols[0].markdown(f"**{row['numero']}**")
                                cols[1].write(str(row["tipo"]))
                                cols[2].write(str(row["secretaria"]))
                                cols[3].write(str(row["setor"] if pd.notna(row["setor"]) else "-"))
                                cols[4].write(str(row["solicitante"]))
                                cols[5].write(str(row["equipamento"] if pd.notna(row["equipamento"]) else "-"))
                                cols[6].write(str(row["tecnico"]))
                                
                                try:
                                    data_formatada = pd.to_datetime(row["data"]).strftime("%d/%m/%Y")
                                    cols[7].write(data_formatada)
                                except Exception:
                                    cols[7].write(str(row["data"]))
                                
                                # BOTÃO PARA VER LAUDO
                                btn_key = f"laudo_{row['numero'].replace('-', '_')}_{idx}"
                                if cols[8].button("📄", key=btn_key, help="Ver laudos"):
                                    st.session_state["ver_laudo_numero"] = row["numero"]
                                    st.session_state["ver_laudo_tipo"] = row["tipo"]
                                    st.rerun()
                            
                            st.markdown("---")
                            
                            # Botão para fechar
                            col_fechar1, col_fechar2, col_fechar3 = st.columns([1, 1, 1])
                            with col_fechar2:
                                if st.button("✓ Fechar Lista", use_container_width=True):
                                    st.session_state["mostrar_os_laudadas"] = False
                                    st.rerun()
                        else:
                            st.info("Nenhuma OS aguardando peça(s) no momento.")
            
            except Exception as e:
                st.error(f"Erro ao verificar OSs laudadas: {e}")
                st.exception(e)

        # --- MODAL PARA VISUALIZAR LAUDOS ---
        if "ver_laudo_numero" in st.session_state and st.session_state.get("ver_laudo_numero"):
            numero_os = st.session_state["ver_laudo_numero"]
            tipo_os = st.session_state["ver_laudo_tipo"]
            
            # --- CORREÇÃO AQUI: Removemos o f"OS {}" ---
            tipo_laudo = tipo_os 
            # -------------------------------------------
            
            @st.dialog(f"📋 Laudos da OS {numero_os}", width="large")
            def mostrar_laudos():
                try:
                    query_laudos = text("""
                        SELECT * FROM laudos 
                        WHERE numero_os = :num AND tipo_os = :tipo 
                        ORDER BY data_registro DESC
                    """)
                    
                    with conn.connect() as con:
                        results = con.execute(
                            query_laudos, 
                            {"num": numero_os, "tipo": tipo_laudo}
                        ).fetchall()
                        laudos = [r._mapping for r in results]
                    
                    if not laudos:
                        st.info(f"Nenhum laudo registrado para a OS {numero_os}.")
                    else:
                        st.success(f"✅ **{len(laudos)} laudo(s) encontrado(s)**")
                        
                        for laudo in laudos:
                            data_reg = laudo["data_registro"].astimezone(fuso_sp).strftime("%d/%m/%Y %H:%M")
                            
                            exp_title = (
                                f"🔧 Laudo #{laudo['id']} - "
                                f"{laudo.get('estado_conservacao', 'N/A')} - "
                                f"Registrado em {data_reg}"
                            )
                            
                            with st.expander(exp_title, expanded=True):
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.markdown(f"**👤 Técnico:** {laudo['tecnico']}")
                                    st.markdown(f"**📊 Estado de Conservação:** {laudo.get('estado_conservacao', 'N/A')}")
                                    st.markdown(f"**🔧 Equipamento Completo:** {laudo.get('equipamento_completo', 'N/A')}")
                                
                                with col2:
                                    st.markdown(f"**📌 Status:** {laudo['status']}")
                                    st.markdown(f"**📅 Data de Registro:** {data_reg}")
                                
                                st.markdown("---")
                                st.markdown("**🔍 Diagnóstico:**")
                                st.text_area(
                                    f"diag_{laudo['id']}", 
                                    laudo.get("diagnostico", "Sem diagnóstico registrado."), 
                                    height=120, 
                                    disabled=True, 
                                    label_visibility="collapsed"
                                )
                                
                                if laudo.get("observacoes"):
                                    st.markdown("**📝 Observações:**")
                                    st.text_area(
                                        f"obs_{laudo['id']}", 
                                        laudo["observacoes"], 
                                        height=100, 
                                        disabled=True, 
                                        label_visibility="collapsed"
                                    )
                
                except Exception as e:
                    st.error(f"❌ Erro ao buscar laudos: {e}")
                    st.exception(e)
                
                st.markdown("---")
                if st.button("✓ Fechar", use_container_width=True, type="primary"):
                    del st.session_state["ver_laudo_numero"]
                    del st.session_state["ver_laudo_tipo"]
                    st.rerun()
            
            mostrar_laudos()

        # --- 6. FILTROS INTERATIVOS (OPCIONAL PARA GRÁFICOS) ---
        st.markdown("---")
        st.markdown("#### Filtros do Dashboard (Opcional)")
        st.caption("Use os filtros abaixo para refinar a visualização dos gráficos")
        
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

        # --- 7. APLICAÇÃO DOS FILTROS (APENAS PARA GRÁFICOS) ---
        df_filtrado = df_base[
            (df_base['data'] >= pd.to_datetime(data_inicio)) &
            (df_base['data'] <= pd.to_datetime(data_fim) + pd.Timedelta(days=1))
        ]
        
        if tecnico_selecionado != "Todos":
            df_filtrado = df_filtrado[df_filtrado['tecnico'] == tecnico_selecionado]

        if df_filtrado.empty:
            st.warning("Nenhum dado encontrado para os filtros selecionados.")
            st.stop()

        # Cálculo do TMA filtrado para o gráfico
        df_finalizadas_tma = df_filtrado[pd.notna(df_filtrado['data_finalizada'])].copy()
        
        if not df_finalizadas_tma.empty:
            df_finalizadas_tma['tempo_atendimento_dias'] = (
                df_finalizadas_tma['data_finalizada'] - df_finalizadas_tma['data']
            ).dt.total_seconds() / (3600 * 24)
            
            df_finalizadas_tma = df_finalizadas_tma[df_finalizadas_tma['tempo_atendimento_dias'] >= 0]

        st.markdown("---")

        # --- 8. GRÁFICOS VISUAIS (COM FILTROS APLICADOS) ---
        
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

            # GRÁFICO 2: TMA por Técnico
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