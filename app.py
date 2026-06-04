import streamlit as st

st.set_page_config(
    page_title="ForgeFlow ERP",
    page_icon="⚙️",
    layout="wide"
)

st.title("⚙️ ForgeFlow ERP")
st.subheader("Sistema experto multiagente para taller de torno y fresadora")

mensaje = st.chat_input("Escribe tu solicitud...")

if mensaje:
    with st.chat_message("user"):
        st.write(mensaje)

    with st.chat_message("assistant"):
        st.write("Entendido. Aquí después irá la respuesta del chatbot y el motor de inferencia.")