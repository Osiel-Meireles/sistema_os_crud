import streamlit as st
import pandas as pd
from database import get_connection
from sqlalchemy import text
from import_export import exportar_filtrados_para_excel

def render():
    st.markdown("<h3 style='text-align: left;'>Filtrar Ordens de Serviço</h3>", unsafe_allow_html=True)

    # Opções para filtros
    secretarias = ["Todas", "SAÚDE", "EDUCAÇÃO", "INFRAESTRUTURA", "ADMINISTRAÇÃO", "CIDADANIA", "GOVERNO", "SEGURANÇA", "FAZENDA", "ESPORTES"]
    
    with st.form("filtro_form"):
        tipo_os = st.selectbox("Tipo de OS", ["Ambas", "OS Interna", "OS Externa"])
        secretaria = st.selectbox("Secretaria", secretarias)
        data_inicio = st.date_input("Data de Início")
        data_fim = st.date_input("Data de Fim")

        submitted = st.form_submit_button("Filtrar")

    if submitted:
        conn = get_connection()
        
        # Conecta ao banco de dados e executa as consultas
        try:
            with conn.connect() as con:
                params = {
                    "data_inicio": str(data_inicio),
                    "data_fim": str(data_fim),
                    "secretaria": secretaria,
                }
                
                df_final = pd.DataFrame()
                
                if tipo_os == "OS Interna":
                    query_interna = """
                        SELECT numero, secretaria, setor, data, hora, solicitante, telefone, equipamento, descricao, status, data_finalizada, data_retirada, retirada_por, tecnico, solicitacao_cliente, categoria, patrimonio, servico_executado, 'Interna' as tipo
                        FROM os_interna
                        WHERE data BETWEEN :data_inicio AND :data_fim
                    """
                    if secretaria != "Todas":
                        query_interna += " AND secretaria = :secretaria"
                    df_interna = pd.read_sql(text(query_interna), con, params=params)
                    df_final = pd.concat([df_final, df_interna])
                
                elif tipo_os == "OS Externa":
                    query_externa = """
                        SELECT numero, secretaria, setor, data, hora, solicitante, telefone, equipamento, descricao, status, data_finalizada, data_retirada, retirada_por, tecnico, solicitacao_cliente, categoria, patrimonio, servico_executado, 'Externa' as tipo
                        FROM os_externa
                        WHERE data BETWEEN :data_inicio AND :data_fim
                    """
                    if secretaria != "Todas":
                        query_externa += " AND secretaria = :secretaria"
                    df_externa = pd.read_sql(text(query_externa), con, params=params)
                    df_final = pd.concat([df_final, df_externa])

                elif tipo_os == "Ambas":
                    query_interna = """
                        SELECT numero, secretaria, setor, data, hora, solicitante, telefone, equipamento, descricao, status, data_finalizada, data_retirada, retirada_por, tecnico, solicitacao_cliente, categoria, patrimonio, servico_executado, 'Interna' as tipo
                        FROM os_interna
                        WHERE data BETWEEN :data_inicio AND :data_fim
                    """
                    if secretaria != "Todas":
                        query_interna += " AND secretaria = :secretaria"
                    df_interna = pd.read_sql(text(query_interna), con, params=params)
                    
                    query_externa = """
                        SELECT numero, secretaria, setor, data, hora, solicitante, telefone, equipamento, descricao, status, data_finalizada, data_retirada, retirada_por, tecnico, solicitacao_cliente, categoria, patrimonio, servico_executado, 'Externa' as tipo
                        FROM os_externa
                        WHERE data BETWEEN :data_inicio AND :data_fim
                    """
                    if secretaria != "Todas":
                        query_externa += " AND secretaria = :secretaria"
                    df_externa = pd.read_sql(text(query_externa), con, params=params)
                    
                    df_final = pd.concat([df_final, df_interna, df_externa], ignore_index=True)
            
            if df_final.empty:
                st.info("Não há dados nesse intervalo.")
            else:
                st.dataframe(df_final)
                excel_file = exportar_filtrados_para_excel(df_final)
                st.download_button(
                    label="Exportar para Excel",
                    data=excel_file,
                    file_name="dados_filtrados.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type='primary'
                )

        except Exception as e:
            st.error(f"Erro ao executar a consulta: {e}")