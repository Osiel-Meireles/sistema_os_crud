# CÓDIGO COMPLETO E CORRIGIDO PARA: sistema_os_crud-main/minhas_recargas.py
import streamlit as st
import pandas as pd
from sqlalchemy import text
from database import get_connection
from datetime import datetime
import pytz

# Status de recargas simplificado
STATUS_RECARGA = ["EM ABERTO", "AGUARDANDO INSUMO", "RECARGA FEITA"]

def f_registrar_recarga(conn, dados_recarga):
    """Registra uma nova recarga."""
    try:
        with conn.connect() as con:
            with con.begin():
                query = text("""
                    INSERT INTO recargas (
                        numero_recarga, secretaria, localizacao, insumo, 
                        status, data_abertura, hora_abertura, responsavel
                    ) VALUES (
                        :numero_recarga, :secretaria, :localizacao, :insumo,
                        :status, :data_abertura, :hora_abertura, :responsavel
                    )
                """)
                con.execute(query, dados_recarga)
        st.success("Recarga registrada com sucesso!")
        return True
    except Exception as e:
        st.error(f"Erro ao registrar recarga: {e}")
        return False

def f_atualizar_recarga(conn, recarga_id, novo_status):
    """Atualiza o status de uma recarga."""
    try:
        with conn.connect() as con:
            with con.begin():
                query = text("""
                    UPDATE recargas
                    SET status = :status, data_atualizacao = :data
                    WHERE id = :id
                """)
                con.execute(query, {
                    "status": novo_status,
                    "data": datetime.now(pytz.utc),
                    "id": recarga_id
                })
        st.success("Status da recarga atualizado!")
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar recarga: {e}")
        return False

def render():
    role = st.session_state.get('role', '')
    display_name = st.session_state.get('display_name', '')
    
    st.title("Gerenciar Recargas")
    st.markdown("---")
    
    conn = get_connection()
    
    # ================= SEÇÃO: ADMINISTRATIVO =================
    if role in ["admin", "administrativo"]:
        tab1, tab2 = st.tabs(["Registrar Recarga", "Histórico de Recargas"])
        
        # ABA 1: REGISTRAR RECARGA
        with tab1:
            st.markdown("### Registrar Nova Recarga")
            st.info("Preencha os dados abaixo para registrar uma nova solicitação de recarga.")
            
            with st.form("form_registrar_recarga"):
                col1, col2 = st.columns(2)
                
                with col1:
                    numero_recarga = st.text_input(
                        "Número da Recarga *",
                        placeholder="Ex: REC-2025-001"
                    )
                    secretaria = st.selectbox(
                        "Secretaria *",
                        [""] + sorted([s for s in st.session_state.get('secretarias', []) if s])
                    )
                
                with col2:
                    localizacao = st.text_input(
                        "Localização do Serviço *",
                        placeholder="Ex: Sala 102, Prédio A"
                    )
                    insumo = st.text_input(
                        "Insumo/Material *",
                        placeholder="Ex: Toner HP CF283A, Cartucho de Tinta"
                    )
                
                responsavel = st.text_input(
                    "Responsável pelo Registro",
                    value=display_name,
                    disabled=True,
                    help="Preenchido automaticamente com seu nome"
                )
                
                # Data e hora automáticas
                agora = datetime.now()
                data_abertura = agora.date()
                hora_abertura = agora.strftime("%H:%M:%S")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.text_input(
                        "Data de Abertura",
                        value=data_abertura.strftime("%d/%m/%Y"),
                        disabled=True,
                        help="Preenchido automaticamente"
                    )
                with col2:
                    st.text_input(
                        "Hora de Abertura",
                        value=hora_abertura,
                        disabled=True,
                        help="Preenchido automaticamente"
                    )
                
                submitted = st.form_submit_button("Registrar Recarga", use_container_width=True, type="primary")
                
                if submitted:
                    if not numero_recarga or not secretaria or not localizacao or not insumo:
                        st.error("Preencha todos os campos obrigatórios (marcados com *).")
                    else:
                        dados_recarga = {
                            "numero_recarga": numero_recarga,
                            "secretaria": secretaria,
                            "localizacao": localizacao,
                            "insumo": insumo,
                            "status": "EM ABERTO",
                            "data_abertura": data_abertura,
                            "hora_abertura": hora_abertura,
                            "responsavel": display_name
                        }
                        
                        if f_registrar_recarga(conn, dados_recarga):
                            st.session_state.show_registrar = False
                            st.rerun()
        
        # ABA 2: HISTÓRICO DE RECARGAS
        with tab2:
            st.markdown("### Histórico de Recargas")
            
            try:
                query = text("""
                    SELECT id, numero_recarga, secretaria, localizacao, insumo, 
                           status, data_abertura, hora_abertura, responsavel
                    FROM recargas
                    ORDER BY data_abertura DESC, hora_abertura DESC
                """)
                
                with conn.connect() as con:
                    result = con.execute(query).fetchall()
                    if result:
                        df = pd.DataFrame(result, columns=result[0]._mapping.keys())
                        
                        # Filtros
                        col1, col2 = st.columns(2)
                        with col1:
                            filtro_status = st.multiselect(
                                "Filtrar por Status",
                                STATUS_RECARGA,
                                default=[]
                            )
                        with col2:
                            filtro_secretaria = st.multiselect(
                                "Filtrar por Secretaria",
                                sorted(df['secretaria'].unique()),
                                default=[]
                            )
                        
                        # Aplicar filtros
                        if filtro_status:
                            df = df[df['status'].isin(filtro_status)]
                        if filtro_secretaria:
                            df = df[df['secretaria'].isin(filtro_secretaria)]
                        
                        if len(df) > 0:
                            st.markdown(f"**Total: {len(df)} recarga(s)**")
                            st.markdown("---")
                            
                            for idx, row in df.iterrows():
                                with st.container(border=True):
                                    col1, col2, col3 = st.columns([2, 1, 1])
                                    
                                    with col1:
                                        st.markdown(f"**{row['numero_recarga']}**")
                                        st.markdown(f"{row['localizacao']}")
                                        st.markdown(f"{row['insumo']}")
                                        st.markdown(f"{row['secretaria']}")
                                    
                                    with col2:
                                        st.markdown(f"**Data:** {row['data_abertura']}")
                                        st.markdown(f"**Hora:** {row['hora_abertura']}")
                                    
                                    with col3:
                                        status_icons = {
                                            "EM ABERTO": "🔴",
                                            "AGUARDANDO INSUMO": "🟠",
                                            "RECARGA FEITA": "🟢"
                                        }
                                        icon = status_icons.get(row['status'], "⚪")
                                        st.markdown(f"**Status:** {icon} {row['status']}")
                                    
                                    st.caption(f"Registrado por: {row['responsavel']}")
                        else:
                            st.info("Nenhuma recarga encontrada com os filtros aplicados.")
                    else:
                        st.info("Nenhuma recarga registrada.")
            except Exception as e:
                st.error(f"Erro ao carregar histórico: {e}")
    
    # ================= SEÇÃO: TÉCNICO RECARGA =================
    elif role == "tecnico_recarga":
        st.markdown("### Minhas Recargas em Aberto")
        
        try:
            query = text("""
                SELECT id, numero_recarga, secretaria, localizacao, insumo, 
                       status, data_abertura, hora_abertura
                FROM recargas
                WHERE status IN ('EM ABERTO', 'AGUARDANDO INSUMO')
                ORDER BY data_abertura DESC, hora_abertura DESC
            """)
            
            with conn.connect() as con:
                result = con.execute(query).fetchall()
                if result:
                    df = pd.DataFrame(result, columns=result[0]._mapping.keys())
                    
                    if len(df) == 0:
                        st.success("Parabéns! Você não possui recargas pendentes!")
                    else:
                        st.info(f"Você tem **{len(df)}** recarga(s) para executar.")
                        st.markdown("---")
                        
                        for idx, row in df.iterrows():
                            with st.container(border=True):
                                col1, col2 = st.columns([3, 1])
                                
                                with col1:
                                    status_icons = {
                                        "EM ABERTO": "🔴",
                                        "AGUARDANDO INSUMO": "🟠"
                                    }
                                    icon = status_icons.get(row['status'], "⚪")
                                    
                                    st.markdown(f"### {icon} {row['numero_recarga']}")
                                    st.markdown(f"**Localização:** {row['localizacao']}")
                                    st.markdown(f"**Insumo:** {row['insumo']}")
                                    st.markdown(f"**Secretaria:** {row['secretaria']}")
                                    st.markdown(f"**Status:** {row['status']}")
                                    st.markdown(f"*Aberto em: {row['data_abertura']} às {row['hora_abertura']}*")
                                
                                with col2:
                                    if st.button(
                                        "✅ Recarga\nFeita",
                                        key=f"finish_{row['id']}",
                                        use_container_width=True
                                    ):
                                        if f_atualizar_recarga(conn, row['id'], "RECARGA FEITA"):
                                            st.rerun()
                else:
                    st.success("Nenhuma recarga em aberto!")
        except Exception as e:
            st.error(f"Erro ao carregar recargas: {e}")
    
    else:
        st.warning("Você não tem permissão para acessar esta página.")