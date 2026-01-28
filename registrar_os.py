# CÓDIGO ATUALIZADO E COMPLETO PARA: sistema_os_crud-main/registrar_os.py

import streamlit as st
import pandas as pd
from sqlalchemy import text
from datetime import date, datetime
import math
import pytz

from database import get_connection, gerar_proximo_numero_os
from config import SECRETARIAS, TECNICOS, CATEGORIAS, EQUIPAMENTOS

def render():
    st.markdown("##### Registrar Nova Ordem de Serviço")
    
    username = st.session_state.get('username')
    display_name = st.session_state.get('display_name', username)
    user_role = st.session_state.get('role', 'tecnico')

    if not username:
        st.error("Sessão inválida. Por favor, faça login novamente.")
        st.session_state.logged_in = False
        st.rerun()
        return

    secretarias_sorted = sorted(SECRETARIAS)
    tecnicos_sorted = sorted(TECNICOS)
    categorias_sorted = sorted(CATEGORIAS)
    equipamentos_sorted = sorted(EQUIPAMENTOS)
    
    fuso_horario_sp = pytz.timezone('America/Sao_Paulo')
    conn = get_connection()

    tab1, tab2 = st.tabs(["Ordem de Serviço Interna", "Ordem de Serviço Externa"])

    # --- ABA DE OS INTERNA ---
    with tab1:
        st.text("Registre a ordem de serviço interna")
        with st.form("nova_os_interna"):
            col1, col2 = st.columns(2)

            with col1:
                secretaria = st.selectbox(
                    "Secretaria *", secretarias_sorted, 
                    index=None, placeholder="Selecione a secretaria..."
                )
                solicitante = st.text_input("Solicitante *")
                solicitacao_cliente = st.text_area("Solicitação do Cliente *")
                patrimonio = st.text_input("Número do Patrimônio")
                
                tecnico_disabled = False
                tecnico_valor_padrao = None
                if user_role == 'tecnico':
                    for t in tecnicos_sorted:
                        if t.upper() == display_name.upper():
                            tecnico_valor_padrao = t
                            tecnico_disabled = True
                            break
                
                tecnico_index = None
                if tecnico_valor_padrao:
                    tecnico_index = tecnicos_sorted.index(tecnico_valor_padrao)

                tecnico = st.selectbox(
                    "Técnico *", tecnicos_sorted,
                    index=tecnico_index,
                    placeholder="Selecione o técnico...",
                    disabled=tecnico_disabled
                )
                
                data = st.date_input("Data de Entrada", value=date.today(), format="DD/MM/YYYY")

            with col2:
                setor = st.text_input("Setor *")
                telefone = st.text_input("Telefone *")
                categoria = st.selectbox(
                    "Categoria do Serviço *", categorias_sorted,
                    index=None, placeholder="Selecione a categoria..."
                )
                equipamento = st.selectbox(
                    "Equipamento *", equipamentos_sorted,
                    index=None, placeholder="Selecione o equipamento..."
                )
                # ADIÇÃO: Campo Marca/Modelo
                marca_modelo = st.text_input("Marca / Modelo", placeholder="Ex: Dell Optiplex, HP LaserJet...")
                
                hora = st.time_input("Hora de Entrada", value=datetime.now(fuso_horario_sp).time())
            
            submitted_interna = st.form_submit_button("Registrar OS Interna", use_container_width=True, type='primary')
            
            if submitted_interna:
                tecnico_final = tecnico_valor_padrao if tecnico_disabled else tecnico

                if not all([setor, solicitante, telefone, solicitacao_cliente]):
                    st.error("Por favor, preencha todos os campos marcados com * (Setor, Solicitante, Telefone, Solicitação).")
                elif not all([secretaria, tecnico_final, categoria, equipamento]):
                    st.error("Por favor, selecione uma secretaria, técnico, categoria e equipamento válidos.")
                else:
                    try:
                        with conn.connect() as con:
                            with con.begin(): 
                                con.execute(text("LOCK TABLE os_interna IN ACCESS EXCLUSIVE MODE"))
                                numero_os = gerar_proximo_numero_os(con, "os_interna")
                                con.execute(
                                    text("""
                                        INSERT INTO os_interna (
                                            numero, secretaria, setor, data, hora, solicitante, telefone, 
                                            solicitacao_cliente, categoria, patrimonio, equipamento, 
                                            descricao, status, tecnico, registrado_por
                                        )
                                        VALUES (
                                            :numero, :secretaria, :setor, :data, :hora, :solicitante, :telefone, 
                                            :solicitacao_cliente, :categoria, :patrimonio, :equipamento, 
                                            :descricao, 'EM ABERTO', :tecnico, :registrado_por
                                        )
                                    """),
                                    {
                                        "numero": numero_os, "secretaria": secretaria, "setor": setor, 
                                        "data": data, "hora": hora, "solicitante": solicitante, 
                                        "telefone": telefone, "solicitacao_cliente": solicitacao_cliente,
                                        "categoria": categoria, "patrimonio": patrimonio, 
                                        "equipamento": equipamento, "descricao": marca_modelo,
                                        "tecnico": tecnico_final, "registrado_por": username 
                                    }
                                )
                        st.toast(f"✅ OS Interna nº {numero_os} adicionada com sucesso!")
                    except Exception as e:
                        st.error(f"Ocorreu um erro ao registrar a OS: {e}")
        
        st.markdown("---")
        st.markdown("##### Últimas OS Internas cadastradas: ")
        if 'os_interna_page' not in st.session_state: st.session_state.os_interna_page = 1
        ITEMS_PER_PAGE_INT = 15
        try:
            total_items_query_int = text("SELECT COUNT(id) FROM os_interna")
            with conn.connect() as con:
                total_items_int = con.execute(total_items_query_int).scalar()
        except Exception as e:
            st.error(f"Não foi possível contar os registros: {e}")
            total_items_int = 0
        total_pages_int = math.ceil(total_items_int / ITEMS_PER_PAGE_INT) if total_items_int > 0 else 1
        if st.session_state.os_interna_page > total_pages_int: st.session_state.os_interna_page = total_pages_int
        if st.session_state.os_interna_page < 1: st.session_state.os_interna_page = 1
        offset_int = (st.session_state.os_interna_page - 1) * ITEMS_PER_PAGE_INT
        query_int = text(f"SELECT * FROM os_interna ORDER BY id DESC LIMIT :limit OFFSET :offset")
        df_int = pd.read_sql(query_int, conn, params={"limit": ITEMS_PER_PAGE_INT, "offset": offset_int})
        for col in ['data', 'data_finalizada', 'data_retirada']:
            if col in df_int.columns:
                df_int[col] = pd.to_datetime(df_int[col], errors='coerce').dt.strftime('%d/%m/%Y')
        if 'hora' in df_int.columns:
            df_int['hora'] = pd.to_datetime(df_int['hora'].astype(str), errors='coerce').dt.strftime('%H:%M:%S')
        st.dataframe(df_int)
        if total_pages_int > 1:
            col_nav1_int, col_nav2_int, col_nav3_int = st.columns([1, 1, 1])
            if col_nav1_int.button("Anterior", key="prev_interna", disabled=(st.session_state.os_interna_page <= 1)):
                st.session_state.os_interna_page -= 1
                st.rerun()
            col_nav2_int.write(f"**Página {st.session_state.os_interna_page} de {total_pages_int}**")
            if col_nav3_int.button("Próxima", key="next_interna", disabled=(st.session_state.os_interna_page >= total_pages_int)):
                st.session_state.os_interna_page += 1
                st.rerun()

    # --- ABA DE OS EXTERNA ---
    with tab2:
        st.text("Registre a ordem de serviço externa")
        with st.form("nova_os_externa"):
            col1_ext, col2_ext = st.columns(2)
            with col1_ext:
                secretaria_ext = st.selectbox(
                    "Secretaria *", secretarias_sorted, 
                    index=None, placeholder="Selecione a secretaria..."
                )
                solicitante_ext = st.text_input("Solicitante *")
                solicitacao_cliente_ext = st.text_area("Solicitação do Cliente *")
                patrimonio_ext = st.text_input("Número do Patrimônio")
                
                tecnico_disabled_ext = False
                tecnico_valor_padrao_ext = None
                if user_role == 'tecnico':
                    for t in tecnicos_sorted:
                        if t.upper() == display_name.upper():
                            tecnico_valor_padrao_ext = t
                            tecnico_disabled_ext = True
                            break
                
                tecnico_index_ext = None
                if tecnico_valor_padrao_ext:
                    tecnico_index_ext = tecnicos_sorted.index(tecnico_valor_padrao_ext)

                tecnico_ext = st.selectbox(
                    "Técnico *", tecnicos_sorted,
                    index=tecnico_index_ext,
                    placeholder="Selecione o técnico...",
                    disabled=tecnico_disabled_ext
                )
                
                data_ext = st.date_input("Data de Entrada", value=date.today(), format="DD/MM/YYYY")

            with col2_ext:
                setor_ext = st.text_input("Setor *")
                telefone_ext = st.text_input("Telefone *")
                categoria_ext = st.selectbox(
                    "Categoria do Serviço *", categorias_sorted,
                    index=None, placeholder="Selecione a categoria..."
                )
                equipamento_ext = st.selectbox(
                    "Equipamento *", equipamentos_sorted,
                    index=None, placeholder="Selecione o equipamento..."
                )
                # ADIÇÃO: Campo Marca/Modelo
                marca_modelo_ext = st.text_input("Marca / Modelo", placeholder="Ex: Dell Optiplex, HP LaserJet...", key="ext_marca")
                
                hora_ext = st.time_input("Hora de Entrada", value=datetime.now(fuso_horario_sp).time())
                
            submitted_externa = st.form_submit_button("Registrar OS Externa", use_container_width=True, type='primary')

            if submitted_externa:
                tecnico_final_ext = tecnico_valor_padrao_ext if tecnico_disabled_ext else tecnico_ext

                if not all([setor_ext, solicitante_ext, telefone_ext, solicitacao_cliente_ext]):
                    st.error("Por favor, preencha todos os campos marcados com * (Setor, Solicitante, Telefone, Solicitação).")
                elif not all([secretaria_ext, tecnico_final_ext, categoria_ext, equipamento_ext]):
                    st.error("Por favor, selecione uma secretaria, técnico, categoria e equipamento válidos.")
                else:
                    try:
                        with conn.connect() as con:
                            with con.begin():
                                con.execute(text("LOCK TABLE os_externa IN ACCESS EXCLUSIVE MODE"))
                                numero_os_ext = gerar_proximo_numero_os(con, "os_externa")
                                con.execute(
                                    text("""
                                        INSERT INTO os_externa (
                                            numero, secretaria, setor, data, hora, solicitante, telefone, 
                                            solicitacao_cliente, categoria, patrimonio, equipamento, 
                                            descricao, status, tecnico, registrado_por
                                        )
                                        VALUES (
                                            :numero, :secretaria, :setor, :data, :hora, :solicitante, :telefone, 
                                            :solicitacao_cliente, :categoria, :patrimonio, :equipamento, 
                                            :descricao, 'EM ABERTO', :tecnico, :registrado_por
                                        )
                                    """),
                                    {
                                        "numero": numero_os_ext, "secretaria": secretaria_ext, "setor": setor_ext, 
                                        "data": data_ext, "hora": hora_ext, "solicitante": solicitante_ext, 
                                        "telefone": telefone_ext, "solicitacao_cliente": solicitacao_cliente_ext,
                                        "categoria": categoria_ext, "patrimonio": patrimonio_ext, 
                                        "equipamento": equipamento_ext, "descricao": marca_modelo_ext,
                                        "tecnico": tecnico_final_ext, "registrado_por": username 
                                    }
                                )
                        st.toast(f"✅ OS Externa nº {numero_os_ext} adicionada com sucesso!")
                    except Exception as e:
                        st.error(f"Ocorreu um erro ao registrar a OS: {e}")

        st.markdown("---")
        st.markdown("##### Últimas OS Externas cadastradas: ")
        if 'os_externa_page' not in st.session_state: st.session_state.os_externa_page = 1
        ITEMS_PER_PAGE_EXT = 15
        try:
            total_items_query_ext = text("SELECT COUNT(id) FROM os_externa")
            with conn.connect() as con:
                total_items_ext = con.execute(total_items_query_ext).scalar()
        except Exception as e:
            st.error(f"Não foi possível contar os registros: {e}")
            total_items_ext = 0
        total_pages_ext = math.ceil(total_items_ext / ITEMS_PER_PAGE_EXT) if total_items_ext > 0 else 1
        if st.session_state.os_externa_page > total_pages_ext: st.session_state.os_externa_page = total_pages_ext
        if st.session_state.os_externa_page < 1: st.session_state.os_externa_page = 1
        offset_ext = (st.session_state.os_externa_page - 1) * ITEMS_PER_PAGE_EXT
        query_ext = text(f"SELECT * FROM os_externa ORDER BY id DESC LIMIT :limit OFFSET :offset")
        df_ext = pd.read_sql(query_ext, conn, params={"limit": ITEMS_PER_PAGE_EXT, "offset": offset_ext})
        for col in ['data', 'data_finalizada', 'data_retirada']:
            if col in df_ext.columns:
                df_ext[col] = pd.to_datetime(df_ext[col], errors='coerce').dt.strftime('%d/%m/%Y')
        if 'hora' in df_ext.columns:
            df_ext['hora'] = pd.to_datetime(df_ext['hora'].astype(str), errors='coerce').dt.strftime('%H:%M:%S')
        st.dataframe(df_ext)
        if total_pages_ext > 1:
            col_nav1_ext, col_nav2_ext, col_nav3_ext = st.columns([1, 1, 1])
            if col_nav1_ext.button("Anterior", key="prev_externa", disabled=(st.session_state.os_externa_page <= 1)):
                st.session_state.os_externa_page -= 1
                st.rerun()
            col_nav2_ext.write(f"**Página {st.session_state.os_externa_page} de {total_pages_ext}**")
            if col_nav3_ext.button("Próxima", key="next_externa", disabled=(st.session_state.os_externa_page >= total_pages_ext)):
                st.session_state.os_externa_page += 1
                st.rerun()