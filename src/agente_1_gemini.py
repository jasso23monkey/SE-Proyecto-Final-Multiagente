import json
import os

from dotenv import load_dotenv
from google import genai

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")


def gemini_disponible():
    return bool(API_KEY)


def interpretar_mensaje_con_gemini(mensaje: str) -> dict:
    if not API_KEY:
        raise RuntimeError("No se encontró GEMINI_API_KEY en el archivo .env")

    client = genai.Client(api_key=API_KEY)

    prompt = f"""
Eres el Agente 1 de ForgeFlow ERP, un sistema experto para taller de torno y fresadora.

Tu tarea es convertir el mensaje del usuario en JSON.

Acciones posibles:
- consultar_inventario
- consultar_materiales
- consultar_herramientas
- consultar_maquinas
- consultar_proveedores
- consultar_cotizaciones
- consultar_produccion
- generar_cotizacion
- desconocido

Devuelve SOLO JSON válido, sin markdown.

Formato:
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
  "requerimientos_cliente": ""
}}

Mensaje del usuario:
{mensaje}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    texto = response.text.strip()

    if texto.startswith("```"):
        texto = texto.replace("```json", "").replace("```", "").strip()

    return json.loads(texto)