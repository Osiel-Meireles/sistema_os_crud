import streamlit as st
import pandas as pd
from database import get_connection
from sqlalchemy import text
from datetime import date
from config import STATUS_OPTIONS

def render():
    st.markdown("<h3 style='text-align: left;'>Atualizar Ordem de Serviço</h3>", unsafe_allow_html=True)
    st.write("Busque uma OS para atualizar seu status ou para dar baixa (finalizar).")
    
    conn = get_connection()
    
    tipo_os = st.selectbox("Selecione o tipo de OS", ["OS Interna", "OS Externa"])
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
                    st.session_state['os_data'] = os_data
                    st.markdown("#### Informações da OS Encontrada:")
                    st.dataframe(os_df)
                else:
                    st.warning(f"OS número {numero_os} não encontrada.")
                    if 'os_data' in st.session_state:
                        del st.session_state['os_data']
                    
        except Exception as e:
            st.error(f"Ocorreu um erro ao buscar a OS: {e}")

    if 'os_data' in st.session_state and st.session_state['os_data'] is not None:
        os_data = st.session_state['os_data']
        
        current_status = os_data.get('status', 'EM ABERTO')
        is_delivered = (current_status == "ENTREGUE AO CLIENTE")

        if is_delivered:
            st.success("Esta OS já foi finalizada e entregue ao cliente. Nenhuma outra alteração pode ser feita.")

        st.markdown("---")
        message_placeholder_update = st.empty()
        
        with st.form("atualizar_os_form"):
            st.markdown("#### Atualize o status da OS")
            
            status_update_options = [s for s in STATUS_OPTIONS if s not in ["Todos", "AGUARDANDO RETIRADA", "ENTREGUE AO CLIENTE"]]
            
            try:
                status_index = status_update_options.index(current_status)
            except ValueError:
                status_index = 0

            novo_status = st.selectbox("Novo Status", status_update_options, index=status_index, disabled=is_delivered)
            
            texto_atualizacao = st.text_area(
                "Serviço Executado / Descrição da Atualização", 
                value=os_data.get('descricao') if current_status == "AGUARDANDO PEÇA(S)" else os_data.get('servico_executado', ''),
                disabled=is_delivered
            )
            
            data_finalizada = st.date_input(
                "Data de Finalização", 
                value=pd.to_datetime(os_data.get('data_finalizada')).date() if pd.notna(os_data.get('data_finalizada')) else date.today(),
                disabled=(novo_status != "FINALIZADO" or is_delivered)
            )
            
            submitted_update = st.form_submit_button("Salvar Alterações de Status", disabled=is_delivered)

            if submitted_update:
                if novo_status == "FINALIZADO" and not texto_atualizacao:
                    message_placeholder_update.error("Para finalizar, o campo 'Serviço Executado / Descrição da Atualização' é obrigatório.")
                else:
                    params = { "numero": numero_os }
                    
                    if novo_status == "FINALIZADO":
                        params["status"] = "AGUARDANDO RETIRADA"
                        params["servico_executado"] = texto_atualizacao
                        params["data_finalizada"] = data_finalizada
                    else:
                        params["status"] = novo_status
                        params["descricao"] = texto_atualizacao
                        params["servico_executado"] = os_data.get('servico_executado', '')
                        params["data_finalizada"] = None

                    try:
                        with conn.connect() as con:
                            table_name = "os_interna" if tipo_os == "OS Interna" else "os_externa"
                            set_clauses = [f"{key} = :{key}" for key in params if key != 'numero']
                            
                            update_query = text(f"""
                                UPDATE {table_name}
                                SET {', '.join(set_clauses)}
                                WHERE numero = :numero
                            """)
                            con.execute(update_query, params)
                            con.commit()
                            message_placeholder_update.success(f"Status da OS {numero_os} atualizado com sucesso! Recarregando...")
                            del st.session_state['os_data']
                            st.rerun()
                    except Exception as e:
                        message_placeholder_update.error(f"Ocorreu um erro ao atualizar a OS: {e}")

        if os_data.get('status') in ["AGUARDANDO RETIRADA", "ENTREGUE AO CLIENTE"]:
            st.markdown("---")
            message_placeholder_retirada = st.empty()

            with st.form("retirada_form"):
                st.markdown("#### Registrar Retirada do Equipamento")

                data_retirada = st.date_input("Data de Retirada", value=pd.to_datetime(os_data.get('data_retirada')).date() if pd.notna(os_data.get('data_retirada')) else date.today(), disabled=is_delivered)
                retirada_por = st.text_input("Retirada por", value=os_data.get('retirada_por') or '', disabled=is_delivered)

                submitted_retirada = st.form_submit_button("Confirmar Retirada", disabled=is_delivered)

                if submitted_retirada:
                    if not retirada_por:
                        message_placeholder_retirada.error("O campo 'Retirada por' é obrigatório.")
                    else:
                        try:
                            with conn.connect() as con:
                                table_name = "os_interna" if tipo_os == "OS Interna" else "os_externa"
                                update_query = text(f"""
                                    UPDATE {table_name}
                                    SET status = :status,
                                        data_retirada = :data_retirada,
                                        retirada_por = :retirada_por
                                    WHERE numero = :numero
                                """)
                                con.execute(update_query, {
                                    "numero": numero_os,
                                    "status": "ENTREGUE AO CLIENTE",
                                    "data_retirada": data_retirada,
                                    "retirada_por": retirada_por
                                })
                                con.commit()
                                message_placeholder_retirada.success(f"Retirada da OS {numero_os} registrada com sucesso! Recarregando...")
                                del st.session_state['os_data']
                                st.rerun()
                        except Exception as e:
                            message_placeholder_retirada.error(f"Ocorreu um erro ao registrar a retirada: {e}")