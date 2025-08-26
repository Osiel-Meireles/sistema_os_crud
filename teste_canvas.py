# teste_canvas.py
import streamlit as st
from streamlit_drawable_canvas import st_canvas

st.title("Teste Mínimo do Canvas")
st.write("Se você vir uma caixa branca abaixo onde é possível desenhar, o componente funciona.")

# Chamada simples para o componente
st_canvas(
    stroke_width=3,
    stroke_color="#000000",
    background_color="#FFFFFF",
    height=300,
    width=600,
    key="teste_simples",
)

st.write("Fim do teste.")