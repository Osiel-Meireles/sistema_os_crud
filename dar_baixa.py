import streamlit as st
import pandas as pd
from database import get_connection
from sqlalchemy import text
from datetime import date
from config import STATUS_OPTIONS
from streamlit_drawable_canvas import st_canvas
import base64

def render():
    st.markdown("<h3 style='text-align: left;'>Atualizar Ordem de Serviço</h3>", unsafe_allow_html=True)
    st.write("Busque uma OS para atualizar seu status ou para dar baixa (finalizar).")

    conn = get_connection()

    tipo_os = st.selectbox("Selecione o tipo de OS", ["OS Interna", "OS Externa"])
    numero_os = st.text_input(f"Digite o Número da {tipo_os}", key="busca_os_input")

    if st.session_state.busca_os_input:
        numero_os = st.session_state.busca_os_input
        try:
            with conn.connect() as con:
                table_name = "os_interna" if tipo_os == "OS Interna" else "os_externa"
                query = text(f"SELECT * FROM {table_name} WHERE numero = :numero")
                os_df = pd.read_sql(query, con, params={"numero": numero_os})

                if not os_df.empty:
                    st.session_state['os_data'] = os_df.iloc[0]
                else:
                    st.warning(f"OS número {numero_os} não encontrada.")
                    if 'os_data' in st.session_state:
                        del st.session_state['os_data']
        except Exception as e:
            st.error(f"Ocorreu um erro ao buscar a OS: {e}")
            if 'os_data' in st.session_state:
                del st.session_state['os_data']
    else:
        if 'os_data' in st.session_state:
            del st.session_state['os_data']

    if 'os_data' in st.session_state:
        os_data = st.session_state['os_data']
        
        st.markdown("#### Informações da OS Encontrada:")
        st.dataframe(pd.DataFrame([os_data]))

        current_status = os_data.get('status', 'EM ABERTO')
        is_delivered = (current_status == "ENTREGUE AO CLIENTE")
        can_register_retirada = current_status in ["AGUARDANDO RETIRADA", "ENTREGUE AO CLIENTE"]

        if is_delivered:
            st.success("Esta OS já foi finalizada e entregue ao cliente. Nenhuma outra alteração pode ser feita.")

        st.markdown("---")
        
        # --- SEÇÃO DE ATUALIZAÇÃO DE STATUS (SEMPRE VISÍVEL) ---
        with st.form("atualizar_os_form"):
            st.markdown("#### Atualize o status da OS")
            status_update_options = [s for s in STATUS_OPTIONS if s not in ["Todos", "AGUARDANDO RETIRADA", "ENTREGUE AO CLIENTE"]]
            try:
                status_index = status_update_options.index(current_status)
            except ValueError: status_index = 0
            novo_status = st.selectbox("Novo Status", status_update_options, index=status_index, disabled=is_delivered)
            texto_atualizacao = st.text_area("Serviço Executado / Descrição da Atualização", value=os_data.get('descricao') if current_status == "AGUARDANDO PEÇA(S)" else os_data.get('servico_executado', ''), disabled=is_delivered)
            data_finalizada = st.date_input("Data de Finalização", value=pd.to_datetime(os_data.get('data_finalizada')).date() if pd.notna(os_data.get('data_finalizada')) else date.today(), disabled=(novo_status != "FINALIZADO" or is_delivered))
            submitted_update = st.form_submit_button("Salvar Alterações de Status", disabled=is_delivered)
            if submitted_update:
                if novo_status == "FINALIZADO" and not texto_atualizacao:
                    st.error("Para finalizar, o campo 'Serviço Executado' é obrigatório.")
                else:
                    params = {"numero": os_data['numero']}
                    if novo_status == "FINALIZADO":
                        params.update({"status": "AGUARDANDO RETIRADA", "servico_executado": texto_atualizacao, "data_finalizada": data_finalizada})
                    else:
                        params.update({"status": novo_status, "descricao": texto_atualizacao, "servico_executado": os_data.get('servico_executado', ''), "data_finalizada": None})
                    try:
                        with conn.connect() as con:
                            table_name = "os_interna" if tipo_os == "OS Interna" else "os_externa"
                            set_clauses = [f"{key} = :{key}" for key in params if key != 'numero']
                            update_query = text(f"UPDATE {table_name} SET {', '.join(set_clauses)} WHERE numero = :numero")
                            con.execute(update_query, params)
                            con.commit()
                            st.success(f"Status da OS {os_data['numero']} atualizado! Recarregando...")
                            del st.session_state['os_data']
                            st.rerun()
                    except Exception as e:
                        st.error(f"Ocorreu um erro ao atualizar a OS: {e}")

        # --- SEÇÃO DE REGISTRO DE RETIRADA E ASSINATURA (CONDICIONAL) ---
        if can_register_retirada:
            st.markdown("---")
            st.markdown("#### Confirmar Entrega e Coletar Assinatura")
            retirada_por = st.text_input("Confirmado por (Nome do Solicitante)", value=os_data.get('retirada_por') or '', disabled=is_delivered, key="retirada_input")
            
            st.write("Assinatura do Solicitante:")
            canvas_result = st_canvas(
                fill_color="rgba(255, 165, 0, 0.3)",
                stroke_width=3, stroke_color="#000000",
                background_color="#FFFFFF", height=150, width=600,
                drawing_mode="freedraw", key="canvas",
                display_toolbar=not is_delivered
            )

            if st.button("Confirmar Entrega e Salvar Assinatura", disabled=is_delivered, type="primary"):
                if not st.session_state.retirada_input:
                    st.error("O campo 'Confirmado por' é obrigatório.")
                elif canvas_result.image_data is None:
                    st.error("A assinatura do solicitante é obrigatória.")
                else:
                    try:
                        img_bytes = canvas_result.image_data.tobytes()
                        assinatura_base64 = base64.b64encode(img_bytes).decode("utf-8")
                        
                        with conn.connect() as con:
                            table_name = "os_interna" if tipo_os == "OS Interna" else "os_externa"
                            update_query = text(f"""
                                UPDATE {table_name}
                                SET status = :status, data_retirada = :data_retirada,
                                    retirada_por = :retirada_por, assinatura_solicitante_retirada = :assinatura
                                WHERE numero = :numero
                            """)
                            con.execute(update_query, {
                                "numero": os_data['numero'], "status": "ENTREGUE AO CLIENTE",
                                "data_retirada": date.today(), "retirada_por": st.session_state.retirada_input,
                                "assinatura": f"data:image/png;base64,{assinatura_base64}"
                            })
                            con.commit()
                            st.success(f"Retirada da OS {os_data['numero']} registrada com sucesso! Recarregando...")
                            del st.session_state['os_data']
                            st.rerun()
                    except Exception as e:
                        st.error(f"Ocorreu um erro ao registrar a retirada: {e}")