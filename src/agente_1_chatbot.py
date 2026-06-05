from src import db


def obtener_mensaje_bienvenida() -> str:
    return """
👋 **Bienvenido a ForgeFlow ERP**

Soy el **Agente 1 - Atención al Cliente**.

En este segundo commit ya puedo consultar información real de la base de datos y ayudarte a ubicar módulos del sistema.

Comandos principales:

- `/help` → Ver ayuda.
- `/inventario` → Resumen real del inventario.
- `/materiales` → Ver materiales registrados.
- `/herramientas` → Ver herramientas registradas.
- `/maquinas` → Ver máquinas del taller.
- `/proveedores` → Ver proveedores.
- `/cotizaciones` → Ver cotizaciones pendientes por aprobar.
- `/produccion` → Ver cotizaciones aprobadas o en producción.
- `/limpiar` → Limpiar el chat.

Para agregar o actualizar datos usa la pestaña **Inventario y gestión**.
"""


def obtener_ayuda() -> str:
    return """
📌 **Comandos disponibles**

| Comando | Función |
|---|---|
| `/help` | Muestra esta ayuda. |
| `/inventario` | Muestra resumen real de inventario y alertas. |
| `/materiales` | Lista materiales registrados. |
| `/herramientas` | Lista herramientas registradas. |
| `/maquinas` | Lista máquinas registradas. |
| `/proveedores` | Lista proveedores registrados. |
| `/cotizaciones` | Muestra cotizaciones pendientes por aprobar. |
| `/produccion` | Muestra órdenes aprobadas o en producción. |
| `/limpiar` | Limpia el historial del chat. |

También puedes escribir frases como:

- "Quiero ver el inventario"
- "Muéstrame las herramientas"
- "Necesito revisar cotizaciones pendientes"
- "Qué trabajos están en producción"
"""


def tabla_markdown(filas: list[dict], columnas: list[str], max_filas: int = 10) -> str:
    if not filas:
        return "No hay registros para mostrar."

    filas = filas[:max_filas]
    encabezado = "| " + " | ".join(columnas) + " |"
    separador = "| " + " | ".join(["---"] * len(columnas)) + " |"
    cuerpo = []

    for fila in filas:
        valores = []
        for columna in columnas:
            valor = fila.get(columna, "")
            valores.append(str(valor if valor is not None else ""))
        cuerpo.append("| " + " | ".join(valores) + " |")

    extra = ""
    if len(filas) == max_filas:
        extra = "\n\n_Se muestran los primeros registros. Para ver todo, usa la pestaña de gestión._"

    return "\n".join([encabezado, separador] + cuerpo) + extra


def respuesta_inventario() -> str:
    resumen = db.obtener_resumen_sistema()
    alertas = db.obtener_alertas_inventario()

    texto = "📦 **Resumen real del sistema**\n\n"
    texto += "| Módulo | Registros |\n|---|---:|\n"
    for tabla, total in resumen.items():
        texto += f"| {tabla} | {total} |\n"

    texto += "\n⚠️ **Alertas de inventario**\n\n"
    texto += f"- Materiales en bajo stock o agotados: **{len(alertas['materiales'])}**\n"
    texto += f"- Herramientas con alerta: **{len(alertas['herramientas'])}**\n"

    return texto


def respuesta_materiales() -> str:
    filas = db.obtener_materiales()
    return "📦 **Materiales registrados**\n\n" + tabla_markdown(
        filas,
        ["id_material", "codigo_material", "material", "perfil", "cantidad_disponible", "unidad_inventario", "estado"],
    )


def respuesta_herramientas() -> str:
    filas = db.obtener_herramientas()
    return "🧰 **Herramientas registradas**\n\n" + tabla_markdown(
        filas,
        ["id_herramienta", "codigo_herramienta", "nombre_herramienta", "tipo", "stock_unidades", "estado"],
    )


def respuesta_maquinas() -> str:
    filas = db.obtener_maquinas()
    return "🏭 **Máquinas del taller**\n\n" + tabla_markdown(
        filas,
        ["id_maquina", "codigo_maquina", "nombre_maquina", "tipo_maquina", "estado"],
    )


def respuesta_proveedores() -> str:
    filas = db.obtener_proveedores()
    return "🚚 **Proveedores registrados**\n\n" + tabla_markdown(
        filas,
        ["id_proveedor", "nombre_proveedor", "tipo_proveedor", "especialidad", "estado"],
    )


def respuesta_cotizaciones() -> str:
    filas = db.obtener_cotizaciones_pendientes()
    return "📝 **Cotizaciones pendientes por aprobar**\n\n" + tabla_markdown(
        filas,
        ["id_cotizacion", "folio", "cliente_nombre", "pieza_solicitada", "precio_final", "estado_orden"],
    )


def respuesta_produccion() -> str:
    filas = db.obtener_ordenes_produccion()
    return "🏭 **Órdenes aprobadas o en producción**\n\n" + tabla_markdown(
        filas,
        ["id_cotizacion", "folio", "cliente_nombre", "pieza_solicitada", "fecha_entrega_estimada", "estado_orden"],
    )


def detectar_intencion(mensaje: str) -> str:
    texto = mensaje.lower().strip()

    comandos = {
        "/help": "ayuda",
        "/inventario": "inventario",
        "/materiales": "materiales",
        "/herramientas": "herramientas",
        "/maquinas": "maquinas",
        "/máquinas": "maquinas",
        "/proveedores": "proveedores",
        "/cotizaciones": "cotizaciones",
        "/produccion": "produccion",
        "/producción": "produccion",
        "/limpiar": "limpiar",
    }

    if texto in comandos:
        return comandos[texto]

    if any(p in texto for p in ["cotizaciones pendientes", "por aprobar", "faltan por aprobar", "sin aprobar"]):
        return "cotizaciones"

    if any(p in texto for p in ["produccion", "producción", "aprobadas", "en produccion", "en producción"]):
        return "produccion"

    if any(p in texto for p in ["herramienta", "herramientas"]):
        return "herramientas"

    if any(p in texto for p in ["material", "materiales", "acero", "aluminio", "bronce", "cobre"]):
        return "materiales"

    if any(p in texto for p in ["maquina", "máquina", "maquinas", "máquinas", "torno", "fresadora"]):
        return "maquinas"

    if any(p in texto for p in ["proveedor", "proveedores"]):
        return "proveedores"

    if any(p in texto for p in ["inventario", "stock", "almacen", "almacén"]):
        return "inventario"

    if any(p in texto for p in ["agregar", "registrar", "guardar", "actualizar"]):
        return "gestion"

    return "desconocido"


def generar_respuesta(mensaje: str) -> str:
    intencion = detectar_intencion(mensaje)

    try:
        if intencion == "ayuda":
            return obtener_ayuda()
        if intencion == "inventario":
            return respuesta_inventario()
        if intencion == "materiales":
            return respuesta_materiales()
        if intencion == "herramientas":
            return respuesta_herramientas()
        if intencion == "maquinas":
            return respuesta_maquinas()
        if intencion == "proveedores":
            return respuesta_proveedores()
        if intencion == "cotizaciones":
            return respuesta_cotizaciones()
        if intencion == "produccion":
            return respuesta_produccion()
        if intencion == "limpiar":
            return "__LIMPIAR_CHAT__"
        if intencion == "gestion":
            return """
Puedo ayudarte a consultar datos desde el chat, pero para **guardar o actualizar** usa la pestaña **Inventario y gestión**.

Ahí puedes:

- Agregar materiales.
- Actualizar stock de materiales.
- Agregar herramientas.
- Actualizar stock/estado de herramientas.
- Cambiar estado de máquinas.
- Registrar proveedores.
- Aprobar cotizaciones para pasarlas a producción.
"""

    except db.DatabaseError as exc:
        return f"⚠️ {exc}"

    return """
No estoy seguro de qué necesitas hacer.

Puedes escribir `/help` para ver los comandos disponibles.

Ejemplos:

- `/inventario`
- `/herramientas`
- `/materiales`
- `/cotizaciones`
- `/produccion`
"""
