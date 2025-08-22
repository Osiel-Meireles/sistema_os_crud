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
        secretaria = st.selectbox("Secretaria", secretarias_sorted)
        setor = st.text_input("Setor")
        solicitante = st.text_input("Solicitante")
        telefone = st.text_input("Telefone")
        solicitacao_cliente = st.text_area("Solicitação do Cliente")
        categoria = st.selectbox("Categoria do Serviço", categorias_sorted)
        patrimonio = st.text_input("Número do Patrimônio")
        equipamento = st.selectbox("Equipamento", equipamentos_sorted)
        tecnico = st.selectbox("Técnico", tecnicos_sorted)
        data = st.date_input("Data de Entrada", value=date.today(), format="DD/MM/YYYY")
        hora = st.time_input("Hora de Entrada", value=datetime.now().time())
        
        submitted = st.form_submit_button("Registrar ordem de serviço",type='primary')
        if submitted:
            if not all([setor, solicitante, telefone, solicitacao_cliente, patrimonio]):
                st.error("Por favor, preencha todos os campos de texto.")
            elif "Selecione..." in [secretaria, tecnico, categoria, equipamento]:
                st.error("Por favor, selecione uma secretaria, técnico, categoria e equipamento válidos.")
            else:
                try:
                    with conn.connect() as con:
                        with con.begin():
                            con.execute(text("LOCK TABLE os_externa IN ACCESS EXCLUSIVE MODE"))
                            
                            numero_os = gerar_proximo_numero_os(con, "os_externa")
                            
                            con.execute(
                                text("""
                                    INSERT INTO os_externa (numero, secretaria, setor, data, hora, solicitante, telefone, solicitacao_cliente, categoria, patrimonio, equipamento, status, tecnico)
                                    VALUES (:numero, :secretaria, :setor, :data, :hora, :solicitante, :telefone, :solicitacao_cliente, :categoria, :patrimonio, :equipamento, 'EM ABERTO', :tecnico)
                                """),
                                {
                                    "numero": numero_os, "secretaria": secretaria, "setor": setor, "data": data, "hora": hora,
                                    "solicitante": solicitante, "telefone": telefone, "solicitacao_cliente": solicitacao_cliente,
                                    "categoria": categoria, "patrimonio": patrimonio, "equipamento": equipamento,
                                    "tecnico": tecnico,
                                }
                            )
                    st.success(f"OS Externa número {numero_os} adicionada com sucesso!")

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