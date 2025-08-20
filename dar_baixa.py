import streamlit as st
import pandas as pd
from database import get_connection
from sqlalchemy import text
from datetime import date

def render():
    st.markdown("<h3 style='text-align: left;'>Dar Baixa em Ordem de Serviço</h3>", unsafe_allow_html=True)
    st.write("Preencha as informações abaixo para finalizar e dar baixa em uma OS.")

    conn = get_connection()

    # Opção para escolher o tipo de OS
    tipo_os = st.selectbox("Selecione o tipo de OS", ["OS Interna", "OS Externa"])
    
    # Campo de busca da OS
    numero_os = st.text_input(f"Digite o Número da {tipo_os}")
    os_data = None
    
    if numero_os:
        try:
            with conn.connect() as con:
                table_name = "os_interna" if tipo_os == "OS Interna" else "os_externa"
                query = text(f"SELECT * FROM {table_name} WHERE numero = :numero")
                os_df = pd.read_sql(query, con, params={"numero": numero_os})
                
                if not os_df.empty:
                    os_data = os_df.iloc[0]
                    st.markdown("#### Informações da OS encontrada:")
                    st.write(os_df)
                else:
                    st.warning(f"OS número {numero_os} não encontrada.")
                    
        except Exception as e:
            st.error(f"Ocorreu um erro ao buscar a OS: {e}")

    if os_data is not None and os_data.get('status', 'EM ABERTO') == 'EM ABERTO':
        st.markdown("---")
        st.markdown("#### Campos para dar baixa na OS")
        with st.form("dar_baixa_os", clear_on_submit=True):
            servico_executado = st.text_area("Serviço Executado")
            data_finalizada = st.date_input("Data de Finalização")
            data_retirada = st.date_input("Data de Retirada")
            retirada_por = st.text_input("Retirada por")
            
            submitted = st.form_submit_button("Dar Baixa", type='primary')

            if submitted:
                if not servico_executado:
                    st.error("Por favor, preencha o campo de 'Serviço Executado'.")
                else:
                    try:
                        with conn.connect() as con:
                            table_name = "os_interna" if tipo_os == "OS Interna" else "os_externa"
                            con.execute(
                                text(f"""
                                    UPDATE {table_name}
                                    SET data_finalizada = :data_finalizada,
                                        data_retirada = :data_retirada,
                                        retirada_por = :retirada_por,
                                        servico_executado = :servico_executado,
                                        status = 'FINALIZADO'
                                    WHERE numero = :numero
                                """),
                                {
                                    "numero": numero_os,
                                    "data_finalizada": data_finalizada,
                                    "data_retirada": data_retirada,
                                    "retirada_por": retirada_por,
                                    "servico_executado": servico_executado
                                }
                            )
                            con.commit()
                            st.success(f"OS {tipo_os} número {numero_os} finalizada com sucesso!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Ocorreu um erro ao dar baixa na OS: {e}")
    elif os_data is not None and os_data.get('status') == 'FINALIZADO':
        st.warning("Esta OS já foi finalizada.")