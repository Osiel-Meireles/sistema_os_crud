import streamlit as st
import pandas as pd
from sqlalchemy import text
from datetime import date, datetime
from streamlit_drawable_canvas import st_canvas
import base64
from PIL import Image
import io
import numpy as np

from database import get_connection, gerar_proximo_numero_os
from config import SECRETARIAS, TECNICOS, CATEGORIAS_INTERNA, EQUIPAMENTOS

def render():
    st.markdown("##### Ordens de Serviço Internas")
    st.text("Registre a ordem de serviço")

    conn = get_connection()
    
    secretarias_sorted = [SECRETARIAS[0]] + sorted(SECRETARIAS[1:])
    tecnicos_sorted = [TECNICOS[0]] + sorted(TECNICOS[1:])
    categorias_sorted = [CATEGORIAS_INTERNA[0]] + sorted(CATEGORIAS_INTERNA[1:])
    equipamentos_sorted = [EQUIPAMENTOS[0]] + sorted(EQUIPAMENTOS[1:])

    with st.form("nova_os_interna", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            secretaria = st.selectbox("Secretaria", secretarias_sorted)
            solicitante = st.text_input("Solicitante")
            solicitacao_cliente = st.text_area("Solicitação do Cliente")
            patrimonio = st.text_input("Número do Patrimônio")
            tecnico = st.selectbox("Técnico", tecnicos_sorted)
            data = st.date_input("Data de Entrada", value=date.today(), format="DD/MM/YYYY")

        with col2:
            setor = st.text_input("Setor")
            telefone = st.text_input("Telefone")
            categoria = st.selectbox("Categoria do Serviço", categorias_sorted)
            equipamento = st.selectbox("Equipamento", equipamentos_sorted)
            hora = st.time_input("Hora de Entrada", value=datetime.now().time())
        
        st.markdown("---")
        st.write("Assinatura do Solicitante:")
        canvas_result = st_canvas(
            fill_color="rgba(255, 165, 0, 0.3)",
            stroke_width=3,
            stroke_color="#000000",
            background_color="#FFFFFF",
            height=150,
            width=600,
            drawing_mode="freedraw",
            key="canvas_interna"
        )

        submitted = st.form_submit_button("Registrar ordem de serviço", use_container_width=True, type='primary')
        
        if submitted:
            # Validações...
            if not all([setor, solicitante, telefone, solicitacao_cliente]):
                st.error("Por favor, preencha todos os campos de texto (Setor, Solicitante, Telefone, Solicitação).")
                return
            if "Selecione..." in [secretaria, tecnico, categoria, equipamento]:
                st.error("Por favor, selecione uma secretaria, técnico, categoria e equipamento válidos.")
                return
            if canvas_result.image_data is None:
                st.error("A assinatura do solicitante é obrigatória para criar a OS.")
                return

            try:
                # --- INÍCIO DA CORREÇÃO ---
                # Converte o desenho do canvas para uma imagem PNG antes de salvar
                image_array = canvas_result.image_data.astype(np.uint8)
                pil_image = Image.fromarray(image_array, 'RGBA')
                buffer = io.BytesIO()
                pil_image.save(buffer, format="PNG")
                img_bytes = buffer.getvalue()
                # --- FIM DA CORREÇÃO ---

                assinatura_base64 = base64.b64encode(img_bytes).decode("utf-8")
                assinatura_final = f"data:image/png;base64,{assinatura_base64}"

                with conn.connect() as con:
                    with con.begin(): 
                        con.execute(text("LOCK TABLE os_interna IN ACCESS EXCLUSIVE MODE"))
                        
                        numero_os = gerar_proximo_numero_os(con, "os_interna")
                        
                        con.execute(
                            text("""
                                INSERT INTO os_interna (numero, secretaria, setor, data, hora, solicitante, telefone, solicitacao_cliente, categoria, patrimonio, equipamento, status, tecnico, assinatura_solicitante_entrada)
                                VALUES (:numero, :secretaria, :setor, :data, :hora, :solicitante, :telefone, :solicitacao_cliente, :categoria, :patrimonio, :equipamento, 'EM ABERTO', :tecnico, :assinatura)
                            """),
                            {
                                "numero": numero_os, "secretaria": secretaria, "setor": setor, "data": data, "hora": hora,
                                "solicitante": solicitante, "telefone": telefone, "solicitacao_cliente": solicitacao_cliente,
                                "categoria": categoria, "patrimonio": patrimonio, "equipamento": equipamento,
                                "tecnico": tecnico, "assinatura": assinatura_final
                            }
                        )
                st.toast(f"✅ OS Interna nº {numero_os} adicionada com sucesso!")

            except Exception as e:
                st.error(f"Ocorreu um erro ao registrar a OS: {e}")

    st.markdown("---")
    st.markdown("##### Ordens de serviço internas cadastradas: ")
    df = pd.read_sql("SELECT * FROM os_interna ORDER BY id DESC", conn)

    date_cols = ['data', 'data_finalizada', 'data_retirada']
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%d/%m/%Y')
    
    st.dataframe(df)
