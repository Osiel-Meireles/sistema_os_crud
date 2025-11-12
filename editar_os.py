# CÓDIGO COMPLETO PARA O NOVO ARQUIVO: sistema_os_crud-main/editar_os.py

import streamlit as st
import pandas as pd
from sqlalchemy import text
from datetime import date, datetime, time
import pytz

from database import get_connection
from config import SECRETARIAS, TECNICOS, CATEGORIAS, EQUIPAMENTOS

def f_get_os_data(conn, os_id, os_type):
    """Busca os dados de uma OS específica para edição."""
    table_name = "os_interna" if os_type == "Interna" else "os_externa"
    try:
        with conn.connect() as con:
            query = text(f"SELECT * FROM {table_name} WHERE id = :id")
            result = con.execute(query, {"id": os_id}).fetchone()
            return result._mapping if result else None
    except Exception as e:
        st.error(f"Erro ao carregar dados da OS: {e}")
        return None

def f_atualizar_os(conn, data, os_id, os_type):
    """Atualiza uma OS existente no banco de dados."""
    table_name = "os_interna" if os_type == "Interna" else "os_externa"
    try:
        with conn.connect() as con:
            with con.begin():
                query = text(f"""
                    UPDATE {table_name}
                    SET 
                        secretaria = :secretaria,
                        setor = :setor,
                        solicitante = :solicitante,
                        telefone = :telefone,
                        solicitacao_cliente = :solicitacao_cliente,
                        categoria = :categoria,
                        patrimonio = :patrimonio,
                        equipamento = :equipamento,
                        tecnico = :tecnico,
                        data = :data,
                        hora = :hora
                    WHERE id = :id
                """)
                data['id'] = os_id
                con.execute(query, data)
        st.success("Ordem de Serviço atualizada com sucesso!")
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar a OS: {e}")
        return False

def render():
    st.markdown("<h3 style='text-align: left;'>Editar Ordem de Serviço</h3>", unsafe_allow_html=True)
    conn = get_connection()

    # 1. Recupera os dados da OS a ser editada
    if 'edit_os_data' not in st.session_state or not st.session_state.edit_os_data:
        st.error("Nenhuma Ordem de Serviço selecionada para edição.")
        if st.button("Voltar para Filtros"):
            st.session_state.page = "Filtrar OS"
            st.rerun()
        return

    edit_data = st.session_state.edit_os_data
    os_id = edit_data['id']
    os_type = edit_data['tipo'] # "Interna" ou "Externa"
    
    # 2. Carrega os dados do banco se não estiverem no state (1ª carga)
    if 'form_data' not in st.session_state:
        default_data = f_get_os_data(conn, os_id, os_type)
        if not default_data:
            st.error("Não foi possível carregar os dados da OS. Ela pode ter sido deletada.")
            st.session_state.page = "Filtrar OS"
            st.rerun()
            return
        st.session_state.form_data = dict(default_data)
    
    form_data = st.session_state.form_data
    
    # Listas de seleção
    secretarias_sorted = sorted(SECRETARIAS)
    tecnicos_sorted = sorted(TECNICOS)
    categorias_sorted = sorted(CATEGORIAS)
    equipamentos_sorted = sorted(EQUIPAMENTOS)

    # Helper para encontrar o índice correto nos selectbox
    def get_index(lista, valor):
        try: return lista.index(valor)
        except (ValueError, TypeError): return None

    st.info(f"Você está editando a OS **{form_data.get('numero')}** (Tipo: {os_type})")
    
    # 3. Renderiza o formulário
    with st.form("edit_os_form"):
        col1, col2 = st.columns(2)

        with col1:
            secretaria = st.selectbox(
                "Secretaria *", secretarias_sorted, 
                index=get_index(secretarias_sorted, form_data.get('secretaria')),
                placeholder="Selecione a secretaria..."
            )
            solicitante = st.text_input("Solicitante *", value=form_data.get('solicitante', ''))
            solicitacao_cliente = st.text_area("Solicitação do Cliente *", value=form_data.get('solicitacao_cliente', ''))
            patrimonio = st.text_input("Número do Patrimônio", value=form_data.get('patrimonio', ''))
            tecnico = st.selectbox(
                "Técnico *", tecnicos_sorted,
                index=get_index(tecnicos_sorted, form_data.get('tecnico')),
                placeholder="Selecione o técnico..."
            )
            data = st.date_input("Data de Entrada", value=pd.to_datetime(form_data.get('data')), format="DD/MM/YYYY")

        with col2:
            setor = st.text_input("Setor *", value=form_data.get('setor', ''))
            telefone = st.text_input("Telefone *", value=form_data.get('telefone', ''))
            categoria = st.selectbox(
                "Categoria do Serviço *", categorias_sorted,
                index=get_index(categorias_sorted, form_data.get('categoria')),
                placeholder="Selecione a categoria..."
            )
            equipamento = st.selectbox(
                "Equipamento *", equipamentos_sorted,
                index=get_index(equipamentos_sorted, form_data.get('equipamento')),
                placeholder="Selecione o equipamento..."
            )
            # Converte 'hora' de string (se for) para objeto time
            hora_val = form_data.get('hora')
            if isinstance(hora_val, str):
                try:
                    hora_val = datetime.strptime(hora_val, '%H:%M:%S').time()
                except ValueError:
                    hora_val = time(12, 0) # Padrão se a conversão falhar
            
            hora = st.time_input("Hora de Entrada", value=hora_val)
        
        submitted = st.form_submit_button("Salvar Alterações", use_container_width=True, type='primary')
        
        if submitted:
            # 4. Validação e Submissão
            data_payload = {
                "secretaria": secretaria, "solicitante": solicitante, "solicitacao_cliente": solicitacao_cliente,
                "patrimonio": patrimonio, "tecnico": tecnico, "data": data, "setor": setor,
                "telefone": telefone, "categoria": categoria, "equipamento": equipamento, "hora": hora
            }

            if not all([setor, solicitante, telefone, solicitacao_cliente]):
                st.error("Por favor, preencha todos os campos marcados com * (Setor, Solicitante, Telefone, Solicitação).")
            elif not all([secretaria, tecnico, categoria, equipamento]):
                st.error("Por favor, selecione uma secretaria, técnico, categoria e equipamento válidos.")
            else:
                if f_atualizar_os(conn, data_payload, os_id, os_type):
                    # Limpa o state e redireciona
                    del st.session_state.edit_os_data
                    if 'form_data' in st.session_state:
                        del st.session_state.form_data
                    st.session_state.page = "Filtrar OS"
                    st.rerun()
                else:
                    # Salva os dados do formulário no state para repopular
                    st.session_state.form_data = data_payload
    
    if st.button("Cancelar Edição", use_container_width=True):
        del st.session_state.edit_os_data
        if 'form_data' in st.session_state:
            del st.session_state.form_data
        st.session_state.page = "Filtrar OS"
        st.rerun()