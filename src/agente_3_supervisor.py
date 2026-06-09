import json
from src import db


def cargar_json_seguro(valor, default=None):
    if default is None:
        default = []

    if not valor:
        return default

    try:
        return json.loads(valor)
    except Exception:
        return default


def formatear_dinero(valor):
    try:
        return f"${float(valor):,.2f}"
    except Exception:
        return "$0.00"


def generar_explicacion_supervisor(cotizacion):
    procesos = cargar_json_seguro(cotizacion.get("procesos_finales_json"), [])

    texto = f"""
## 🧠 Agente 3 - Explicación de la cotización

**Folio:** {cotizacion.get("folio")}  
**Cliente:** {cotizacion.get("cliente_nombre")}  
**Pieza solicitada:** {cotizacion.get("pieza_solicitada")}  
**Cantidad:** {cotizacion.get("cantidad_piezas")}  
**Material considerado:** {cotizacion.get("material_final")}  
**Estado actual:** {cotizacion.get("estado_orden")}

---

## 1. Decisión tomada por el Agente 2

El Agente 2 generó una cotización preliminar usando la pieza solicitada, el material seleccionado, las operaciones de manufactura estimadas y las tarifas registradas en el sistema.

---

## 2. Desglose de costos

| Concepto | Costo |
|---|---:|
| Materiales | {formatear_dinero(cotizacion.get("costo_materiales"))} |
| Herramientas | {formatear_dinero(cotizacion.get("costo_herramientas"))} |
| Maquinado | {formatear_dinero(cotizacion.get("costo_maquinado"))} |
| Servicios externos | {formatear_dinero(cotizacion.get("costo_servicios_externos"))} |
| **Costo total** | **{formatear_dinero(cotizacion.get("costo_total"))}** |
| **Precio final** | **{formatear_dinero(cotizacion.get("precio_final"))}** |

---

## 3. Tiempo estimado

El tiempo estimado de maquinado es de:

**{cotizacion.get("horas_maquinado_estimadas")} horas**

Fecha estimada de entrega:

**{cotizacion.get("fecha_entrega_estimada")}**

---
"""

    if procesos:
        texto += """
## 4. Procesos considerados

| Operación | Máquina / proceso | Tiempo | Costo |
|---|---|---:|---:|
"""
        for proceso in procesos:
            operacion = proceso.get("operacion") or proceso.get("proceso") or "Operación"
            maquina = proceso.get("maquina") or proceso.get("proceso") or "No especificado"
            tiempo = proceso.get("tiempo_min") or proceso.get("horas_estimadas") or ""
            costo = proceso.get("costo") or proceso.get("costo_estimado") or 0

            texto += f"| {operacion} | {maquina} | {tiempo} | {formatear_dinero(costo)} |\n"

    texto += f"""

---

## 5. Explicación generada por el Agente 2

{cotizacion.get("explicacion_inferencia") or "No hay explicación previa registrada."}

---

## 6. Recomendación del Agente 3

"""

    estado = cotizacion.get("estado_orden", "")

    if estado in ["VALIDACION_PENDIENTE", "COTIZADO", "PENDIENTE_APROBACION"]:
        texto += """
La cotización puede ser revisada por el operador.  
Si los costos, tiempos y material son correctos, puede aprobarse para pasar al módulo de producción.
"""
    elif estado == "APROBADO":
        texto += """
La cotización ya fue aprobada.  
Puede enviarse a producción cuando el taller confirme disponibilidad.
"""
    elif estado == "EN_PRODUCCION":
        texto += """
La orden ya se encuentra en producción.  
Se recomienda dar seguimiento al avance del trabajo.
"""
    elif estado == "CANCELADA":
        texto += """
La cotización fue cancelada.  
No debe enviarse a producción.
"""

    return texto


def validar_cotizacion(id_cotizacion, nuevo_estado, observaciones_supervisor=""):
    cotizacion = db.obtener_cotizacion_por_id(id_cotizacion)

    if not cotizacion:
        raise ValueError("No se encontró la cotización seleccionada.")

    explicacion = generar_explicacion_supervisor(cotizacion)

    db.actualizar_estado_cotizacion(id_cotizacion=id_cotizacion,
                                    nuevo_estado=nuevo_estado,
                                    observaciones=observaciones_supervisor
    )

    db.registrar_historial_inferencia(
        id_cotizacion=id_cotizacion,
        agente_origen="AGENTE_3_SUPERVISOR",
        entrada_json=json.dumps(cotizacion, ensure_ascii=False),
        regla_evaluada="Validación de cotización",
        condiciones_cumplidas_json=json.dumps({
            "estado_anterior": cotizacion.get("estado_orden"),
            "estado_nuevo": nuevo_estado
        }, ensure_ascii=False),
        resultado_json=json.dumps({
            "id_cotizacion": id_cotizacion,
            "nuevo_estado": nuevo_estado
        }, ensure_ascii=False),
        explicacion_generada=explicacion,
        confianza=1.0,
        requiere_validacion=0
    )

    return explicacion