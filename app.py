import streamlit as st

from src import db
from src import agente_2_motor
from src import agente_3_supervisor
from src.agente_1_chatbot import obtener_mensaje_bienvenida, generar_respuesta


st.set_page_config(
    page_title="ForgeFlow ERP",
    page_icon="⚙️",
    layout="wide",
)


def inicializar_estado():
    if "mensajes" not in st.session_state:
        st.session_state.mensajes = [
            {"rol": "assistant", "contenido": obtener_mensaje_bienvenida()}
        ]


def procesar_mensaje(texto_usuario: str):
    st.session_state.mensajes.append({"rol": "user", "contenido": texto_usuario})
    respuesta = generar_respuesta(texto_usuario)

    if respuesta == "__LIMPIAR_CHAT__":
        st.session_state.mensajes = [
            {"rol": "assistant", "contenido": obtener_mensaje_bienvenida()}
        ]
        st.rerun()

    st.session_state.mensajes.append({"rol": "assistant", "contenido": respuesta})


def mostrar_header():
    st.title("⚙️ ForgeFlow ERP")
    st.caption("Sistema experto multiagente para taller de torno y fresadora")

    if not db.existe_bd():
        st.warning("No se encontró `database/forgeflow.db`. Ejecuta primero `py seed.py`.")

    with st.expander("ℹ️ Estado del prototipo"):
        st.write(
            """
                Permite consultar inventario, materiales, herramientas, máquinas, proveedores y clientes mediante lenguaje natural o comandos específicos, además de generar cotizaciones técnicas con explicación detallada del proceso de inferencia utilizado.
            
            """
        )


def mostrar_sidebar():
    with st.sidebar:
        st.header("Panel rápido")

        st.subheader("Agentes")
        st.write("✅ Agente 1: Atención al cliente")
        st.write("✅ Agente 2: Motor de inferencia v2 — modelo físico por etapas")
        st.write("✅ Agente 3: Supervisor")

        st.divider()
        st.subheader("Comandos")

        comandos = [
            "/help",
            "/inventario",
            "/materiales",
            "/herramientas",
            "/maquinas",
            "/proveedores",
            "/cotizaciones",
            "/produccion",
        ]

        for comando in comandos:
            if st.button(comando, use_container_width=True):
                procesar_mensaje(comando)
                st.rerun()

        st.divider()
        if st.button("🧹 Limpiar chat", use_container_width=True):
            st.session_state.mensajes = [
                {"rol": "assistant", "contenido": obtener_mensaje_bienvenida()}
            ]
            st.rerun()


def mostrar_chat():
    for mensaje in st.session_state.mensajes:
        with st.chat_message(mensaje["rol"]):
            st.markdown(mensaje["contenido"])

    texto_usuario = st.chat_input("Escribe tu mensaje o comando...")
    if texto_usuario:
        procesar_mensaje(texto_usuario)
        st.rerun()


def mostrar_tabla(titulo: str, filas: list[dict]):
    st.subheader(titulo)
    if filas:
        st.dataframe(filas, use_container_width=True, hide_index=True)
    else:
        st.info("No hay registros para mostrar.")


def formulario_agregar_material():
    with st.expander("➕ Agregar material", expanded=False):
        with st.form("form_agregar_material"):
            col1, col2, col3 = st.columns(3)

            with col1:
                codigo = st.text_input("Código", placeholder="MAT-AC1018-BR-2")
                material = st.text_input("Material *", placeholder="Acero 1018")
                perfil = st.text_input("Perfil *", placeholder="Barra Redonda")
                dimension = st.number_input("Dimensión principal *", min_value=0.0, value=1.0, step=0.1)

            with col2:
                unidad_dimension = st.selectbox("Unidad dimensión", ["mm", "cm", "m", "pulgadas"], index=3)
                cantidad = st.number_input("Cantidad disponible *", min_value=0.0, value=1.0, step=0.5)
                unidad_inventario = st.selectbox("Unidad inventario", ["metros", "piezas", "kg", "placas"], index=0)
                costo = st.number_input("Costo unitario", min_value=0.0, value=0.0, step=10.0)

            with col3:
                stock_minimo = st.number_input("Stock mínimo", min_value=0.0, value=0.0, step=0.5)
                ubicacion = st.text_input("Ubicación", placeholder="Rack A-01")
                estado = st.selectbox("Estado", ["DISPONIBLE", "BAJO_STOCK", "AGOTADO", "APARTADO"])
                observaciones = st.text_area("Observaciones")

            enviado = st.form_submit_button("Guardar material")

            if enviado:
                if not material.strip() or not perfil.strip():
                    st.error("Material y perfil son obligatorios.")
                else:
                    try:
                        nuevo_id = db.agregar_material(
                            codigo,
                            material,
                            perfil,
                            dimension,
                            unidad_dimension,
                            cantidad,
                            unidad_inventario,
                            costo,
                            stock_minimo,
                            ubicacion,
                            estado,
                            observaciones,
                        )
                        st.success(f"Material guardado correctamente. ID: {nuevo_id}")
                        st.rerun()
                    except db.DatabaseError as exc:
                        st.error(str(exc))


def formulario_actualizar_material(materiales: list[dict]):
    with st.expander("🔄 Actualizar stock de material", expanded=False):
        if not materiales:
            st.info("No hay materiales registrados.")
            return

        opciones = {
            f"{m['id_material']} - {m['material']} / {m['perfil']} / {m['dimension_principal']} {m['unidad_dimension']}": m
            for m in materiales
        }

        with st.form("form_actualizar_material"):
            seleccionado = st.selectbox("Material", list(opciones.keys()))
            material = opciones[seleccionado]

            col1, col2 = st.columns(2)
            with col1:
                cantidad = st.number_input(
                    "Nueva cantidad disponible",
                    min_value=0.0,
                    value=float(material["cantidad_disponible"]),
                    step=0.5,
                )
                estado = st.selectbox(
                    "Estado",
                    ["AUTO", "DISPONIBLE", "BAJO_STOCK", "AGOTADO", "APARTADO"],
                    index=0,
                )
            with col2:
                observaciones = st.text_area("Observaciones de actualización")

            enviado = st.form_submit_button("Actualizar material")

            if enviado:
                try:
                    db.actualizar_stock_material(
                        int(material["id_material"]),
                        cantidad,
                        None if estado == "AUTO" else estado,
                        observaciones,
                    )
                    st.success("Material actualizado correctamente.")
                    st.rerun()
                except db.DatabaseError as exc:
                    st.error(str(exc))


def formulario_agregar_herramienta():
    with st.expander("➕ Agregar herramienta", expanded=False):
        with st.form("form_agregar_herramienta"):
            col1, col2, col3 = st.columns(3)

            with col1:
                codigo = st.text_input("Código", placeholder="HER-BRO-HSS-01")
                nombre = st.text_input("Nombre herramienta *", placeholder="Broca HSS")
                tipo = st.text_input("Tipo *", placeholder="Broca")
                medida = st.text_input("Medida", placeholder="1/2 pulgada")

            with col2:
                material_herramienta = st.text_input("Material herramienta", placeholder="HSS")
                stock = st.number_input("Stock unidades *", min_value=0, value=1, step=1)
                stock_minimo = st.number_input("Stock mínimo", min_value=0, value=0, step=1)
                costo = st.number_input("Costo unitario", min_value=0.0, value=0.0, step=10.0)

            with col3:
                ubicacion = st.text_input("Ubicación", placeholder="Cajón H-01")
                estado = st.selectbox(
                    "Estado",
                    ["DISPONIBLE", "BAJO_STOCK", "REQUERIR_AFILADO", "EN_USO", "AGOTADO", "DAÑADA"],
                )
                observaciones = st.text_area("Observaciones")

            enviado = st.form_submit_button("Guardar herramienta")

            if enviado:
                if not nombre.strip() or not tipo.strip():
                    st.error("Nombre y tipo son obligatorios.")
                else:
                    try:
                        nuevo_id = db.agregar_herramienta(
                            codigo,
                            nombre,
                            tipo,
                            medida,
                            material_herramienta,
                            stock,
                            stock_minimo,
                            costo,
                            ubicacion,
                            estado,
                            observaciones,
                        )
                        st.success(f"Herramienta guardada correctamente. ID: {nuevo_id}")
                        st.rerun()
                    except db.DatabaseError as exc:
                        st.error(str(exc))


def formulario_actualizar_herramienta(herramientas: list[dict]):
    with st.expander("🔄 Actualizar stock/estado de herramienta", expanded=False):
        if not herramientas:
            st.info("No hay herramientas registradas.")
            return

        opciones = {
            f"{h['id_herramienta']} - {h['nombre_herramienta']} / {h['tipo']} / {h.get('medida') or ''}": h
            for h in herramientas
        }

        with st.form("form_actualizar_herramienta"):
            seleccionado = st.selectbox("Herramienta", list(opciones.keys()))
            herramienta = opciones[seleccionado]

            col1, col2 = st.columns(2)
            with col1:
                stock = st.number_input(
                    "Nuevo stock",
                    min_value=0,
                    value=int(herramienta["stock_unidades"]),
                    step=1,
                )
                estado = st.selectbox(
                    "Estado",
                    ["AUTO", "DISPONIBLE", "BAJO_STOCK", "REQUERIR_AFILADO", "EN_USO", "AGOTADO", "DAÑADA"],
                    index=0,
                )
            with col2:
                observaciones = st.text_area("Observaciones de actualización")

            enviado = st.form_submit_button("Actualizar herramienta")

            if enviado:
                try:
                    db.actualizar_stock_herramienta(
                        int(herramienta["id_herramienta"]),
                        int(stock),
                        None if estado == "AUTO" else estado,
                        observaciones,
                    )
                    st.success("Herramienta actualizada correctamente.")
                    st.rerun()
                except db.DatabaseError as exc:
                    st.error(str(exc))


def formulario_actualizar_maquina(maquinas: list[dict]):
    with st.expander("🔄 Actualizar estado de máquina", expanded=False):
        if not maquinas:
            st.info("No hay máquinas registradas.")
            return

        opciones = {
            f"{m['id_maquina']} - {m['nombre_maquina']} / {m['tipo_maquina']}": m
            for m in maquinas
        }

        with st.form("form_actualizar_maquina"):
            seleccionado = st.selectbox("Máquina", list(opciones.keys()))
            maquina = opciones[seleccionado]
            estado = st.selectbox(
                "Nuevo estado",
                ["DISPONIBLE", "EN_USO", "MANTENIMIENTO", "FUERA_SERVICIO"],
            )
            observaciones = st.text_area("Observaciones")
            enviado = st.form_submit_button("Actualizar máquina")

            if enviado:
                try:
                    db.actualizar_estado_maquina(int(maquina["id_maquina"]), estado, observaciones)
                    st.success("Máquina actualizada correctamente.")
                    st.rerun()
                except db.DatabaseError as exc:
                    st.error(str(exc))


def formulario_agregar_proveedor():
    with st.expander("➕ Agregar proveedor", expanded=False):
        with st.form("form_agregar_proveedor"):
            col1, col2, col3 = st.columns(3)
            with col1:
                nombre = st.text_input("Nombre proveedor *")
                tipo = st.selectbox("Tipo", ["MATERIALES", "HERRAMIENTAS", "SERVICIO_EXTERNO", "MIXTO"])
                contacto = st.text_input("Contacto")
                correo = st.text_input("Correo")
            with col2:
                telefono = st.text_input("Teléfono")
                direccion = st.text_input("Dirección")
                especialidad = st.text_input("Especialidad", placeholder="Metales, Herramientas, Tratamiento térmico")
                entrega = st.number_input("Tiempo entrega estimado días", min_value=0, value=0, step=1)
            with col3:
                condiciones = st.text_input("Condiciones de pago")
                calificacion = st.slider("Calificación", min_value=1, max_value=5, value=5)
                estado = st.selectbox("Estado", ["ACTIVO", "INACTIVO"])
                observaciones = st.text_area("Observaciones")

            enviado = st.form_submit_button("Guardar proveedor")

            if enviado:
                if not nombre.strip():
                    st.error("El nombre del proveedor es obligatorio.")
                else:
                    try:
                        nuevo_id = db.agregar_proveedor(
                            nombre,
                            tipo,
                            contacto,
                            correo,
                            telefono,
                            direccion,
                            especialidad,
                            entrega,
                            condiciones,
                            calificacion,
                            estado,
                            observaciones,
                        )
                        st.success(f"Proveedor guardado correctamente. ID: {nuevo_id}")
                        st.rerun()
                    except db.DatabaseError as exc:
                        st.error(str(exc))


def mostrar_inventario_gestion():
    st.header("📦 Inventario y gestión")

    try:
        materiales = db.obtener_materiales()
        herramientas = db.obtener_herramientas()
        maquinas = db.obtener_maquinas()
        proveedores = db.obtener_proveedores()
    except db.DatabaseError as exc:
        st.error(str(exc))
        return

    tab_materiales, tab_herramientas, tab_maquinas, tab_proveedores = st.tabs(
        ["Materiales", "Herramientas", "Máquinas", "Proveedores"]
    )

    with tab_materiales:
        mostrar_tabla("Materiales registrados", materiales)
        formulario_agregar_material()
        formulario_actualizar_material(materiales)

    with tab_herramientas:
        mostrar_tabla("Herramientas registradas", herramientas)
        formulario_agregar_herramienta()
        formulario_actualizar_herramienta(herramientas)

    with tab_maquinas:
        mostrar_tabla("Máquinas registradas", maquinas)
        formulario_actualizar_maquina(maquinas)

    with tab_proveedores:
        mostrar_tabla("Proveedores registrados", proveedores)
        formulario_agregar_proveedor()


def mostrar_cotizaciones_produccion():
    st.header("📝 Cotizaciones y producción")

    try:
        pendientes = db.obtener_cotizaciones_pendientes()
        produccion = db.obtener_ordenes_produccion()
    except db.DatabaseError as exc:
        st.error(str(exc))
        return

    col1, col2 = st.columns(2)

    with col1:
        mostrar_tabla("Pendientes por aprobar", pendientes)

        with st.expander("✅ Aprobar cotización", expanded=False):
            if not pendientes:
                st.info("No hay cotizaciones pendientes.")
            else:
                opciones = {
                    f"{c['id_cotizacion']} - {c['folio']} / {c['cliente_nombre']} / {c['pieza_solicitada']}": c
                    for c in pendientes
                }
                with st.form("form_aprobar_cotizacion"):
                    seleccion = st.selectbox("Cotización", list(opciones.keys()))
                    enviar_a = st.selectbox("Nuevo estado", ["APROBADO", "EN_PRODUCCION", "CANCELADA"])
                    observaciones = st.text_area("Observaciones")
                    enviado = st.form_submit_button("Actualizar cotización")

                    if enviado:
                        try:
                            cot = opciones[seleccion]
                            db.actualizar_estado_cotizacion(
                                int(cot["id_cotizacion"]), enviar_a, observaciones
                            )
                            st.success("Cotización actualizada correctamente.")
                            st.rerun()
                        except db.DatabaseError as exc:
                            st.error(str(exc))

    with col2:
        mostrar_tabla("Aprobadas / en producción", produccion)

def vista_agente_2():
    st.subheader("🧮 Agente 2 - Motor de inferencia")
    st.write("""
    Esta sección genera una cotización preliminar usando la base de conocimiento,
    inventario, tarifas y reglas básicas del sistema experto.
    """)

    try:
        plantillas = db.obtener_plantillas()
    except Exception as error:
        st.error(f"No se pudieron cargar las plantillas: {error}")
        return

    nombres_plantillas = [p["nombre_pieza"] for p in plantillas]

    with st.form("form_agente_2_cotizacion"):
        cliente_nombre = st.text_input("Nombre del cliente")

        pieza_solicitada = st.selectbox(
            "Pieza solicitada",
            options=nombres_plantillas if nombres_plantillas else ["pieza_personalizada"]
        )

        tipo_servicio = st.selectbox(
            "Tipo de servicio",
            ["FABRICACION", "REPARACION", "MODIFICACION", "MANTENIMIENTO"]
        )

        cantidad_piezas = st.number_input(
            "Cantidad de piezas",
            min_value=1,
            step=1
        )

        material_solicitado = st.text_input(
            "Material solicitado",
            value="Acero 1018"
        )

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            diametro = st.text_input("Diámetro exterior (pulgadas)", value="", placeholder="ej. 4")

        with col2:
            largo = st.text_input("Largo (pulgadas)", value="", placeholder="ej. 2")

        with col3:
            num_dientes = st.text_input("Núm. dientes (solo engranes)", value="", placeholder="ej. 99")

        with col4:
            tolerancia = st.text_input("Tolerancia", value="")

        requerimientos_cliente = st.text_area(
            "Requerimientos del cliente",
            placeholder="Ejemplo: requiere ajuste para balero, acabado fino, ranura interna, etc."
        )

        generar = st.form_submit_button("Generar cotización preliminar")

    if generar:
        dimensiones = {
            "diametro_medida_principal": diametro,
            "largo": largo,
            "num_dientes": num_dientes,
            "ancho": largo,
            "tolerancia": tolerancia
        }

        try:
            resultado = agente_2_motor.generar_cotizacion_preliminar(
                cliente_nombre=cliente_nombre,
                pieza_solicitada=pieza_solicitada,
                tipo_servicio=tipo_servicio,
                cantidad_piezas=int(cantidad_piezas),
                material_solicitado=material_solicitado,
                requerimientos_cliente=requerimientos_cliente,
                dimensiones=dimensiones
            )

            st.success(f"Cotización generada: **{resultado['folio']}**")

            # ── Métricas principales ──────────────────────────────────────
            col_a, col_b, col_c, col_d = st.columns(4)
            with col_a:
                st.metric("Estado", resultado["estado"])
            with col_b:
                horas_txt = resultado.get("horas_texto", f"{resultado['horas_maquinado_estimadas']:.2f} h")
                st.metric("Tiempo estimado", horas_txt)
            with col_c:
                st.metric("Precio final", f"${resultado['precio_final']:.2f}")
            with col_d:
                st.metric("Entrega estimada", resultado["fecha_entrega_estimada"])

            # ── Desglose por etapa ────────────────────────────────────────
            st.subheader("🔩 Desglose de maquinado por etapa")
            if resultado.get("detalle_procesos"):
                import pandas as pd
                filas = []
                for paso in resultado["detalle_procesos"]:
                    h = paso["horas_total"]
                    hh = int(h); mm = round((h - hh) * 60)
                    tiempo_txt = f"{hh}h {mm}min" if hh > 0 and mm > 0 else (f"{hh}h" if hh > 0 else f"{mm}min")
                    filas.append({
                        "Etapa":        paso["etapa"],
                        "Descripción":  paso["descripcion"],
                        "h/pieza":      f"{paso['horas_por_pieza']:.3f}",
                        "Tiempo total": tiempo_txt,
                        "Tarifa $/h":   f"${paso['tarifa_hora']:.0f}",
                        "Subtotal":     f"${paso['costo_estimado']:.2f}",
                    })
                st.dataframe(pd.DataFrame(filas), use_container_width=True, hide_index=True)

            # ── Resumen de costos ─────────────────────────────────────────
            st.subheader("💰 Resumen de costos")
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Material:** ${resultado.get('costo_total', 0) - resultado.get('costo_total', resultado['precio_final'] / 1.2):.2f}")
                st.write(f"**Maquinado:** ver desglose arriba")
            with col2:
                st.write(f"**Precio final (con margen):** **${resultado['precio_final']:.2f}**")

            # ── Explicación completa ──────────────────────────────────────
            st.subheader("🧠 Explicación del Agente 2")
            st.markdown(resultado["explicacion"])

            # ── Hoja de ruta ──────────────────────────────────────────────
            st.subheader("📋 Hoja de ruta")
            st.code(resultado["hoja_ruta"])

            # ── Advertencias ──────────────────────────────────────────────
            if resultado["advertencias"]:
                st.warning("⚠️ La cotización requiere revisión antes de aprobar.")
                for advertencia in resultado["advertencias"]:
                    st.write(f"- {advertencia}")

        except Exception as error:
            st.error(f"No se pudo generar la cotización: {error}")

def main():
    inicializar_estado()
    mostrar_header()
    mostrar_sidebar()

    tab_chat, tab_inventario, tab_cotizaciones, tab_agente_2, tab_agente_3 = st.tabs(
        ["💬 Chat", "📦 Inventario y gestión", "📝 Cotizaciones y producción", "🧮 Agente 2", "✅ Agente 3"]
    )

    with tab_agente_3:
        vista_agente_3()

    with tab_chat:
        mostrar_chat()

    with tab_inventario:
        mostrar_inventario_gestion()

    with tab_cotizaciones:
        mostrar_cotizaciones_produccion()

    with tab_agente_2:
        vista_agente_2()

def vista_agente_3():
    st.subheader("✅ Agente 3 - Supervisor y explicador")
    st.write("""
    Este agente revisa la cotización generada por el Agente 2, explica la toma de decisiones
    y permite validar si la cotización pasa a producción.
    """)

    try:
        cotizaciones = db.obtener_cotizaciones_para_supervisor()
    except Exception as error:
        st.error(f"No se pudieron cargar las cotizaciones: {error}")
        return

    if not cotizaciones:
        st.info("No hay cotizaciones disponibles para supervisar.")
        return

    st.dataframe(cotizaciones, use_container_width=True)

    opciones = {
        f"{c['folio']} - {c['cliente_nombre']} - {c['pieza_solicitada']} - {c['estado_orden']}": c["id_cotizacion"]
        for c in cotizaciones
    }

    seleccion = st.selectbox(
        "Selecciona una cotización para revisar",
        list(opciones.keys())
    )

    id_cotizacion = opciones[seleccion]
    cotizacion = db.obtener_cotizacion_por_id(id_cotizacion)

    if cotizacion:
        explicacion = agente_3_supervisor.generar_explicacion_supervisor(cotizacion)

        st.markdown(explicacion)

        st.divider()

        nuevo_estado = st.selectbox(
            "Decisión del supervisor",
            ["APROBADO", "EN_PRODUCCION", "CANCELADA", "VALIDACION_PENDIENTE"]
        )

        observaciones = st.text_area(
            "Observaciones del supervisor",
            placeholder="Ejemplo: Se aprueba porque el costo y tiempo son razonables."
        )

        if st.button("Guardar decisión del Agente 3"):
            try:
                agente_3_supervisor.validar_cotizacion(
                    id_cotizacion=id_cotizacion,
                    nuevo_estado=nuevo_estado,
                    observaciones_supervisor=observaciones
                )
                st.success(f"Cotización actualizada a estado: {nuevo_estado}")
                st.rerun()
            except Exception as error:
                st.error(f"No se pudo validar la cotización: {error}")


if __name__ == "__main__":
    main()


