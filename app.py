import streamlit as st
from src.agente_1_chatbot import (
    obtener_mensaje_bienvenida,
    generar_respuesta
)


st.set_page_config(
    page_title="ForgeFlow ERP",
    page_icon="⚙️",
    layout="wide"
)


def inicializar_estado():
    if "mensajes" not in st.session_state:
        st.session_state.mensajes = [
            {
                "rol": "assistant",
                "contenido": obtener_mensaje_bienvenida()
            }
        ]


def mostrar_header():
    st.title("⚙️ ForgeFlow ERP")
    st.caption("Sistema experto multiagente para taller de torno y fresadora")

    with st.expander("ℹ️ Estado del prototipo"):
        st.write("""
        **Commit actual:** Interfaz inicial del Agente 1.

        Funciones incluidas:

        - Mensaje de bienvenida.
        - Chat funcional en Streamlit.
        - Comandos básicos.
        - Detección simple de lenguaje natural.
        - Respuestas de demostración.

        Próximo commit:

        - Conexión con SQLite.
        - Consulta real de cotizaciones.
        - Consulta real de producción.
        - Registro de herramientas, materiales y otros datos.
        """)


def mostrar_sidebar():
    with st.sidebar:
        st.header("Panel del sistema")

        st.subheader("Agentes")
        st.write("✅ Agente 1: Atención al cliente")
        st.write("⬜ Agente 2: Motor de inferencia")
        st.write("⬜ Agente 3: Supervisor / Explicador")

        st.divider()

        st.subheader("Comandos rápidos")

        if st.button("/help"):
            procesar_mensaje("/help")

        if st.button("/cotizaciones"):
            procesar_mensaje("/cotizaciones")

        if st.button("/produccion"):
            procesar_mensaje("/produccion")

        if st.button("/inventario"):
            procesar_mensaje("/inventario")

        if st.button("/nueva_cotizacion"):
            procesar_mensaje("/nueva_cotizacion")

        st.divider()

        if st.button("🧹 Limpiar chat"):
            st.session_state.mensajes = [
                {
                    "rol": "assistant",
                    "contenido": obtener_mensaje_bienvenida()
                }
            ]
            st.rerun()


def mostrar_chat():
    for mensaje in st.session_state.mensajes:
        with st.chat_message(mensaje["rol"]):
            st.markdown(mensaje["contenido"])


def procesar_mensaje(texto_usuario):
    st.session_state.mensajes.append(
        {
            "rol": "user",
            "contenido": texto_usuario
        }
    )

    respuesta = generar_respuesta(texto_usuario)

    if respuesta == "__LIMPIAR_CHAT__":
        st.session_state.mensajes = [
            {
                "rol": "assistant",
                "contenido": obtener_mensaje_bienvenida()
            }
        ]
        st.rerun()

    st.session_state.mensajes.append(
        {
            "rol": "assistant",
            "contenido": respuesta
        }
    )


def main():
    inicializar_estado()
    mostrar_header()
    mostrar_sidebar()
    mostrar_chat()

    texto_usuario = st.chat_input("Escribe tu mensaje o comando...")

    if texto_usuario:
        procesar_mensaje(texto_usuario)
        st.rerun()


if __name__ == "__main__":
    main()