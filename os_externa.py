import streamlit as st
import pandas as pd
from database import get_connection
from sqlalchemy import text

def render():
    st.markdown("##### Ordens de Serviço Externas")
    st.text("Registre a ordem de serviço")

    conn = get_connection()

    # Opções para os selectboxes
    secretarias = ["Selecione...", "SAÚDE", "EDUCAÇÃO", "INFRAESTRUTURA", "ADMINISTRAÇÃO", "CIDADANIA", "GOVERNO", "SEGURANÇA", "FAZENDA", "ESPORTES"]
    tecnicos = ["Selecione...", "ANTONY CAUÃ", "MAYKON RODOLFO", "DIEGO CARDOSO", "ROMÉRIO CIRQUEIRA", "DIEL BATISTA", "JOSAFÁ MEDEIROS", "VALMIR FRANCISCO"]
    categorias = ["Selecione...", "INSTALAÇÃO", "MANUTENÇÃO", "REDES", "CONFIGURAÇÃO", "OUTROS"]
    equipamentos = ["Selecione...", "COMPUTADOR", "NOTEBOOK", "NOBREAK", "TRANSFORMADOR", "PERIFÉRICO", "MONITOR", "TABLET", "CELULAR"]
    
    # Formulário de inserção
    with st.form("nova_os_externa", clear_on_submit=True):
        numero = st.text_input("Número da OS")
        secretaria = st.selectbox("Secretaria", secretarias)
        setor = st.text_input("Setor")
        solicitante = st.text_input("Solicitante")
        telefone = st.text_input("Telefone")
        solicitacao_cliente = st.text_area("Solicitação do Cliente")
        categoria = st.selectbox("Categoria do Serviço", categorias)
        patrimonio = st.text_input("Número do Patrimônio")
        equipamento = st.selectbox("Equipamento", equipamentos)
        descricao = st.text_area("Descrição do Problema (OS)")
        tecnico = st.selectbox("Técnico", tecnicos)
        data = st.date_input("Data de Entrada")
        hora = st.time_input("Hora de Entrada")
        
        submitted = st.form_submit_button("Registrar ordem de serviço",type='primary')
        if submitted:
            if secretaria == "Selecione..." or tecnico == "Selecione..." or categoria == "Selecione...":
                st.error("Por favor, selecione uma secretaria, um técnico e uma categoria válidos.")
            else:
                with conn.connect() as con:
                    existing_os = con.execute(text("SELECT numero FROM os_externa WHERE numero = :numero"), {"numero": numero}).fetchone()
                    if existing_os:
                        st.error(f"Erro: O número de OS '{numero}' já existe. Por favor, use um número diferente.")
                    else:
                        con.execute(
                            text("""
                                INSERT INTO os_externa (numero, secretaria, setor, data, hora, solicitante, telefone, solicitacao_cliente, categoria, patrimonio, equipamento, descricao, status, tecnico)
                                VALUES (:numero, :secretaria, :setor, :data, :hora, :solicitante, :telefone, :solicitacao_cliente, :categoria, :patrimonio, :equipamento, :descricao, 'EM ABERTO', :tecnico)
                            """),
                            {
                                "numero": numero, "secretaria": secretaria, "setor": setor, "data": data, "hora": hora,
                                "solicitante": solicitante, "telefone": telefone, "solicitacao_cliente": solicitacao_cliente,
                                "categoria": categoria, "patrimonio": patrimonio, "equipamento": equipamento,
                                "descricao": descricao, "tecnico": tecnico,
                            }
                        )
                        con.commit()
                        st.success("OS Externa adicionada com sucesso!")

    st.markdown("##### Ordens de serviço externas cadastradas: ")
    df = pd.read_sql("SELECT * FROM os_externa", conn)
    st.dataframe(df)