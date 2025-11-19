# CÓDIGO ATUALIZADO E COMPLETO PARA: sistema_os_crud-main/importar_dados.py

import streamlit as st
from import_export import importar_equipamentos, importar_os_interna, importar_os_externa
from sqlalchemy.exc import IntegrityError # Importa o erro específico

def render():
    st.markdown("<h3 style='text-align: left;'>Importação de Dados em Massa</h3>", unsafe_allow_html=True)
    st.info("Use esta tela para importar dados de planilhas (CSV, XLSX, ODS) para o sistema.")

    # --- 1. IMPORTAÇÃO DE EQUIPAMENTOS (COM TRATAMENTO DE ERRO) ---
    st.markdown("---")
    st.markdown("#### 1. Importar Equipamentos")
    st.write("Importe o arquivo CSV de inventário (como `equipamentos_pf.csv`).")
    st.write("Colunas esperadas: `Categoria`, `Hostname`, `ModeloEspecificacao` (para especificação), `Secretaria`, `Setor` (para departamento), etc.")
    
    uploaded_equip = st.file_uploader("Selecione o arquivo de equipamentos", type=["csv", "xlsx", "ods"], key="equip_uploader")
    
    if uploaded_equip is not None:
        if st.button("Importar Equipamentos", type="primary"):
            try:
                with st.spinner("Lendo e processando o arquivo de equipamentos..."):
                    inserted, ignored = importar_equipamentos(uploaded_equip)
                st.success(f"Importação concluída! {inserted} novos equipamentos registrados.")
                if ignored > 0:
                    st.warning(f"{ignored} registros foram ignorados (provavelmente duplicados ou com dados obrigatórios faltando).")
            
            # --- ALTERAÇÃO AQUI: Captura o erro de duplicidade ---
            except IntegrityError as e:
                if "UniqueViolation" in str(e) or "equipamentos_mac_key" in str(e) or "equipamentos_ip_key" in str(e) or "equipamentos_hostname_key" in str(e):
                    st.error("Erro de Importação: O arquivo contém dados duplicados (IP, MAC ou Hostname) que já existem no banco. A importação foi interrompida.")
                    st.info("Os dados que já estavam no banco não foram alterados. Registros que já estavam no CSV *antes* da duplicata podem ter sido inseridos.")
                else:
                    st.error(f"Ocorreu um erro de banco de dados: {e}")
            # --- FIM DA ALTERAÇÃO ---
            except Exception as e:
                st.error(f"Ocorreu um erro crítico durante a importação: {e}")
                
    # --- 2. IMPORTAÇÃO DE OS (Legado) ---
    st.markdown("---")
    st.markdown("#### 2. Importar Ordens de Serviço (Legado)")
    st.warning("Use esta opção apenas para importar dados de planilhas antigas. Para novos registros, use a tela 'Registrar OS'.")

    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**OS Interna**")
        uploaded_os_int = st.file_uploader("Selecione o arquivo de OS Interna", type=["csv", "xlsx", "ods"], key="os_int_uploader")
        if uploaded_os_int is not None:
            if st.button("Importar OS Interna"):
                try:
                    with st.spinner("Importando OS Internas..."):
                        inserted_int = importar_os_interna(uploaded_os_int)
                    st.success(f"Importação concluída! {inserted_int} novos registros de OS Interna adicionados.")
                except Exception as e:
                    st.error(f"Ocorreu um erro na importação de OS Interna: {e}")

    with col2:
        st.markdown("**OS Externa**")
        uploaded_os_ext = st.file_uploader("Selecione o arquivo de OS Externa", type=["csv", "xlsx", "ods"], key="os_ext_uploader")
        if uploaded_os_ext is not None:
            if st.button("Importar OS Externa"):
                try:
                    with st.spinner("Importando OS Externas..."):
                        inserted_ext = importar_os_externa(uploaded_os_ext)
                    st.success(f"Importação concluída! {inserted_ext} novos registros de OS Externa adicionados.")
                except Exception as e:
                    st.error(f"Ocorreu um erro na importação de OS Externa: {e}")