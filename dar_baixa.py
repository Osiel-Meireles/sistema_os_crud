import streamlit as st
import pandas as pd
from database import get_connection
from sqlalchemy import text
from datetime import datetime
import pytz
from config import STATUS_OPTIONS


def limpar_estado_baixa():
    """Limpa todos os estados relacionados à OS selecionada para baixa."""
    st.session_state.pop("os_baixa_encontrada", None)
    # Limpar widgets do formulário para não herdar valores
    st.session_state.pop("select_status_baixa_admin", None)
    st.session_state.pop("select_status_baixa_tecnico", None)
    st.session_state.pop("date_finalizacao_baixa", None)
    st.session_state.pop("textarea_obs_baixa", None)
    st.session_state.pop("input_retirada_por", None)
    st.session_state.pop("date_retirada", None)


def f_buscar_os_para_baixa(conn, tipo_os, numero_os):
    """Busca uma OS específica no banco de dados para dar baixa."""
    if not numero_os or not str(numero_os).strip():
        st.error("O campo 'Número da OS' é obrigatório.")
        return None

    numero_os = str(numero_os).strip()
    table_name = "os_interna" if tipo_os == "Interna" else "os_externa"

    query = text(
        f"""
        SELECT id, numero, secretaria, setor, equipamento, status, solicitante,
               patrimonio, categoria, tecnico, data, solicitacao_cliente, servico_executado
        FROM {table_name}
        WHERE numero = :numero
        """
    )

    try:
        with conn.connect() as con:
            result = con.execute(query, {"numero": numero_os}).fetchone()

        if result:
            os_data = dict(result._mapping)
            os_data["numero_os"] = numero_os
            os_data["tipo_os"] = tipo_os
            st.session_state.os_baixa_encontrada = os_data
            return os_data

        st.warning(f"OS {tipo_os} com número {numero_os} não encontrada.")
        limpar_estado_baixa()
        return None

    except Exception as e:
        st.error(f"Erro ao buscar OS: {e}")
        limpar_estado_baixa()
        return None


def f_dar_baixa(conn, table_name, os_id, dados_baixa, role):
    """Atualiza o status da OS para baixa/finalização."""
    try:
        with conn.connect() as con:
            with con.begin():
                # REGRA DE NEGÓCIO: Técnico muda "FINALIZADO" → "AGUARDANDO RETIRADA"
                if role == "tecnico" and dados_baixa.get("status") == "FINALIZADO":
                    dados_baixa["status"] = "AGUARDANDO RETIRADA"

                set_clause = []
                params = {"id": os_id}
                for key, value in dados_baixa.items():
                    if key != "id":
                        set_clause.append(f"{key} = :{key}")
                        params[key] = value

                if not set_clause:
                    st.error("Nenhum dado para atualizar.")
                    return False

                query = text(
                    f"UPDATE {table_name} SET {', '.join(set_clause)} WHERE id = :id"
                )
                con.execute(query, params)

        if role == "tecnico":
            st.success("OS finalizada! Status alterado para 'AGUARDANDO RETIRADA'")
        else:
            st.success("Baixa registrada com sucesso!")
        return True

    except Exception as e:
        st.error(f"Erro ao registrar baixa: {e}")
        return False


def render():
    st.title("Dar Baixa - Finalizar Ordem de Serviço")

    conn = get_connection()
    role = st.session_state.get("role", "")

    # Verificar se veio de Minhas Tarefas com OS pré-selecionada
    baixa_os_id = st.session_state.get("baixa_os_id")
    baixa_os_numero = st.session_state.get("baixa_os_numero")
    baixa_os_tipo = st.session_state.get("baixa_os_tipo", "Interna")

    st.markdown("---")

    # Exibir informação de permissões
    if role == "tecnico":
        st.info(
            "Como técnico, você pode finalizar a OS. O status será automaticamente alterado para 'AGUARDANDO RETIRADA'."
        )
    elif role in ["admin", "administrativo"]:
        st.info(
            "Como administrador, você pode registrar a retirada e informar quem retirou o equipamento."
        )

    st.markdown("---")

    # Seção de pesquisa/seleção de OS
    st.markdown("### Selecionar Ordem de Serviço para Baixa")
    col1, col2 = st.columns(2)

    with col1:
        tipo_os_options = ["Interna", "Externa"]
        tipo_os_index = (
            tipo_os_options.index(baixa_os_tipo)
            if baixa_os_tipo in tipo_os_options
            else 0
        )
        tipo_os = st.selectbox(
            "Tipo de OS",
            tipo_os_options,
            index=tipo_os_index,
            key="select_tipo_os_baixa",
        )

    with col2:
        numero_os = st.text_input(
            "Número da OS",
            value=baixa_os_numero if baixa_os_numero else "",
            placeholder="Ex: 1-25",
            key="input_numero_os_baixa",
        )

    # ✅ CORREÇÃO: Detectar mudança de filtro e limpar OS anterior
    filtro_atual = {
        "tipo_os": tipo_os,
        "numero_os": (numero_os or "").strip(),
    }
    filtro_anterior = st.session_state.get("filtro_baixa_anterior")

    if filtro_atual != filtro_anterior:
        limpar_estado_baixa()
        st.session_state["filtro_baixa_anterior"] = filtro_atual

    # Buscar automaticamente quando vem de Minhas Tarefas
    if (
        baixa_os_id
        and baixa_os_numero
        and "os_baixa_encontrada" not in st.session_state
    ):
        with st.spinner("Buscando OS automaticamente..."):
            os_auto = f_buscar_os_para_baixa(conn, baixa_os_tipo, baixa_os_numero)
        
        # Fixar snapshot do filtro para próxima renderização
        st.session_state["filtro_baixa_anterior"] = {
            "tipo_os": baixa_os_tipo,
            "numero_os": str(baixa_os_numero).strip(),
        }
        
        # Limpar variáveis de redirecionamento
        st.session_state.baixa_os_id = None
        st.session_state.baixa_os_numero = None
        st.session_state.baixa_os_tipo = None

    # Botão de busca manual
    if st.button("Buscar OS", use_container_width=True, type="primary"):
        f_buscar_os_para_baixa(conn, tipo_os, numero_os)
        st.session_state["filtro_baixa_anterior"] = {
            "tipo_os": tipo_os,
            "numero_os": (numero_os or "").strip(),
        }

    os_encontrada = st.session_state.get("os_baixa_encontrada")

    if os_encontrada:
        # ✅ CORREÇÃO: ID ÚNICO para keys dos widgets
        os_numero_display = os_encontrada.get("numero_os", "N/A")
        os_id = os_encontrada.get("id")

        # Validação: Técnico só pode dar baixa em suas OS
        display_name = st.session_state.get("display_name", "")
        if role == "tecnico" and os_encontrada.get("tecnico") != display_name:
            st.error("Você só pode dar baixa em suas próprias Ordens de Serviço.")
            st.warning(f"Esta OS está atribuída a: {os_encontrada.get('tecnico')}")
            limpar_estado_baixa()
            return

        st.markdown("---")
        st.success("✅ OS Encontrada para Dar Baixa!")

        # Exibir informações da OS (métricas)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Número", os_encontrada.get("numero_os", "N/A"))
        with col2:
            st.metric("Tipo", os_encontrada.get("tipo_os", "N/A"))
        with col3:
            st.metric("Status Atual", os_encontrada.get("status", "N/A"))

        # Informações detalhadas
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Secretaria:** {os_encontrada.get('secretaria', 'N/A')}")
            st.write(f"**Setor:** {os_encontrada.get('setor', 'N/A')}")
            st.write(f"**Técnico:** {os_encontrada.get('tecnico', 'N/A')}")
        with col2:
            st.write(f"**Equipamento:** {os_encontrada.get('equipamento', 'N/A')}")
            st.write(f"**Patrimônio:** {os_encontrada.get('patrimonio', 'N/A')}")
            st.write(f"**Solicitante:** {os_encontrada.get('solicitante', 'N/A')}")

        # Formatar data
        data_formatada = "N/A"
        if pd.notna(os_encontrada.get("data")):
            try:
                data_formatada = pd.to_datetime(os_encontrada.get("data")).strftime("%d/%m/%Y")
            except:
                data_formatada = str(os_encontrada.get("data"))
        st.write(f"**Data da OS:** {data_formatada}")

        # ✅ CORREÇÃO: text_area com KEY DINÂMICA por OS
        if os_encontrada.get("solicitacao_cliente"):
            st.markdown("**Solicitação do Cliente:**")
            st.text_area(
                "Solicitação",
                value=str(os_encontrada.get("solicitacao_cliente")),
                disabled=True,
                height=80,
                label_visibility="collapsed",
                key=f"text_solicitacao_baixa_{os_numero_display}_{os_id}"  # ✅ KEY ÚNICA
            )

        if os_encontrada.get("servico_executado"):
            st.markdown("**Serviço Executado:**")
            st.text_area(
                "Serviço",
                value=str(os_encontrada.get("servico_executado")),
                disabled=True,
                height=80,
                label_visibility="collapsed",
                key=f"text_servico_baixa_{os_numero_display}_{os_id}"  # ✅ KEY ÚNICA
            )

        st.markdown("---")
        st.markdown("### Registrar Baixa da OS")

        with st.form("form_dar_baixa"):
            col1, col2 = st.columns(2)

            with col1:
                # REGRA: Técnicos só podem finalizar
                if role == "tecnico":
                    status_options = ["FINALIZADO"]
                    status_novo = st.selectbox(
                        "Novo Status *",
                        status_options,
                        key="select_status_baixa_tecnico",
                    )
                    st.caption(
                        "Técnico: Ao salvar, o status será automaticamente alterado para 'AGUARDANDO RETIRADA'"
                    )
                else:
                    status_novo = st.selectbox(
                        "Novo Status *",
                        STATUS_OPTIONS,
                        index=(
                            STATUS_OPTIONS.index(os_encontrada.get("status", "EM ABERTO"))
                            if os_encontrada.get("status") in STATUS_OPTIONS
                            else 0
                        ),
                        key="select_status_baixa_admin",
                    )

            with col2:
                data_finalizacao = st.date_input(
                    "Data de Finalização *",
                    value=datetime.now().date(),
                    key="date_finalizacao_baixa",
                )

            observacoes_finalizacao = st.text_area(
                "Observações da Finalização / Serviço Executado *",
                value=os_encontrada.get("servico_executado", "") or "",
                height=150,
                placeholder="Descreva o serviço realizado ou observações sobre a finalização da OS...",
                key="textarea_obs_baixa",
            )

            # REGRA: Apenas admin/administrativo podem registrar retirada
            retirada_por = None
            data_retirada = None
            if role in ["admin", "administrativo"]:
                st.divider()
                st.markdown("#### Registro de Retirada (Apenas Admin/Administrativo)")
                retirada_por = st.text_input(
                    "Retirado por (Nome de quem retirou o equipamento)",
                    placeholder="Nome completo da pessoa que retirou",
                    key="input_retirada_por",
                )
                data_retirada = st.date_input(
                    "Data da Retirada",
                    value=datetime.now().date(),
                    key="date_retirada",
                )
            else:
                st.info("O registro de retirada será preenchido apenas por administradores.")

            st.markdown("---")
            col_btn1, col_btn2 = st.columns(2)

            submitted = col_btn1.form_submit_button(
                "Registrar Baixa",
                use_container_width=True,
                type="primary",
            )
            cancelar = col_btn2.form_submit_button(
                "Cancelar",
                use_container_width=True,
            )

            if submitted:
                # Validações
                if not status_novo or not data_finalizacao or not observacoes_finalizacao:
                    st.error("Preencha todos os campos obrigatórios (marcados com *).")
                else:
                    table_name = (
                        "os_interna"
                        if os_encontrada.get("tipo_os") == "Interna"
                        else "os_externa"
                    )
                    dados_baixa = {
                        "status": status_novo,
                        "data_finalizada": data_finalizacao if data_finalizacao else None,
                        "servico_executado": observacoes_finalizacao if observacoes_finalizacao else None,
                    }

                    # Adicionar retirada apenas para admin
                    if role in ["admin", "administrativo"] and retirada_por:
                        dados_baixa["retirada_por"] = retirada_por
                        dados_baixa["data_retirada"] = data_retirada

                    # REGRA: Admin finalizado → ENTREGUE AO CLIENTE
                    if status_novo == "FINALIZADO" and role in ["admin", "administrativo"]:
                        dados_baixa["status"] = "ENTREGUE AO CLIENTE"

                    if f_dar_baixa(conn, table_name, os_id, dados_baixa, role):
                        limpar_estado_baixa()
                        if role == "tecnico":
                            st.info("Redirecionando para Minhas Tarefas...")
                            st.session_state.current_page = "Minhas Tarefas"
                            st.rerun()
                        else:
                            st.rerun()

            if cancelar:
                limpar_estado_baixa()
                if role == "tecnico":
                    st.session_state.current_page = "Minhas Tarefas"
                    st.rerun()
                else:
                    st.rerun()

    else:
        st.info("🔍 Busque por uma OS para registrar a baixa.")

    st.markdown("---")

    # Botão para voltar
    if role == "tecnico":
        if st.button("Voltar para Minhas Tarefas", use_container_width=True):
            limpar_estado_baixa()
            st.session_state.current_page = "Minhas Tarefas"
            st.rerun()