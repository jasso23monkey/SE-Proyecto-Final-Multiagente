from datetime import datetime


def obtener_mensaje_bienvenida():
    return """
👋 **Bienvenido a ForgeFlow ERP**

Soy el **Agente 1 - Atención al Cliente**.

Por ahora puedo ayudarte a iniciar solicitudes, consultar comandos del sistema y simular algunos flujos básicos del taller.

Puedes escribir comandos como:

- `/help` → Ver comandos disponibles.
- `/cotizaciones` → Ver cotizaciones pendientes por aprobar.
- `/produccion` → Ver cotizaciones aprobadas listas para producción.
- `/inventario` → Consultar opciones de inventario.
- `/nueva_cotizacion` → Iniciar una cotización.
- `/limpiar` → Limpiar el historial del chat.

También puedes escribirme en lenguaje natural, por ejemplo:

> Necesito realizar una cotización  
> Quiero ver las cotizaciones pendientes  
> Muéstrame lo que está en producción  
> Necesito revisar el inventario
"""


def obtener_ayuda():
    return """
📌 **Comandos disponibles**

| Comando | Función |
|---|---|
| `/help` | Muestra esta ayuda. |
| `/cotizaciones` | Muestra cotizaciones pendientes por aprobar. |
| `/produccion` | Muestra cotizaciones aprobadas/listas para producción. |
| `/inventario` | Muestra opciones relacionadas con inventario. |
| `/nueva_cotizacion` | Inicia el flujo para una nueva cotización. |
| `/limpiar` | Limpia el historial del chat. |

También puedes usar lenguaje natural:

- "Necesito hacer una cotización"
- "Quiero ver cotizaciones pendientes"
- "Muéstrame la producción"
- "Revisa el inventario"
"""


def obtener_cotizaciones_demo():
    return """
📝 **Cotizaciones pendientes por aprobar**

Estas son cotizaciones de ejemplo para el prototipo:

| ID | Cliente | Pieza | Estado |
|---|---|---|---|
| COT-001 | Taller Mecánico López | Engrane recto | Pendiente de aprobación |
| COT-002 | FlexoPrint GDL | Rodillo de aluminio | Pendiente de aprobación |
| COT-003 | Empaques Rivera | Buje de bronce ranurado | Pendiente de aprobación |

⚠️ En el siguiente commit, esta información se tomará directamente desde la base de datos.
"""


def obtener_produccion_demo():
    return """
🏭 **Cotizaciones aprobadas / producción**

Estas órdenes son de ejemplo para el prototipo:

| ID | Cliente | Trabajo | Estado |
|---|---|---|---|
| ORD-001 | Industrias Ramírez | Rodillo completo | En producción |
| ORD-002 | Maquinados del Centro | Engrane helicoidal | Programado |
| ORD-003 | FlexoPrint GDL | Yunque completo | En espera de material |

⚠️ En el siguiente commit, esta información se conectará con SQLite.
"""


def obtener_inventario_demo():
    return """
📦 **Módulo de inventario**

En este prototipo inicial puedo reconocer solicitudes relacionadas con:

- Materiales del taller.
- Herramientas.
- Máquinas.
- Proveedores.

Ejemplos de mensajes:

> Quiero revisar el inventario  
> Necesito agregar una herramienta  
> Consulta las máquinas disponibles  
> Revisa proveedores de acero  

⚠️ El registro y consulta real de inventario se conectará en el segundo commit.
"""


def iniciar_cotizacion():
    return """
🧾 **Nueva cotización iniciada**

Para comenzar una cotización necesito algunos datos:

1. Nombre del cliente.
2. Tipo de pieza.
3. Material requerido.
4. Cantidad.
5. Medidas aproximadas.
6. Proceso requerido, si lo conoces.

Ejemplo:

> Cliente: FlexoPrint GDL, necesita 2 engranes rectos de acero 1018 de 4 pulgadas.

Por ahora este flujo solo identifica la intención. En el segundo commit se conectará con la base de datos y después con el motor de inferencia.
"""


def detectar_intencion(mensaje):
    """
    Detecta comandos y lenguaje natural básico.
    Esta versión pertenece al primer commit.
    Más adelante puede sustituirse por Gemini, Ollama o un clasificador más avanzado.
    """

    texto = mensaje.lower().strip()

    # Comandos directos
    if texto == "/help":
        return "ayuda"

    if texto == "/cotizaciones":
        return "cotizaciones_pendientes"

    if texto == "/produccion":
        return "produccion"

    if texto == "/inventario":
        return "inventario"

    if texto == "/nueva_cotizacion":
        return "nueva_cotizacion"

    if texto == "/limpiar":
        return "limpiar"

    # Lenguaje natural: cotización
    palabras_cotizacion = [
        "cotizacion",
        "cotización",
        "cotizar",
        "presupuesto",
        "precio",
        "cuanto cuesta",
        "cuánto cuesta",
        "necesito realizar una cotizacion",
        "necesito realizar una cotización",
        "hacer una cotizacion",
        "hacer una cotización"
    ]

    if any(palabra in texto for palabra in palabras_cotizacion):
        return "nueva_cotizacion"

    # Lenguaje natural: cotizaciones pendientes
    palabras_pendientes = [
        "cotizaciones pendientes",
        "pendientes por aprobar",
        "faltan por aprobar",
        "por aprobar",
        "sin aprobar"
    ]

    if any(palabra in texto for palabra in palabras_pendientes):
        return "cotizaciones_pendientes"

    # Lenguaje natural: producción
    palabras_produccion = [
        "produccion",
        "producción",
        "aprobadas",
        "ordenes aprobadas",
        "órdenes aprobadas",
        "trabajos aprobados",
        "en produccion",
        "en producción"
    ]

    if any(palabra in texto for palabra in palabras_produccion):
        return "produccion"

    # Lenguaje natural: inventario
    palabras_inventario = [
        "inventario",
        "herramienta",
        "herramientas",
        "material",
        "materiales",
        "maquina",
        "máquina",
        "maquinas",
        "máquinas",
        "proveedor",
        "proveedores",
        "stock"
    ]

    if any(palabra in texto for palabra in palabras_inventario):
        return "inventario"

    return "desconocido"


def generar_respuesta(mensaje):
    intencion = detectar_intencion(mensaje)

    if intencion == "ayuda":
        return obtener_ayuda()

    if intencion == "cotizaciones_pendientes":
        return obtener_cotizaciones_demo()

    if intencion == "produccion":
        return obtener_produccion_demo()

    if intencion == "inventario":
        return obtener_inventario_demo()

    if intencion == "nueva_cotizacion":
        return iniciar_cotizacion()

    if intencion == "limpiar":
        return "__LIMPIAR_CHAT__"

    return """
No estoy seguro de qué necesitas hacer.

Puedes escribir `/help` para ver los comandos disponibles.

También puedes probar con frases como:

- Necesito realizar una cotización.
- Quiero ver cotizaciones pendientes.
- Muéstrame la producción.
- Necesito revisar el inventario.
"""