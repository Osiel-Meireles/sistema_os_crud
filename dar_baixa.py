# CÓDIGO ATUALIZADO E COMPLETO PARA: sistema_os_crud-main/dar_baixa.py

import streamlit as st
import pandas as pd
from database import get_connection
from sqlalchemy import text
from datetime import datetime
import pytz 
from config import STATUS_OPTIONS

def render():
    st.markdown("<h3 style='text-align: left;'>Atualizar Ordem de Serviço</h3>", unsafe_allow_html=True)
    st.write("Busque uma OS para atualizar seu status ou para dar baixa (finalizar).")

    numero_preenchido = st.session_state.get('numero_os_preenchido', None)
    if numero_preenchido:
        st.session_state.busca_os_input = numero_preenchido
        del st.session_state.numero_os_preenchido 
    
    USER_ROLE = st.session_state.get('role', 'tecnico')
    conn = get_connection()

    tipo_os = st.selectbox("Selecione o tipo de OS", ["OS Interna", "OS Externa"])
    numero_os_input = st.text_input(f"Digite o Número da {tipo_os}", key="busca_os_input")

    if numero_os_input:
        numero_os = numero_os_input
        try:
            with conn.connect() as con:
                table_name = "os_interna" if tipo_os == "OS Interna" else "os_externa"
                query = text(f"SELECT * FROM {table_name} WHERE numero = :numero")
                os_df = pd.read_sql(query, con, params={"numero": numero_os})
                if not os_df.empty:
                    st.session_state['os_data'] = os_df.iloc[0].to_dict() 
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
        is_awaiting_parts = (current_status == "AGUARDANDO PEÇA(S)")

        # --- SEÇÃO DO LAUDO PDF (LEGADO) ---
        # Mantém a exibição de PDFs antigos, se existirem
        if os_data.get('laudo_pdf') is not None:
            st.markdown("---")
            st.markdown("#### Laudo Técnico (Anexo PDF Antigo)")
            pdf_data = bytes(os_data['laudo_pdf']) if isinstance(os_data['laudo_pdf'], memoryview) else os_data['laudo_pdf']
            st.download_button(
                label=f"Baixar Laudo PDF ({os_data.get('laudo_filename')})",
                data=pdf_data,
                file_name=os_data.get('laudo_filename'),
                mime="application/pdf"
            )

        # --- ALTERAÇÃO AQUI: Exibe os Laudos do Sistema ---
        # Substitui a lógica de "Anexar Laudo"
        if is_awaiting_parts:
            st.markdown("---")
            st.markdown("#### Laudos de Componentes Registrados")
            
            tipo_os_laudo = tipo_os # O tipo_os já é "OS Interna" ou "OS Externa"
            numero_os = os_data.get('numero')

            laudos_registrados = []
            try:
                query_laudos = text("SELECT * FROM laudos WHERE numero_os = :num AND tipo_os = :tipo ORDER BY id DESC")
                with conn.connect() as con:
                    results = con.execute(query_laudos, {"num": numero_os, "tipo": tipo_os_laudo}).fetchall()
                    laudos_registrados = [r._mapping for r in results]
            except Exception as e:
                st.error(f"Erro ao buscar laudos de componentes: {e}")

            if not laudos_registrados:
                st.warning("Esta OS está 'Aguardando Peça(s)', mas nenhum laudo de componente foi encontrado no sistema.")
            else:
                fuso_sp = pytz.timezone('America/Sao_Paulo')
                for laudo in laudos_registrados:
                    data_reg = laudo['data_registro'].astimezone(fuso_sp).strftime('%d/%m/%Y %H:%M')
                    exp_title = f"Laudo ID {laudo['id']} - {laudo['componente']} (Status: {laudo['status']}) - Reg. {data_reg}"
                    with st.expander(exp_title):
                        st.markdown(f"**Técnico:** {laudo['tecnico']}")
                        st.markdown("**Especificação:**")
                        st.text_area(f"spec_{laudo['id']}", laudo['especificacao'], height=100, disabled=True, label_visibility="collapsed")
                        if laudo['link_compra']:
                            st.markdown(f"**Link:** [Link de Compra]({laudo['link_compra']})")
                        if laudo['observacoes']:
                            st.markdown("**Observações:**")
                            st.text_area(f"obs_{laudo['id']}", laudo['observacoes'], height=80, disabled=True, label_visibility="collapsed")
        # --- FIM DA ALTERAÇÃO ---


        if not is_delivered:
            st.markdown("---")
            with st.form("atualizar_os_form"):
                st.markdown("#### Atualize o status da OS")
                status_update_options = [s for s in STATUS_OPTIONS if s not in ["Todos", "AGUARDANDO RETIRADA", "ENTREGUE AO CLIENTE"]]
                
                # 'administrativo' e 'tecnico' não podem mexer se estiver aguardando peças
                if USER_ROLE in ['tecnico', 'administrativo'] and current_status == "AGUARDANDO PEÇA(S)":
                    st.info("A OS está aguardando peças. Apenas um administrador pode alterar este status.")
                    st.form_submit_button("Salvar Alterações de Status", disabled=True)
                else:
                    try:
                        status_index = status_update_options.index(current_status)
                    except ValueError: status_index = 0
                    
                    novo_status = st.selectbox("Novo Status", status_update_options, index=status_index)
                    texto_atualizacao = st.text_area("Serviço Executado / Descrição da Atualização", value=os_data.get('descricao') if current_status == "AGUARDANDO PEÇA(S)" else os_data.get('servico_executado', ''))
                    
                    submitted_update = st.form_submit_button("Salvar Alterações de Status")
                    if submitted_update:
                        if novo_status == "FINALIZADO" and not texto_atualizacao:
                            st.error("Para finalizar, o campo 'Serviço Executado' é obrigatório.")
                        else:
                            params = {"numero": os_data['numero']}
                            set_clauses = []
                            if novo_status == "FINALIZADO":
                                data_hora_finalizada_utc = datetime.now(pytz.utc)
                                params.update({
                                    "status": "AGUARDANDO RETIRADA", 
                                    "servico_executado": texto_atualizacao, 
                                    "data_finalizada": data_hora_finalizada_utc
                                })
                                set_clauses.extend(["status = :status", "servico_executado = :servico_executado", "data_finalizada = :data_finalizada"])
                            else:
                                params.update({
                                    "status": novo_status, 
                                    "descricao": texto_atualizacao
                                })
                                set_clauses.extend(["status = :status", "descricao = :descricao"])
                            try:
                                with conn.connect() as con:
                                    table_name = "os_interna" if tipo_os == "OS Interna" else "os_externa"
                                    update_query = text(f"UPDATE {table_name} SET {', '.join(set_clauses)} WHERE numero = :numero")
                                    con.execute(update_query, params)
                                    con.commit()
                                    st.success(f"Status da OS {os_data['numero']} atualizado! Recarregando...")
                                    del st.session_state['os_data']
                                    st.rerun()
                            except Exception as e:
                                st.error(f"Ocorreu um erro ao atualizar a OS: {e}")

        # Seção de "Registrar Entrega" (Apenas 'administrativo')
        if can_register_retirada and USER_ROLE == 'administrativo':
            if not is_delivered:
                st.markdown("---")
                st.markdown(f"#### Registrar Entrega ao Cliente ({USER_ROLE.capitalize()})")
                retirada_por = st.text_input("Nome de quem está retirando", value=os_data.get('retirada_por') or '', key="retirada_input")
                
                if st.button("Confirmar Entrega", type="primary"):
                    if not retirada_por:
                        st.error("O campo 'Nome de quem está retirando' é obrigatório.")
                    else:
                        try:
                            data_hora_retirada_utc = datetime.now(pytz.utc)
                            with conn.connect() as con:
                                with con.begin():
                                    table_name_os = "os_interna" if tipo_os == "OS Interna" else "os_externa"
                                    update_query_os = text(f"""
                                        UPDATE {table_name_os}
                                        SET status = :status, 
                                            data_finalizada = COALESCE(data_finalizada, :data_retirada),
                                            data_retirada = :data_retirada,
                                            retirada_por = :retirada_por
                                        WHERE numero = :numero
                                    """)
                                    con.execute(update_query_os, {
                                        "numero": os_data['numero'], 
                                        "status": "ENTREGUE AO CLIENTE",
                                        "data_retirada": data_hora_retirada_utc,
                                        "retirada_por": retirada_por,
                                    })
                            st.success(f"Retirada da OS {os_data['numero']} registrada com sucesso! Recarregando...")
                            del st.session_state['os_data']
                            st.rerun()
                        except Exception as e:
                            st.error(f"Ocorreu um erro ao registrar a retirada: {e}")
        
        elif can_register_retirada and USER_ROLE in ['tecnico', 'admin']:
             st.info("Serviço finalizado e aguardando retirada. Apenas um usuário 'Administrativo' pode registrar a entrega ao cliente.")

        if is_delivered:
            st.success("Esta OS já foi finalizada e entregue ao cliente. Nenhuma outra alteração pode ser feita.")