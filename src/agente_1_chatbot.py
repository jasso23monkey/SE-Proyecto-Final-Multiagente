import re
import unicodedata

from src import db
from src import agente_2_motor


# ============================================================
# MENSAJES BASE DEL AGENTE 1
# ============================================================

def obtener_mensaje_bienvenida() -> str:
    return """
👋 **Bienvenido a ForgeFlow ERP**

Soy el **Agente 1 - Atención al Cliente**.

Puedo ayudarte a consultar información real de la base de datos, ubicar módulos del sistema y generar cotizaciones preliminares por chat.

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

También puedes escribir una solicitud natural, por ejemplo:

> Cotiza 2 engranes rectos de Acero 1018 para Taller López, diámetro 4 pulgadas, largo 1 pulgada.

Para agregar o actualizar inventario también puedes usar la pestaña **Inventario y gestión**.
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

Para generar una cotización por chat, usa una frase como:

> Cotiza 2 engranes rectos de Acero 1018 para Taller López, diámetro 4 pulgadas, largo 1 pulgada.

Datos recomendados para cotizar:

1. Cliente.
2. Cantidad de piezas.
3. Pieza solicitada.
4. Material.
5. Medidas principales.
6. Requerimientos especiales.
"""


# ============================================================
# UTILIDADES PARA TABLAS EN CHAT
# ============================================================

def tabla_markdown(filas: list[dict], columnas: list[str], max_filas: int = 10) -> str:
    if not filas:
        return "No hay registros para mostrar."

    filas_mostradas = filas[:max_filas]

    encabezado = "| " + " | ".join(columnas) + " |"
    separador = "| " + " | ".join(["---"] * len(columnas)) + " |"
    cuerpo = []

    for fila in filas_mostradas:
        valores = []
        for columna in columnas:
            valor = fila.get(columna, "")
            valores.append(str(valor if valor is not None else ""))
        cuerpo.append("| " + " | ".join(valores) + " |")

    extra = ""
    if len(filas) > max_filas:
        extra = "\n\n_Se muestran solo los primeros registros. Para ver todo, usa la pestaña de gestión._"

    return "\n".join([encabezado, separador] + cuerpo) + extra


# ============================================================
# RESPUESTAS DE CONSULTA
# ============================================================

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
        [
            "id_material",
            "codigo_material",
            "material",
            "perfil",
            "cantidad_disponible",
            "unidad_inventario",
            "estado"
        ],
    )


def respuesta_herramientas() -> str:
    filas = db.obtener_herramientas()
    return "🧰 **Herramientas registradas**\n\n" + tabla_markdown(
        filas,
        [
            "id_herramienta",
            "codigo_herramienta",
            "nombre_herramienta",
            "tipo",
            "stock_unidades",
            "estado"
        ],
    )


def respuesta_maquinas() -> str:
    filas = db.obtener_maquinas()
    return "🏭 **Máquinas del taller**\n\n" + tabla_markdown(
        filas,
        [
            "id_maquina",
            "codigo_maquina",
            "nombre_maquina",
            "tipo_maquina",
            "estado"
        ],
    )


def respuesta_proveedores() -> str:
    filas = db.obtener_proveedores()
    return "🚚 **Proveedores registrados**\n\n" + tabla_markdown(
        filas,
        [
            "id_proveedor",
            "nombre_proveedor",
            "tipo_proveedor",
            "especialidad",
            "estado"
        ],
    )


def respuesta_cotizaciones() -> str:
    filas = db.obtener_cotizaciones_pendientes()
    return "📝 **Cotizaciones pendientes por aprobar**\n\n" + tabla_markdown(
        filas,
        [
            "id_cotizacion",
            "folio",
            "cliente_nombre",
            "pieza_solicitada",
            "precio_final",
            "estado_orden"
        ],
    )


def respuesta_produccion() -> str:
    filas = db.obtener_ordenes_produccion()
    return "🏭 **Órdenes aprobadas o en producción**\n\n" + tabla_markdown(
        filas,
        [
            "id_cotizacion",
            "folio",
            "cliente_nombre",
            "pieza_solicitada",
            "fecha_entrega_estimada",
            "estado_orden"
        ],
    )


# ============================================================
# PARSER BÁSICO PARA COTIZACIONES POR CHAT
# ============================================================

def normalizar_texto(texto: str) -> str:
    texto = texto.lower().strip()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    texto = texto.replace("_", " ")
    texto = re.sub(r"\s+", " ", texto)
    return texto


def singularizar_basico(texto: str) -> str:
    palabras = texto.split()
    resultado = []

    for palabra in palabras:
        if len(palabra) > 4 and palabra.endswith("nes"):
            # engranes -> engrane
            palabra = palabra[:-1]
        elif len(palabra) > 4 and palabra.endswith("es"):
            # materiales -> material
            palabra = palabra[:-2]
        elif len(palabra) > 3 and palabra.endswith("s"):
            # rectos -> recto
            palabra = palabra[:-1]

        resultado.append(palabra)

    return " ".join(resultado)


def detectar_pieza_desde_texto(texto: str):
    texto_norm = singularizar_basico(normalizar_texto(texto))

    try:
        plantillas = db.obtener_plantillas()
    except Exception:
        plantillas = []

    # Primero intenta detectar usando las plantillas reales de la BD.
    for plantilla in plantillas:
        nombre_real = plantilla["nombre_pieza"]
        nombre_norm = singularizar_basico(normalizar_texto(nombre_real))

        if nombre_norm in texto_norm:
            return nombre_real

    # Fallback con alias comunes por si el usuario escribe más natural.
    alias_piezas = {
        "engrane recto": "engrane_recto",
        "engranes rectos": "engrane_recto",
        "engrane mamelon": "engrane_mamelon",
        "engrane con mamelon": "engrane_mamelon",
        "engrane helicoidal": "engrane_helicoidal",
        "engranes helicoidales": "engrane_helicoidal",
        "rodillo aluminio": "rodillo_aluminio",
        "rodillo de aluminio": "rodillo_aluminio",
        "rodillos de aluminio": "rodillo_aluminio",
        "rodillo acero": "rodillo_acero_yunque",
        "rodillo de acero": "rodillo_acero_yunque",
        "rodillo yunque": "rodillo_acero_yunque",
        "buje bronce": "buje_bronce_ranurado",
        "buje de bronce": "buje_bronce_ranurado",
        "bujes de bronce": "buje_bronce_ranurado",
        "buje bronce ranurado": "buje_bronce_ranurado",
        "buje cobre": "buje_cobre",
        "buje de cobre": "buje_cobre",
        "bujes de cobre": "buje_cobre",
    }

    for alias, nombre_plantilla in alias_piezas.items():
        alias_norm = singularizar_basico(normalizar_texto(alias))

        if alias_norm in texto_norm:
            return nombre_plantilla

    return None


def detectar_material_desde_texto(texto: str):
    texto_norm = normalizar_texto(texto)

    try:
        materiales = db.obtener_materiales()
    except Exception:
        materiales = []

    materiales_ordenados = sorted(
        materiales,
        key=lambda m: len(str(m.get("material", ""))),
        reverse=True
    )

    for material in materiales_ordenados:
        nombre_material = str(material.get("material", ""))
        material_norm = normalizar_texto(nombre_material)

        if material_norm and material_norm in texto_norm:
            return nombre_material

    materiales_comunes = [
        "Acero 1018",
        "Acero 1045",
        "Aluminio 6061",
        "Bronce",
        "Cobre"
    ]

    for material in materiales_comunes:
        if normalizar_texto(material) in texto_norm:
            return material

    return None


def extraer_cantidad(texto: str):
    texto_norm = normalizar_texto(texto)

    # Busca números escritos con dígitos.
    match = re.search(r"\b(\d+)\b", texto_norm)
    if match:
        cantidad = int(match.group(1))
        if cantidad > 0:
            return cantidad

    # Fallback para números escritos en texto.
    numeros_texto = {
        "uno": 1,
        "una": 1,
        "dos": 2,
        "tres": 3,
        "cuatro": 4,
        "cinco": 5,
        "seis": 6,
        "siete": 7,
        "ocho": 8,
        "nueve": 9,
        "diez": 10,
    }

    for palabra, numero in numeros_texto.items():
        if re.search(rf"\b{palabra}\b", texto_norm):
            return numero

    return None


def extraer_cliente(texto: str):
    patrones = [
        r"cliente\s*:\s*([^,.]+)",
        r"para\s+([^,.]+)",
        r"a nombre de\s+([^,.]+)"
    ]

    for patron in patrones:
        match = re.search(patron, texto, flags=re.IGNORECASE)
        if match:
            cliente = match.group(1).strip()

            # Limpieza básica para evitar que se coma medidas después del cliente.
            cliente = re.split(
                r"\b(diametro|diámetro|largo|longitud|requiere|con|material|medidas)\b",
                cliente,
                flags=re.IGNORECASE
            )[0].strip()

            if cliente:
                return cliente

    return None


def extraer_dimensiones(texto: str) -> dict:
    dimensiones = {}

    patron_diametro = re.search(
        r"(diametro|diámetro)\s*(de)?\s*([\d.]+\s*(pulgadas|pulgada|cm|mm|in)?)",
        texto,
        flags=re.IGNORECASE
    )

    patron_largo = re.search(
        r"(largo|longitud)\s*(de)?\s*([\d.]+\s*(pulgadas|pulgada|cm|mm|in)?)",
        texto,
        flags=re.IGNORECASE
    )

    patron_tolerancia = re.search(
        r"tolerancia\s*(de)?\s*([^,.]+)",
        texto,
        flags=re.IGNORECASE
    )

    if patron_diametro:
        dimensiones["diametro_medida_principal"] = patron_diametro.group(3).strip()

    if patron_largo:
        dimensiones["largo"] = patron_largo.group(3).strip()

    if patron_tolerancia:
        dimensiones["tolerancia"] = patron_tolerancia.group(2).strip()

    return dimensiones


def extraer_requerimientos(texto: str) -> str:
    patrones = [
        r"requiere\s+(.+)",
        r"con\s+(.+)",
        r"necesita\s+(.+)"
    ]

    for patron in patrones:
        match = re.search(patron, texto, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()

    return ""


def extraer_datos_cotizacion(texto: str) -> dict:
    return {
        "cliente_nombre": extraer_cliente(texto),
        "pieza_solicitada": detectar_pieza_desde_texto(texto),
        "cantidad_piezas": extraer_cantidad(texto),
        "material_solicitado": detectar_material_desde_texto(texto),
        "tipo_servicio": "FABRICACION",
        "dimensiones": extraer_dimensiones(texto),
        "requerimientos_cliente": extraer_requerimientos(texto)
    }


def responder_cotizacion_por_chat(texto: str) -> str:
    datos = extraer_datos_cotizacion(texto)

    faltantes = []

    if not datos["cliente_nombre"]:
        faltantes.append("nombre del cliente")

    if not datos["pieza_solicitada"]:
        faltantes.append("tipo de pieza")

    if not datos["cantidad_piezas"]:
        faltantes.append("cantidad de piezas")

    if not datos["material_solicitado"]:
        faltantes.append("material solicitado")

    if faltantes:
        return f"""
🧾 Detecté que quieres generar una cotización, pero faltan datos:

**Datos detectados:**

- Cliente: {datos["cliente_nombre"] or "No detectado"}
- Pieza: {datos["pieza_solicitada"] or "No detectada"}
- Cantidad: {datos["cantidad_piezas"] or "No detectada"}
- Material: {datos["material_solicitado"] or "No detectado"}

**Datos faltantes:**
{chr(10).join(f"- {dato}" for dato in faltantes)}

Puedes escribirlo así:

> Cotiza 2 engranes rectos de Acero 1018 para Taller López, diámetro 4 pulgadas, largo 1 pulgada.
"""

    try:
        resultado = agente_2_motor.generar_cotizacion_preliminar(
            cliente_nombre=datos["cliente_nombre"],
            pieza_solicitada=datos["pieza_solicitada"],
            tipo_servicio=datos["tipo_servicio"],
            cantidad_piezas=int(datos["cantidad_piezas"]),
            material_solicitado=datos["material_solicitado"],
            requerimientos_cliente=datos["requerimientos_cliente"],
            dimensiones=datos["dimensiones"]
        )

        texto_respuesta = f"""
✅ **Cotización generada correctamente**

**Folio:** {resultado["folio"]}  
**Estado:** {resultado["estado"]}  
**Cliente:** {datos["cliente_nombre"]}  
**Pieza:** {datos["pieza_solicitada"]}  
**Material:** {resultado["material_final"]}  
**Precio final estimado:** ${resultado["precio_final"]:.2f}  
**Horas estimadas:** {resultado["horas_maquinado_estimadas"]}  
**Fecha estimada de entrega:** {resultado["fecha_entrega_estimada"]}

### Explicación del Agente 2

{resultado["explicacion"]}

### Hoja de ruta preliminar

```text
{resultado["hoja_ruta"]}
```
"""

        if resultado["advertencias"]:
            texto_respuesta += "\n### Advertencias\n"
            for advertencia in resultado["advertencias"]:
                texto_respuesta += f"- {advertencia}\n"

        return texto_respuesta

    except Exception as error:
        return f"⚠️ No se pudo generar la cotización: {error}"


# ============================================================
# DETECCIÓN DE INTENCIONES
# ============================================================

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

    # IMPORTANTE:
    # Esto va antes de "materiales", porque una cotización normalmente contiene palabras como acero o aluminio.
    if any(p in texto for p in [
        "cotiza",
        "cotizar",
        "cotizacion",
        "cotización",
        "presupuesto",
        "cuanto cuesta",
        "cuánto cuesta",
        "hacer una cotizacion",
        "hacer una cotización",
        "generar una cotizacion",
        "generar una cotización",
        "necesito una cotizacion",
        "necesito una cotización",
        "realizar una cotizacion",
        "realizar una cotización"
    ]):
        return "nueva_cotizacion"

    if any(p in texto for p in [
        "cotizaciones pendientes",
        "por aprobar",
        "faltan por aprobar",
        "sin aprobar"
    ]):
        return "cotizaciones"

    if any(p in texto for p in [
        "produccion",
        "producción",
        "aprobadas",
        "en produccion",
        "en producción"
    ]):
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


# ============================================================
# RESPUESTA PRINCIPAL DEL AGENTE 1
# ============================================================

def generar_respuesta(mensaje: str) -> str:
    intencion = detectar_intencion(mensaje)

    try:
        if intencion == "ayuda":
            return obtener_ayuda()

        if intencion == "inventario":
            return respuesta_inventario()

        if intencion == "nueva_cotizacion":
            return responder_cotizacion_por_chat(mensaje)

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

Más adelante, con Gemini, podré extraer estos datos desde lenguaje natural y pedir confirmación antes de guardarlos.
"""

    except db.DatabaseError as exc:
        return f"⚠️ {exc}"

    except Exception as exc:
        return f"⚠️ Ocurrió un error al procesar la solicitud: {exc}"

    return """
No estoy seguro de qué necesitas hacer.

Puedes escribir `/help` para ver los comandos disponibles.

Ejemplos:

- `/inventario`
- `/herramientas`
- `/materiales`
- `/cotizaciones`
- `/produccion`

Para generar una cotización por chat puedes escribir:

> Cotiza 2 engranes rectos de Acero 1018 para Taller López, diámetro 4 pulgadas, largo 1 pulgada.
"""