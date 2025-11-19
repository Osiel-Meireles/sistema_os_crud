# CÓDIGO COMPLETO PARA: sistema_os_crud-main/recargas.py
import streamlit as st
import pandas as pd
from sqlalchemy import text
from database import get_connection, gerar_proximo_numero_recarga
from config import SECRETARIAS
from datetime import date, datetime
import math

STATUS_OPTIONS = ['Em análise', 'Enviado', 'Em recarga', 'Devolvido', 'Em uso', 'Sucata']
TIPO_INSUMO_OPTIONS = ['Cartucho', 'Toner']
COR_OPTIONS = ['Preto', 'Colorido', 'Cyan', 'Magenta', 'Yellow']

def get_impressoras(conn):
    try:
        with conn.connect() as con:
            query = text("""
                SELECT id, hostname, especificacao FROM equipamentos
                WHERE LOWER(categoria) LIKE '%impressora%' ORDER BY hostname
            """)
            result = con.execute(query).fetchall()
            return [(row[0], f"{row[1]} - {row[2][:50]}") for row in result]
    except Exception:
        return []

def f_registrar_recarga(conn, data):
    try:
        with conn.connect() as con:
            numero_recarga = gerar_proximo_numero_recarga(con)
            data['numero_recarga'] = numero_recarga
            data['registrado_por'] = st.session_state.get('username', 'Sistema')
            
            with con.begin():
                query = text("""
                    INSERT INTO recargas (
                        numero_recarga, data_solicitacao, data_envio, data_retorno,
                        status, secretaria, departamento, equipamento_id, equipamento_nome,
                        tipo_insumo, modelo_insumo, cor, quantidade,
                        fornecedor, valor_recarga, numero_nota,
                        numero_os, tipo_os, observacoes, registrado_por
                    ) VALUES (
                        :numero_recarga, :data_solicitacao, :data_envio, :data_retorno,
                        :status, :secretaria, :departamento, :equipamento_id, :equipamento_nome,
                        :tipo_insumo, :modelo_insumo, :cor, :quantidade,
                        :fornecedor, :valor_recarga, :numero_nota,
                        :numero_os, :tipo_os, :observacoes, :registrado_por
                    )
                """)
                con.execute(query, data)
        
        st.success(f"Recarga **{numero_recarga}** registrada com sucesso!")
        return True
    except Exception as e:
        st.error(f"Erro ao registrar recarga: {e}")
        return False

def f_atualizar_recarga(conn, data, recarga_id):
    try:
        data["id"] = recarga_id
        data["ultima_atualizacao"] = datetime.now()
        
        with conn.connect() as con:
            with con.begin():
                query = text("""
                    UPDATE recargas SET
                        data_solicitacao = :data_solicitacao, data_envio = :data_envio,
                        data_retorno = :data_retorno, status = :status,
                        secretaria = :secretaria, departamento = :departamento,
                        equipamento_id = :equipamento_id, equipamento_nome = :equipamento_nome,
                        tipo_insumo = :tipo_insumo, modelo_insumo = :modelo_insumo,
                        cor = :cor, quantidade = :quantidade,
                        fornecedor = :fornecedor, valor_recarga = :valor_recarga,
                        numero_nota = :numero_nota, numero_os = :numero_os,
                        tipo_os = :tipo_os, observacoes = :observacoes,
                        ultima_atualizacao = :ultima_atualizacao
                    WHERE id = :id
                """)
                con.execute(query, data)
        
        st.success(f"Recarga (ID: {recarga_id}) atualizada com sucesso!")
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar recarga: {e}")
        return False

def f_deletar_recarga(conn, recarga_id):
    try:
        with conn.connect() as con:
            with con.begin():
                con.execute(text("DELETE FROM recargas WHERE id = :id"), {"id": recarga_id})
        st.success(f"Recarga (ID: {recarga_id}) deletada com sucesso.")
        return True
    except Exception as e:
        st.error(f"Erro ao deletar recarga: {e}")
        return False

def get_recarga_by_id(conn, recarga_id):
    try:
        with conn.connect() as con:
            result = con.execute(text("SELECT * FROM recargas WHERE id = :id"), {"id": recarga_id}).fetchone()
            return result._mapping if result else None
    except Exception:
        return None

@st.dialog("Detalhes da Recarga", width="large")
def show_recarga_details(recarga_data):
    st.markdown(f"### Recarga Nº {recarga_data.get('numero_recarga', 'N/A')}")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Status", recarga_data.get('status', 'N/A'))
    with col2:
        st.metric("Tipo", recarga_data.get('tipo_insumo', 'N/A'))
    with col3:
        st.metric("Cor", recarga_data.get('cor', 'N/A'))
    with col4:
        st.metric("Quantidade", recarga_data.get('quantidade', 0))
    
    st.markdown("---")
    st.markdown("#### Datas")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.text_input("Data de Solicitação", value=str(recarga_data.get('data_solicitacao') or 'N/A'), disabled=True)
    with col2:
        st.text_input("Data de Envio", value=str(recarga_data.get('data_envio') or 'N/A'), disabled=True)
    with col3:
        st.text_input("Data de Retorno", value=str(recarga_data.get('data_retorno') or 'N/A'), disabled=True)
    
    st.markdown("#### Localização")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.text_input("Secretaria", value=str(recarga_data.get('secretaria') or 'N/A'), disabled=True)
    with col2:
        st.text_input("Departamento", value=str(recarga_data.get('departamento') or 'N/A'), disabled=True)
    with col3:
        st.text_input("Equipamento", value=str(recarga_data.get('equipamento_nome') or 'N/A'), disabled=True)
    
    st.markdown("#### Insumo")
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("Modelo do Insumo", value=str(recarga_data.get('modelo_insumo') or 'N/A'), disabled=True)
        st.text_input("Tipo", value=str(recarga_data.get('tipo_insumo') or 'N/A'), disabled=True)
    with col2:
        st.text_input("Cor", value=str(recarga_data.get('cor') or 'N/A'), disabled=True, key="cor_detail")
        st.text_input("Quantidade", value=str(recarga_data.get('quantidade') or 'N/A'), disabled=True)
    
    st.markdown("#### Financeiro")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.text_input("Fornecedor", value=str(recarga_data.get('fornecedor') or 'N/A'), disabled=True)
    with col2:
        valor = recarga_data.get('valor_recarga')
        valor_str = f"R$ {float(valor):.2f}" if valor else 'N/A'
        st.text_input("Valor da Recarga", value=valor_str, disabled=True)
    with col3:
        st.text_input("Nº da Nota", value=str(recarga_data.get('numero_nota') or 'N/A'), disabled=True)
    
    if recarga_data.get('numero_os'):
        st.markdown("#### Ordem de Serviço Vinculada")
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("Nº da OS", value=str(recarga_data.get('numero_os') or 'N/A'), disabled=True)
        with col2:
            st.text_input("Tipo da OS", value=str(recarga_data.get('tipo_os') or 'N/A'), disabled=True)
    
    if recarga_data.get('observacoes'):
        st.markdown("#### Observações")
        st.text_area("", value=recarga_data.get('observacoes'), height=100, disabled=True, label_visibility="collapsed")
    
    st.markdown("#### Metadados")
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"**Registrado por:** {recarga_data.get('registrado_por', 'N/A')}")
    with col2:
        st.info(f"**Data de Registro:** {recarga_data.get('data_registro', 'N/A')}")
    
    if st.button("Fechar", use_container_width=True, type="secondary"):
        st.rerun()

def render_tab_registro(conn):
    edit_id = st.session_state.get('edit_recarga_id')
    form_title = "Atualizar Recarga" if edit_id else "Registrar Nova Recarga"
    button_label = "Salvar Alterações" if edit_id else "Registrar Recarga"
    
    default_data = {}
    if edit_id and 'form_data' not in st.session_state:
        default_data = get_recarga_by_id(conn, edit_id) or {}
    
    form_data = st.session_state.get('form_data', default_data)
    
    st.markdown(f"### {form_title}")
    
    if edit_id:
        st.info(f"Editando recarga ID: **{edit_id}** | Número: **{form_data.get('numero_recarga', 'N/A')}**")
    
    with st.form("recarga_form"):
        st.markdown("#### 1. Datas e Status")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            data_solicitacao = st.date_input("Data de Solicitação *", value=form_data.get('data_solicitacao') or date.today())
        with col2:
            data_envio = st.date_input("Data de Envio", value=form_data.get('data_envio') if form_data.get('data_envio') else None)
        with col3:
            data_retorno = st.date_input("Data de Retorno", value=form_data.get('data_retorno') if form_data.get('data_retorno') else None)
        with col4:
            status = st.selectbox("Status *", STATUS_OPTIONS, index=STATUS_OPTIONS.index(form_data.get('status', 'Em análise')))
        
        st.markdown("#### 2. Localização")
        secretarias = sorted(SECRETARIAS)
        
        col1, col2 = st.columns(2)
        with col1:
            secretaria = st.selectbox(
                "Secretaria *",
                secretarias,
                index=secretarias.index(form_data.get('secretaria')) if form_data.get('secretaria') in secretarias else 0
            )
        
        with col2:
            departamento = st.text_input(
                "Departamento",
                value=form_data.get('departamento', ''),
                placeholder="Ex: TI, Administrativo"
            )
        
        impressoras = get_impressoras(conn)
        impressoras_dict = {imp[0]: imp[1] for imp in impressoras}
        impressoras_options = [''] + list(impressoras_dict.values())
        
        col1, col2 = st.columns(2)
        with col1:
            current_equip_id = form_data.get('equipamento_id')
            current_equip_idx = 0
            if current_equip_id and current_equip_id in impressoras_dict:
                current_equip_idx = impressoras_options.index(impressoras_dict[current_equip_id])
            
            equipamento_selecionado = st.selectbox("Equipamento/Impressora", impressoras_options, index=current_equip_idx)
        
        with col2:
            equipamento_nome_manual = st.text_input("Ou digite o nome manualmente", value=form_data.get('equipamento_nome', '') if not equipamento_selecionado else '')
        
        st.markdown("#### 3. Insumo")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            tipo_insumo = st.selectbox("Tipo *", TIPO_INSUMO_OPTIONS, index=TIPO_INSUMO_OPTIONS.index(form_data.get('tipo_insumo', 'Cartucho')))
        with col2:
            cor = st.selectbox("Cor *", COR_OPTIONS, index=COR_OPTIONS.index(form_data.get('cor', 'Preto')))
        with col3:
            quantidade = st.number_input("Quantidade *", min_value=1, value=form_data.get('quantidade', 1))
        with col4:
            modelo_insumo = st.text_input("Modelo do Insumo *", value=form_data.get('modelo_insumo', ''), placeholder="Ex: HP 664 Preto")
        
        st.markdown("#### 4. Financeiro")
        col1, col2, col3 = st.columns(3)
        with col1:
            fornecedor = st.text_input("Fornecedor", value=form_data.get('fornecedor', ''), placeholder="Ex: Recarga Express")
        with col2:
            valor_recarga = st.number_input("Valor da Recarga (R$)", min_value=0.0, format="%.2f", value=float(form_data.get('valor_recarga', 0)) if form_data.get('valor_recarga') else 0.0)
        with col3:
            numero_nota = st.text_input("Nº da Nota/Recibo", value=form_data.get('numero_nota', ''), placeholder="Ex: NF-12345")
        
        st.markdown("#### 5. Vínculo com OS (Opcional)")
        col1, col2 = st.columns(2)
        with col1:
            numero_os = st.text_input("Nº da OS", value=form_data.get('numero_os', ''), placeholder="Ex: 123-25")
        with col2:
            tipo_os = st.selectbox("Tipo da OS", ['', 'Interna', 'Externa'], index=(['', 'Interna', 'Externa'].index(form_data.get('tipo_os', ''))))
        
        st.markdown("#### 6. Observações")
        observacoes = st.text_area("Observações", value=form_data.get('observacoes', ''), height=100, placeholder="Informações adicionais...")
        
        submitted = st.form_submit_button(button_label, use_container_width=True, type="primary")
        
        if submitted:
            equip_id = None
            equip_nome = equipamento_nome_manual
            
            if equipamento_selecionado:
                for imp_id, imp_nome in impressoras_dict.items():
                    if imp_nome == equipamento_selecionado:
                        equip_id = imp_id
                        equip_nome = imp_nome
                        break
            
            data = {
                "data_solicitacao": data_solicitacao,
                "data_envio": data_envio if data_envio else None,
                "data_retorno": data_retorno if data_retorno else None,
                "status": status,
                "secretaria": secretaria,
                "departamento": departamento or None,
                "equipamento_id": equip_id,
                "equipamento_nome": equip_nome or None,
                "tipo_insumo": tipo_insumo,
                "modelo_insumo": modelo_insumo,
                "cor": cor,
                "quantidade": quantidade,
                "fornecedor": fornecedor or None,
                "valor_recarga": valor_recarga if valor_recarga > 0 else None,
                "numero_nota": numero_nota or None,
                "numero_os": numero_os or None,
                "tipo_os": tipo_os or None,
                "observacoes": observacoes or None,
            }
            
            erros = []
            if not secretaria:
                erros.append("O campo 'Secretaria' é obrigatório.")
            if not modelo_insumo:
                erros.append("O campo 'Modelo do Insumo' é obrigatório.")
            
            if erros:
                for erro in erros:
                    st.error(erro)
                st.session_state.form_data = data
            else:
                success = False
                if edit_id:
                    success = f_atualizar_recarga(conn, data, edit_id)
                else:
                    success = f_registrar_recarga(conn, data)
                
                if success:
                    if 'form_data' in st.session_state:
                        del st.session_state.form_data
                    if 'edit_recarga_id' in st.session_state:
                        del st.session_state.edit_recarga_id
                    st.rerun()
    
    if edit_id:
        if st.button("Cancelar Edição", use_container_width=True):
            if 'form_data' in st.session_state:
                del st.session_state.form_data
            if 'edit_recarga_id' in st.session_state:
                del st.session_state.edit_recarga_id
            st.rerun()

def render_tab_consulta(conn):
    st.markdown("### Consulta de Recargas")
    
    try:
        with conn.connect() as con:
            total_count = con.execute(text("SELECT COUNT(*) FROM recargas")).scalar()
            status_counts = con.execute(text("""
                SELECT status, COUNT(*) as count FROM recargas
                GROUP BY status ORDER BY count DESC
            """)).fetchall()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total de Recargas", total_count)
        with col2:
            em_andamento = sum([row[1] for row in status_counts if row[0] in ['Em análise', 'Enviado', 'Em recarga']])
            st.metric("Em Andamento", em_andamento)
        with col3:
            concluidas = sum([row[1] for row in status_counts if row[0] in ['Devolvido', 'Em uso']])
            st.metric("Concluídas", concluidas)
        with col4:
            sucata = sum([row[1] for row in status_counts if row[0] == 'Sucata'])
            st.metric("Sucata", sucata)
        
    except Exception as e:
        st.error(f"Erro ao buscar estatísticas: {e}")
        return
    
    if total_count == 0:
        st.warning("Nenhuma recarga encontrada no banco de dados. Registre a primeira recarga!")
        return
    
    with st.expander("Aplicar Filtros", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            f_status = st.multiselect("Filtrar por Status", STATUS_OPTIONS)
            f_secretaria = st.multiselect("Filtrar por Secretaria", sorted(SECRETARIAS))
        with col2:
            f_tipo = st.multiselect("Filtrar por Tipo de Insumo", TIPO_INSUMO_OPTIONS)
            f_cor = st.multiselect("Filtrar por Cor", COR_OPTIONS)
        with col3:
            f_numero = st.text_input("Pesquisar por Nº da Recarga")
            f_modelo = st.text_input("Pesquisar por Modelo do Insumo")
    
    query_base = "SELECT * FROM recargas"
    where_clauses = []
    params = {}
    
    if f_status:
        placeholders = ','.join([f":st{i}" for i in range(len(f_status))])
        where_clauses.append(f"status IN ({placeholders})")
        for i, st_val in enumerate(f_status):
            params[f"st{i}"] = st_val
    
    if f_secretaria:
        placeholders = ','.join([f":sec{i}" for i in range(len(f_secretaria))])
        where_clauses.append(f"secretaria IN ({placeholders})")
        for i, sec in enumerate(f_secretaria):
            params[f"sec{i}"] = sec
    
    if f_tipo:
        placeholders = ','.join([f":tipo{i}" for i in range(len(f_tipo))])
        where_clauses.append(f"tipo_insumo IN ({placeholders})")
        for i, tipo in enumerate(f_tipo):
            params[f"tipo{i}"] = tipo
    
    if f_cor:
        placeholders = ','.join([f":cor{i}" for i in range(len(f_cor))])
        where_clauses.append(f"cor IN ({placeholders})")
        for i, cor_val in enumerate(f_cor):
            params[f"cor{i}"] = cor_val
    
    if f_numero:
        where_clauses.append("numero_recarga ILIKE :numero")
        params["numero"] = f"%{f_numero}%"
    
    if f_modelo:
        where_clauses.append("modelo_insumo ILIKE :modelo")
        params["modelo"] = f"%{f_modelo}%"
    
    if where_clauses:
        query_base += " WHERE " + " AND ".join(where_clauses)
    
    if 'recarga_page' not in st.session_state:
        st.session_state.recarga_page = 1
    
    ITEMS_PER_PAGE = 10
    
    try:
        count_query = f"SELECT COUNT(*) FROM ({query_base}) as sub"
        with conn.connect() as con:
            total_items = con.execute(text(count_query), params).scalar()
    except Exception as e:
        st.error(f"Erro ao contar recargas: {e}")
        return
    
    if total_items == 0:
        st.info("Nenhuma recarga encontrada com os filtros aplicados.")
        return
    
    total_pages = math.ceil(total_items / ITEMS_PER_PAGE)
    
    if st.session_state.recarga_page > total_pages:
        st.session_state.recarga_page = total_pages
    if st.session_state.recarga_page < 1:
        st.session_state.recarga_page = 1
    
    offset = (st.session_state.recarga_page - 1) * ITEMS_PER_PAGE
    query_final = f"{query_base} ORDER BY data_registro DESC LIMIT {ITEMS_PER_PAGE} OFFSET {offset}"
    
    try:
        with conn.connect() as con:
            result = con.execute(text(query_final), params)
            rows = result.fetchall()
            columns = result.keys()
            df_recargas = pd.DataFrame(rows, columns=columns)
        
        st.info(f"Exibindo **{len(df_recargas)}** de **{total_items}** recargas (Página {st.session_state.recarga_page}/{total_pages})")
        
        st.markdown("---")
        
        cols_header = st.columns((1, 1.5, 1.5, 1.5, 1.5, 2, 2))
        headers = ["Nº Recarga", "Data Solicit.", "Status", "Secretaria", "Tipo", "Modelo (resumo)", "Ações"]
        
        for col, header in zip(cols_header, headers):
            col.markdown(f"**{header}**")
        
        st.markdown("<hr style='margin-top: 0; margin-bottom: 0;'>", unsafe_allow_html=True)
        
        for idx, row in df_recargas.iterrows():
            recarga_id = row['id']
            cols_row = st.columns((1, 1.5, 1.5, 1.5, 1.5, 2, 2))
            
            cols_row[0].write(str(row.get('numero_recarga', 'N/A')))
            cols_row[1].write(str(row.get('data_solicitacao', 'N/A')))
            cols_row[2].write(str(row.get('status', 'N/A')))
            cols_row[3].write(str(row.get('secretaria', 'N/A')))
            cols_row[4].write(str(row.get('tipo_insumo', 'N/A')))
            
            modelo = str(row.get('modelo_insumo', 'N/A'))
            modelo_resumido = modelo[:25] + "..." if len(modelo) > 25 else modelo
            cols_row[5].write(modelo_resumido)
            
            action_col = cols_row[6]
            col_b1, col_b2, col_b3 = action_col.columns(3)
            
            if col_b1.button("👁️", key=f"view_{recarga_id}_{idx}", use_container_width=True, help="Visualizar"):
                show_recarga_details(dict(row))
            
            if col_b2.button("✏️", key=f"edit_{recarga_id}_{idx}", use_container_width=True, help="Editar"):
                st.session_state.edit_recarga_id = recarga_id
                if 'form_data' in st.session_state:
                    del st.session_state.form_data
                st.rerun()
            
            if col_b3.button("🗑️", key=f"del_{recarga_id}_{idx}", use_container_width=True, type="secondary", help="Deletar"):
                st.session_state.delete_recarga_id = recarga_id
                st.session_state.delete_recarga_data = dict(row)
                st.rerun()
            
            st.markdown("<hr style='margin-top: 0; margin-bottom: 0;'>", unsafe_allow_html=True)
        
        st.markdown("---")
        if total_pages > 1:
            col_nav1, col_nav2, col_nav3 = st.columns([1, 1, 1])
            
            if col_nav1.button("← Anterior", key="prev_recarga", disabled=(st.session_state.recarga_page <= 1)):
                st.session_state.recarga_page -= 1
                st.rerun()
            
            col_nav2.markdown(f"**Página {st.session_state.recarga_page} de {total_pages}**")
            
            if col_nav3.button("Próxima →", key="next_recarga", disabled=(st.session_state.recarga_page >= total_pages)):
                st.session_state.recarga_page += 1
                st.rerun()
    
    except Exception as e:
        st.error(f"Erro ao consultar recargas: {e}")
        st.exception(e)

def render_delete_confirmation(conn):
    if 'delete_recarga_id' in st.session_state:
        recarga_id = st.session_state.delete_recarga_id
        recarga_data = st.session_state.get('delete_recarga_data', {})
        
        st.warning("Confirmação de Exclusão")
        st.write(f"Tem certeza que deseja deletar a recarga **{recarga_data.get('numero_recarga', 'N/A')}**?")
        
        col1, col2 = st.columns(2)
        if col1.button("Sim, Deletar", type="primary", use_container_width=True):
            if f_deletar_recarga(conn, recarga_id):
                del st.session_state.delete_recarga_id
                if 'delete_recarga_data' in st.session_state:
                    del st.session_state.delete_recarga_data
                st.rerun()
        
        if col2.button("Cancelar", use_container_width=True):
            del st.session_state.delete_recarga_id
            if 'delete_recarga_data' in st.session_state:
                del st.session_state.delete_recarga_data
            st.rerun()

def render():
    conn = get_connection()
    st.title("Gerenciamento de Recargas de Impressora")
    
    render_delete_confirmation(conn)
    
    tab1, tab2 = st.tabs(["Registro de Recargas", "Consulta de Recargas"])
    
    with tab1:
        render_tab_registro(conn)
    
    with tab2:
        render_tab_consulta(conn)