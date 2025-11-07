# CÓDIGO ATUALIZADO PARA: sistema_os_crud-main/equipamentos.py

import streamlit as st
import pandas as pd
from sqlalchemy import text
from database import get_connection
from config import SECRETARIAS, CATEGORIAS_EQUIP
import re
import math

# --- ALTERAÇÃO AQUI: Lógica de lista simplificada ---
SECRETARIAS_EQUIP = sorted(SECRETARIAS)
# --- FIM DA ALTERAÇÃO ---

# --- Funções de Validação (inalteradas) ---
def is_valid_ip(ip):
    if not ip: return True 
    return re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip)
def is_valid_mac(mac):
    if not mac: return True 
    return re.match(r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$", mac)
def is_valid_cidr(cidr):
    if not cidr: return True 
    return re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2}$", cidr)
def check_duplicate(conn, field, value, current_id=None):
    if not value:
        return False 
    query_base = f"SELECT id FROM equipamentos WHERE {field} = :value"
    params = {"value": value}
    if current_id:
        query_base += " AND id != :id"
        params["id"] = current_id
    try:
        with conn.connect() as con:
            result = con.execute(text(query_base), params).fetchone()
        return bool(result)
    except Exception as e:
        st.error(f"Erro ao verificar duplicidade de {field}: {e}")
        return True 
def normalize_mac(mac):
    if not mac:
        return None
    mac_normalized = mac.replace('-', ':').upper()
    return mac_normalized

# --- Funções de CRUD (inalteradas) ---
def f_registrar_equipamento(conn, data):
    try:
        with conn.connect() as con:
            with con.begin():
                query = text("""
                    INSERT INTO equipamentos (
                        categoria, patrimonio, hostname, especificacao, secretaria, setor,
                        localizacao_fisica, ip, mac, subrede, gateway, dns, numero_serie, observacoes
                    ) VALUES (
                        :categoria, :patrimonio, :hostname, :especificacao, :secretaria, :setor,
                        :localizacao_fisica, :ip, :mac, :subrede, :gateway, :dns, :numero_serie, :observacoes
                    )
                """)
                con.execute(query, data)
        st.success(f"Equipamento '{data['hostname']}' registrado com sucesso!")
        return True
    except Exception as e:
        st.error(f"Erro ao registrar equipamento: {e}")
        return False
def f_atualizar_equipamento(conn, data, equip_id):
    try:
        data["id"] = equip_id
        with conn.connect() as con:
            with con.begin():
                query = text("""
                    UPDATE equipamentos SET
                        categoria = :categoria, patrimonio = :patrimonio, hostname = :hostname,
                        especificacao = :especificacao, secretaria = :secretaria, setor = :setor,
                        localizacao_fisica = :localizacao_fisica, ip = :ip, mac = :mac,
                        subrede = :subrede, gateway = :gateway, dns = :dns,
                        numero_serie = :numero_serie, observacoes = :observacoes
                    WHERE id = :id
                """)
                con.execute(query, data)
        st.success(f"Equipamento '{data['hostname']}' (ID: {equip_id}) atualizado com sucesso!")
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar equipamento: {e}")
        return False
def f_deletar_equipamento(conn, equip_id):
    try:
        with conn.connect() as con:
            with con.begin():
                con.execute(text("DELETE FROM equipamentos WHERE id = :id"), {"id": equip_id})
        st.success(f"Equipamento (ID: {equip_id}) deletado com sucesso.")
        return True
    except Exception as e:
        st.error(f"Erro ao deletar equipamento: {e}")
        return False
def get_equip_by_id(conn, equip_id):
    try:
        with conn.connect() as con:
            result = con.execute(text("SELECT * FROM equipamentos WHERE id = :id"), {"id": equip_id}).fetchone()
        return result._mapping if result else None
    except Exception:
        return None

# --- Componentes da UI ---
def render_form_equipamento(conn):
    """Renderiza o formulário de registro/edição."""
    
    edit_id = st.session_state.get('edit_equip_id')
    form_title = "Atualizar Equipamento" if edit_id else "Registrar Novo Equipamento"
    button_label = "Salvar Alterações" if edit_id else "Registrar Equipamento"
    
    default_data = {}
    if edit_id and 'form_data' not in st.session_state: 
        default_data = get_equip_by_id(conn, edit_id) or {}
    
    form_data = st.session_state.get('form_data', default_data)
    
    def get_index(lista, valor):
        try: return lista.index(valor)
        except (ValueError, TypeError): return None # Retorna None para o placeholder funcionar
    
    with st.form("equip_form"):
        st.markdown(f"#### {form_title}")

        st.markdown("**1. Identificação do Equipamento**")
        col1, col2 = st.columns(2)
        with col1:
            # --- ALTERAÇÃO AQUI: Placeholder e index=None ---
            categoria = st.selectbox(
                "Categoria *", sorted(CATEGORIAS_EQUIP), 
                index=get_index(sorted(CATEGORIAS_EQUIP), form_data.get('categoria')),
                placeholder="Selecione a categoria..."
            )
            # --- FIM DA ALTERAÇÃO ---
        with col2:
            patrimonio = st.text_input("Patrimônio", placeholder="Ex: PAT-2024-001", 
                                       value=form_data.get('patrimonio', ''))
            
        hostname = st.text_input("Hostname *", placeholder="Ex: COMP-ADM-01", 
                                 value=form_data.get('hostname', ''))
        especificacao = st.text_area("Modelo/Especificação *", 
                                     placeholder="Ex: Dell Optiplex 7010 - Intel i5, 8GB RAM, SSD 256GB", 
                                     height=100, value=form_data.get('especificacao', ''))

        st.markdown("**2. Localização**")
        col1, col2 = st.columns(2)
        with col1:
            # --- ALTERAÇÃO AQUI: Placeholder e index=None ---
            secretaria = st.selectbox(
                "Secretaria *", SECRETARIAS_EQUIP, # Já está ordenada
                index=get_index(SECRETARIAS_EQUIP, form_data.get('secretaria')),
                placeholder="Selecione a secretaria..."
            )
            # --- FIM DA ALTERAÇÃO ---
        with col2:
            setor = st.text_input("Setor", placeholder="Ex: TI, Administrativo, Recepção",
                                  value=form_data.get('setor', ''))
        
        localizacao_fisica = st.text_input("Localização Física", placeholder="Ex: Sala 101, Andar 2",
                                           value=form_data.get('localizacao_fisica', ''))

        st.markdown("**3. Rede (Opcional)**")
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            ip = st.text_input("Endereço IP", placeholder="Ex: 192.168.1.100", 
                               value=form_data.get('ip', ''))
            mac = st.text_input("MAC Address", placeholder="Ex: AA:BB:CC:DD:EE:FF", 
                                value=form_data.get('mac', ''))
            subrede = st.text_input("Sub-rede", placeholder="Ex: 192.168.1.0/24", 
                                    value=form_data.get('subrede', ''))
        with col_r2:
            gateway = st.text_input("Gateway", placeholder="Ex: 192.168.1.1", 
                                    value=form_data.get('gateway', ''))
            dns = st.text_input("DNS", placeholder="Ex: 8.8.8.8", 
                                value=form_data.get('dns', ''))

        st.markdown("**4. Informações Adicionais (Opcional)**")
        numero_serie = st.text_input("Número de Série", placeholder="Ex: SN123456789", 
                                     value=form_data.get('numero_serie', ''))
        observacoes = st.text_area("Observações", 
                                   placeholder="Informações adicionais sobre o equipamento", 
                                   height=100, value=form_data.get('observacoes', ''))
        
        submitted = st.form_submit_button(button_label, use_container_width=True, type="primary")

        if submitted:
            mac_norm = normalize_mac(mac)
            data = {
                "categoria": categoria, "patrimonio": patrimonio or None, "hostname": hostname,
                "especificacao": especificacao, "secretaria": secretaria, "setor": setor or None,
                "localizacao_fisica": localizacao_fisica or None, "ip": ip or None, "mac": mac_norm,
                "subrede": subrede or None, "gateway": gateway or None, "dns": dns or None,
                "numero_serie": numero_serie or None, "observacoes": observacoes or None,
            }
            
            # --- ALTERAÇÃO AQUI: Validação simplificada ---
            erros = []
            if not categoria:
                erros.append("O campo 'Categoria' é obrigatório.")
            if not hostname:
                erros.append("O campo 'Hostname' é obrigatório.")
            if not especificacao:
                erros.append("O campo 'Modelo/Especificação' é obrigatório.")
            if not secretaria:
                erros.append("O campo 'Secretaria' é obrigatório.")
            # --- FIM DA ALTERAÇÃO ---

            if ip and not is_valid_ip(ip):
                erros.append(f"Formato de IP inválido: {ip}")
            if mac and not is_valid_mac(mac_norm): 
                erros.append(f"Formato de MAC Address inválido: {mac}")
            if subrede and not is_valid_cidr(subrede):
                erros.append(f"Formato de Sub-rede (CIDR) inválido: {subrede}")
            if gateway and not is_valid_ip(gateway):
                erros.append(f"Formato de Gateway inválido: {gateway}")
            if dns and not is_valid_ip(dns):
                erros.append(f"Formato de DNS inválido: {dns}")

            if not erros:
                if check_duplicate(conn, "ip", ip, edit_id):
                    erros.append(f"O Endereço IP '{ip}' já está em uso.")
                if check_duplicate(conn, "mac", mac_norm, edit_id):
                    erros.append(f"O MAC Address '{mac_norm}' já está em uso.")

            if erros:
                for erro in erros:
                    st.error(erro)
                st.session_state.form_data = data
            else:
                success = False
                if edit_id:
                    success = f_atualizar_equipamento(conn, data, edit_id)
                else:
                    success = f_registrar_equipamento(conn, data)
                
                if success:
                    if 'form_data' in st.session_state: del st.session_state.form_data
                    if 'edit_equip_id' in st.session_state: del st.session_state.edit_equip_id
                    st.rerun()

    if edit_id:
        if st.button("Cancelar Edição", use_container_width=True):
            if 'form_data' in st.session_state: del st.session_state.form_data
            if 'edit_equip_id' in st.session_state: del st.session_state.edit_equip_id
            st.rerun()


def render_consulta_equipamentos(conn):
    """Renderiza os filtros e a tabela de consulta."""
    st.markdown("#### 5. Consulta de Equipamentos")

    with st.expander("Aplicar Filtros"):
        col1, col2 = st.columns(2)
        with col1:
            # --- ALTERAÇÃO AQUI: Lógica de lista simplificada ---
            f_categoria = st.multiselect("Filtrar por Categoria", sorted(CATEGORIAS_EQUIP))
            f_secretaria = st.multiselect("Filtrar por Secretaria", SECRETARIAS_EQUIP)
            # --- FIM DA ALTERAÇÃO ---
        with col2:
            f_hostname = st.text_input("Pesquisar por Hostname")
            f_ip = st.text_input("Pesquisar por IP")
    
    # ... (lógica de SQL, paginação e tabela permanecem inalteradas) ...
    query_base = "SELECT id, hostname, categoria, secretaria, ip, mac, especificacao FROM equipamentos"
    where_clauses = []
    params = {}

    if f_categoria:
        where_clauses.append("categoria IN :categoria")
        params["categoria"] = tuple(f_categoria)
    if f_secretaria:
        where_clauses.append("secretaria IN :secretaria")
        params["secretaria"] = tuple(f_secretaria)
    if f_hostname:
        where_clauses.append("hostname ILIKE :hostname")
        params["hostname"] = f"%{f_hostname}%"
    if f_ip:
        where_clauses.append("ip ILIKE :ip")
        params["ip"] = f"%{f_ip}%"

    if where_clauses:
        query_base += " WHERE " + " AND ".join(where_clauses)
    
    if 'equip_page' not in st.session_state:
        st.session_state.equip_page = 1
    ITEMS_PER_PAGE = 10
    
    try:
        count_query = f"SELECT COUNT(id) FROM ({query_base}) as sub"
        with conn.connect() as con:
            total_items = con.execute(text(count_query), params).scalar()
    except Exception as e:
        st.error(f"Erro ao contar equipamentos: {e}")
        total_items = 0

    total_pages = math.ceil(total_items / ITEMS_PER_PAGE) if total_items > 0 else 1
    if st.session_state.equip_page > total_pages: st.session_state.equip_page = total_pages
    if st.session_state.equip_page < 1: st.session_state.equip_page = 1
    
    offset = (st.session_state.equip_page - 1) * ITEMS_PER_PAGE
    query_base += f" ORDER BY id DESC LIMIT {ITEMS_PER_PAGE} OFFSET {offset}"

    try:
        df_equip = pd.read_sql(text(query_base), conn, params=params)

        if df_equip.empty:
            st.info("Nenhum equipamento encontrado com os filtros aplicados.")
            return

        st.markdown("##### Equipamentos Registrados")
        
        cols_header = st.columns((1, 1.5, 1.5, 1.5, 1.5, 2, 1.5))
        headers = ["Hostname", "Categoria", "Secretaria", "IP", "MAC", "Modelo (resumo)", "Ações"]
        for col, header in zip(cols_header, headers):
            col.markdown(f"**{header}**")
        
        st.markdown("<hr style='margin-top: 0; margin-bottom: 0;'>", unsafe_allow_html=True)

        for _, row in df_equip.iterrows():
            equip_id = row["id"]
            cols_row = st.columns((1, 1.5, 1.5, 1.5, 1.5, 2, 1.5))
            
            cols_row[0].write(row.get("hostname"))
            cols_row[1].write(row.get("categoria"))
            cols_row[2].write(row.get("secretaria"))
            cols_row[3].write(row.get("ip", "N/A"))
            cols_row[4].write(row.get("mac", "N/A"))
            spec = row.get("especificacao", "")
            spec_resumida = (spec[:30] + '...') if len(spec) > 30 else spec
            cols_row[5].write(spec_resumida)

            action_col = cols_row[6]
            col_b1, col_b2 = action_col.columns(2)
            
            if col_b1.button("Editar", key=f"edit_{equip_id}", use_container_width=True):
                st.session_state.edit_equip_id = equip_id
                if 'form_data' in st.session_state: del st.session_state.form_data 
                st.rerun()
            
            if col_b2.button("Deletar", key=f"del_{equip_id}", use_container_width=True, type="secondary"):
                st.session_state.delete_equip_id = equip_id
                st.session_state.delete_equip_data = row.to_dict()
                st.rerun() 

            st.markdown("<hr style='margin-top: 0; margin-bottom: 0;'>", unsafe_allow_html=True)

        st.markdown(" ")
        if total_pages > 1:
            col_nav1, col_nav2, col_nav3 = st.columns([1, 1, 1])
            if col_nav1.button("Anterior", key="prev_equip", disabled=(st.session_state.equip_page <= 1)):
                st.session_state.equip_page -= 1
                st.rerun()
            col_nav2.write(f"**Página {st.session_state.equip_page} de {total_pages}**")
            if col_nav3.button("Próxima", key="next_equip", disabled=(st.session_state.equip_page >= total_pages)):
                st.session_state.equip_page += 1
                st.rerun()
            
    except Exception as e:
        st.error(f"Erro ao consultar equipamentos: {e}")

def render_modal_delete(conn):
    # ... (função inalterada, já estava correta com st.dialog) ...
    if 'delete_equip_id' not in st.session_state or st.session_state.delete_equip_id is None:
        return

    equip_id = st.session_state.delete_equip_id
    data = st.session_state.delete_equip_data

    @st.dialog("Confirmar Exclusão", dismissible=False)
    def show_modal():
        st.warning(f"**Você tem certeza que deseja deletar este equipamento?**")
        st.markdown("Esta ação não pode ser desfeita.")
        
        st.markdown(f"**Hostname:** {data.get('hostname')}")
        st.markdown(f"**Categoria:** {data.get('categoria')}")
        st.markdown(f"**Secretaria:** {data.get('secretaria')}")
        if data.get('ip'):
            st.markdown(f"**IP:** {data.get('ip')}")

        st.markdown("---")
        
        col1, col2 = st.columns(2)
        if col1.button("Confirmar Exclusão", type="primary", use_container_width=True):
            if f_deletar_equipamento(conn, equip_id):
                del st.session_state.delete_equip_id
                del st.session_state.delete_equip_data
                st.rerun()
        
        if col2.button("Cancelar", use_container_width=True):
            del st.session_state.delete_equip_id
            del st.session_state.delete_equip_data
            st.rerun()

    show_modal()


def render():
    st.markdown("<h3 style='text-align: left;'>Registro de Equipamentos</h3>", unsafe_allow_html=True)
    conn = get_connection()

    tab1, tab2 = st.tabs(["Registrar/Atualizar Equipamento", "Consultar Equipamentos"])

    with tab1:
        render_form_equipamento(conn)
    
    with tab2:
        render_consulta_equipamentos(conn)
    
    render_modal_delete(conn)