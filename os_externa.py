import streamlit as st
import pandas as pd
from sqlalchemy import text
from datetime import date, datetime

from database import get_connection, gerar_proximo_numero_os
from config import SECRETARIAS, TECNICOS, CATEGORIAS_EXTERNA, EQUIPAMENTOS

def render():
    st.markdown("##### Ordens de Serviço Externas")
    st.text("Registre a ordem de serviço")

    conn = get_connection()

    secretarias_sorted = [SECRETARIAS[0]] + sorted(SECRETARIAS[1:])
    tecnicos_sorted = [TECNICOS[0]] + sorted(TECNICOS[1:])
    categorias_sorted = [CATEGORIAS_EXTERNA[0]] + sorted(CATEGORIAS_EXTERNA[1:])
    equipamentos_sorted = [EQUIPAMENTOS[0]] + sorted(EQUIPAMENTOS[1:])

    with st.form("nova_os_externa", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            secretaria = st.selectbox("Secretaria", secretarias_sorted)
            solicitante = st.text_input("Solicitante")
            solicitacao_cliente = st.text_area("Solicitação do Cliente")
            patrimonio = st.text_input("Número do Patrimônio")
            tecnico = st.selectbox("Técnico", tecnicos_sorted)
            data = st.date_input("Data de Entrada", value=date.today(), format="DD/MM/YYYY")

        with col2:
            setor = st.text_input("Setor")
            telefone = st.text_input("Telefone")
            categoria = st.selectbox("Categoria do Serviço", categorias_sorted)
            equipamento = st.selectbox("Equipamento", equipamentos_sorted)
            hora = st.time_input("Hora de Entrada", value=datetime.now().time())
            
        # --- CAMPO DE ASSINATURA REMOVIDO DAQUI ---
        
        submitted = st.form_submit_button("Registrar ordem de serviço", use_container_width=True, type='primary')

        if submitted:
            # Validações
            if not all([setor, solicitante, telefone, solicitacao_cliente]):
                st.error("Por favor, preencha todos os campos de texto (Setor, Solicitante, Telefone, Solicitação).")
                return
            if "Selecione..." in [secretaria, tecnico, categoria, equipamento]:
                st.error("Por favor, selecione uma secretaria, técnico, categoria e equipamento válidos.")
                return

            try:
                with conn.connect() as con:
                    with con.begin():
                        con.execute(text("LOCK TABLE os_externa IN ACCESS EXCLUSIVE MODE"))
                        
                        numero_os = gerar_proximo_numero_os(con, "os_externa")
                        
                        # --- CAMPO DE ASSINATURA REMOVIDO DA QUERY ---
                        con.execute(
                            text("""
                                INSERT INTO os_externa (numero, secretaria, setor, data, hora, solicitante, telefone, solicitacao_cliente, categoria, patrimonio, equipamento, status, tecnico)
                                VALUES (:numero, :secretaria, :setor, :data, :hora, :solicitante, :telefone, :solicitacao_cliente, :categoria, :patrimonio, :equipamento, 'EM ABERTO', :tecnico)
                            """),
                            {
                                "numero": numero_os, "secretaria": secretaria, "setor": setor, "data": data, "hora": hora,
                                "solicitante": solicitante, "telefone": telefone, "solicitacao_cliente": solicitacao_cliente,
                                "categoria": categoria, "patrimonio": patrimonio, "equipamento": equipamento,
                                "tecnico": tecnico
                            }
                        )
                st.toast(f"✅ OS Externa nº {numero_os} adicionada com sucesso!")

            except Exception as e:
                st.error(f"Ocorreu um erro ao registrar a OS: {e}")

    st.markdown("---")
    st.markdown("##### Ordens de serviço externas cadastradas: ")
    df = pd.read_sql("SELECT * FROM os_externa ORDER BY id DESC", conn)
    
    date_cols = ['data', 'data_finalizada', 'data_retirada']
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%d/%m/%Y')

    st.dataframe(df)
