import json
import os
import re
import unicodedata

from dotenv import load_dotenv
from google import genai

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")


def gemini_disponible():
    return bool(API_KEY)


def normalizar_texto(texto: str) -> str:
    texto = texto.lower().strip()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    texto = re.sub(r"\s+", " ", texto)
    return texto


def detectar_accion_local(mensaje: str):
    """
    Detecta consultas que NO deben usar Gemini.
    Esto mantiene rápidas y controladas las consultas simples.
    """
    texto = normalizar_texto(mensaje)

    comandos = {
        "/help": "ayuda",
        "/inventario": "consultar_inventario",
        "/materiales": "consultar_materiales",
        "/herramientas": "consultar_herramientas",
        "/maquinas": "consultar_maquinas",
        "/proveedores": "consultar_proveedores",
        "/cotizaciones": "consultar_cotizaciones",
        "/produccion": "consultar_produccion",
        "/limpiar": "limpiar",
    }

    if texto in comandos:
        return comandos[texto]

    # Consultas locales: Gemini NO debe intervenir.
    if any(p in texto for p in [
        "inventario",
        "stock",
        "almacen",
        "almacenamiento",
        "existencias"
    ]):
        return "consultar_inventario"

    if any(p in texto for p in [
        "material",
        "materiales",
        "aceros disponibles",
        "aluminio disponible",
        "bronce disponible",
        "cobre disponible"
    ]):
        # Pero si también dice cotizar, no lo tratamos como consulta local.
        if not parece_solicitud_cotizacion(texto):
            return "consultar_materiales"

    if any(p in texto for p in [
        "herramienta",
        "herramientas",
        "brocas",
        "buriles",
        "machuelos",
        "cortadores"
    ]):
        return "consultar_herramientas"

    if any(p in texto for p in [
        "maquina",
        "maquinas",
        "torno",
        "fresadora",
        "sierra"
    ]):
        if not parece_solicitud_cotizacion(texto):
            return "consultar_maquinas"

    if any(p in texto for p in [
        "proveedor",
        "proveedores",
        "contacto proveedor"
    ]):
        return "consultar_proveedores"

    if any(p in texto for p in [
        "cotizaciones pendientes",
        "pendientes por aprobar",
        "sin aprobar",
        "por aprobar"
    ]):
        return "consultar_cotizaciones"

    if any(p in texto for p in [
        "produccion",
        "en produccion",
        "ordenes aprobadas",
        "trabajos aprobados",
        "aprobadas"
    ]):
        return "consultar_produccion"

    return None


def parece_solicitud_cotizacion(texto: str) -> bool:
    texto = normalizar_texto(texto)

    palabras_cotizacion = [
        "cotiza",
        "cotizar",
        "cotizacion",
        "presupuesto",
        "cuanto cuesta",
        "costo",
        "precio",
        "sacar precio",
        "realizar cotizacion",
        "hacer cotizacion",
        "generar cotizacion"
    ]

    return any(p in texto for p in palabras_cotizacion)


def limpiar_json_respuesta(texto: str) -> str:
    texto = texto.strip()

    if texto.startswith("```"):
        texto = texto.replace("```json", "")
        texto = texto.replace("```", "")
        texto = texto.strip()

    return texto

def limpiar_json(texto: str) -> str:
    texto = texto.strip()
    if texto.startswith("```"):
        texto = texto.replace("```json", "").replace("```", "").strip()
    return texto


def interpretar_intencion_general(mensaje: str) -> dict:
    if not API_KEY:
        raise RuntimeError("No se encontró GEMINI_API_KEY")

    client = genai.Client(api_key=API_KEY)

    prompt = f"""
Eres el Agente 1 de ForgeFlow ERP.

Convierte el mensaje del usuario en JSON.

Acciones permitidas:
- consultar_inventario
- consultar_materiales
- consultar_herramientas
- consultar_maquinas
- consultar_proveedores
- consultar_clientes
- consultar_cotizaciones
- consultar_produccion
- generar_cotizacion
- desconocido

Devuelve SOLO JSON válido.

Formato:
{{
  "accion": "",
  "filtros": {{
    "material": "",
    "estado": "",
    "cliente": "",
    "pieza": "",
    "proveedor": "",
    "maquina": ""
  }},
  "cotizacion": {{
    "cliente_nombre": "",
    "pieza_solicitada": "",
    "cantidad_piezas": 1,
    "material_solicitado": "",
    "tipo_servicio": "FABRICACION",
    "dimensiones": {{
      "diametro_medida_principal": "",
      "largo": "",
      "ancho": "",
      "num_dientes": "",
      "tolerancia": ""
    }},
    "requerimientos_cliente": ""
  }}
}}

Ejemplos:
"muéstrame clientes" -> consultar_clientes
"dame materiales disponibles" -> consultar_materiales
"qué proveedores tengo" -> consultar_proveedores
"cotiza un engrane recto..." -> generar_cotizacion

Mensaje:
{mensaje}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return json.loads(limpiar_json(response.text))


def redactar_respuesta_con_gemini(mensaje_usuario: str, accion: str, datos: list[dict]) -> str:
    if not API_KEY:
        return str(datos)

    client = genai.Client(api_key=API_KEY)

    prompt = f"""
Eres el Agente 1 de ForgeFlow ERP.

El usuario pidió:
{mensaje_usuario}

Acción detectada:
{accion}

Datos reales obtenidos desde SQLite:
{json.dumps(datos, ensure_ascii=False, indent=2)}

Redacta una respuesta clara, breve y útil en español.
No inventes datos.
Si no hay datos, dilo claramente.
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return response.text

def interpretar_mensaje_con_gemini(mensaje: str) -> dict:
    """
    Gemini SOLO se usa para solicitudes de cotización.
    Para consultas simples devuelve una acción local sin llamar al modelo.
    """

    accion_local = detectar_accion_local(mensaje)

    if accion_local:
        return {
            "accion": accion_local,
            "cliente_nombre": "",
            "pieza_solicitada": "",
            "cantidad_piezas": None,
            "material_solicitado": "",
            "tipo_servicio": "",
            "dimensiones": {},
            "requerimientos_cliente": "",
            "origen": "parser_local"
        }

    if not parece_solicitud_cotizacion(mensaje):
        return {
            "accion": "desconocido",
            "cliente_nombre": "",
            "pieza_solicitada": "",
            "cantidad_piezas": None,
            "material_solicitado": "",
            "tipo_servicio": "",
            "dimensiones": {},
            "requerimientos_cliente": "",
            "origen": "parser_local"
        }

    if not API_KEY:
        raise RuntimeError("No se encontró GEMINI_API_KEY en el archivo .env")

    client = genai.Client(api_key=API_KEY)

    prompt = f"""
Eres el Agente 1 de ForgeFlow ERP, un sistema experto para taller de torno y fresadora.

REGLA CRÍTICA:
Solo debes interpretar solicitudes de cotización/fabricación.
Si el usuario pide inventario, materiales, herramientas, máquinas, proveedores, cotizaciones pendientes o producción, NO generes cotización.
En ese caso devuelve:
{{"accion": "desconocido"}}

Tu tarea es convertir una solicitud de cotización en JSON estructurado.

Acción válida para este módulo:
- generar_cotizacion
- desconocido

Devuelve SOLO JSON válido, sin markdown, sin explicaciones.

Nombres de pieza recomendados:
- engrane_recto
- engrane_mamelon
- engrane_helicoidal
- rodillo_aluminio
- rodillo_acero_yunque
- buje_bronce_ranurado
- buje_cobre

Materiales recomendados:
- Acero 1018
- Acero 1045
- Aluminio 6061
- Bronce
- Cobre

Formato obligatorio:
{{
  "accion": "generar_cotizacion",
  "cliente_nombre": "",
  "pieza_solicitada": "",
  "cantidad_piezas": 1,
  "material_solicitado": "",
  "tipo_servicio": "FABRICACION",
  "dimensiones": {{
    "diametro_medida_principal": "",
    "largo": "",
    "ancho": "",
    "num_dientes": "",
    "tolerancia": ""
  }},
  "requerimientos_cliente": "",
  "origen": "gemini"
}}

Criterios:
- Si no hay solicitud de precio, presupuesto, cotización o fabricación, usa "accion": "desconocido".
- Si el usuario dice "engrane recto", usa "engrane_recto".
- Si el usuario dice "engrane helicoidal", usa "engrane_helicoidal".
- Si el usuario dice "buje de bronce", usa "buje_bronce_ranurado" solo si menciona ranura; si no, usa "buje_bronce_ranurado" como aproximación.
- Si el usuario dice "media pulgada de ancho", guarda "ancho": "0.5 pulgadas".
- Si menciona dientes, guarda el número en "num_dientes".
- Si no menciona cantidad, usa 1.
- Si no menciona tipo de servicio, usa "FABRICACION".
- No inventes cliente si no aparece.

Mensaje del usuario:
{mensaje}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    texto = limpiar_json_respuesta(response.text)

    datos = json.loads(texto)

    if "accion" not in datos:
        datos["accion"] = "desconocido"

    datos["origen"] = datos.get("origen", "gemini")

    return datos