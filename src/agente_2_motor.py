import json
from datetime import datetime, timedelta

from src import db


def cargar_lista_json(valor):
    """
    Convierte un campo JSON o texto separado por comas en lista.
    Sirve para tolerar datos antiguos y datos nuevos.
    """
    if not valor:
        return []

    if isinstance(valor, list):
        return valor

    try:
        resultado = json.loads(valor)
        if isinstance(resultado, list):
            return resultado
        return []
    except Exception:
        return [item.strip() for item in str(valor).split(",") if item.strip()]


def generar_folio():
    fecha = datetime.now().strftime("%Y%m%d")
    total = db.contar_tabla("Cotizaciones_Ordenes") + 1
    return f"COT-{fecha}-{total:03d}"


def estimar_fecha_entrega(horas_estimadas, requiere_validacion=True):
    """
    Estimación sencilla:
    - 8 horas de trabajo por día.
    - Si requiere validación, se agrega 1 día extra.
    """
    dias_trabajo = max(1, round(horas_estimadas / 8))
    if requiere_validacion:
        dias_trabajo += 1

    fecha = datetime.now() + timedelta(days=dias_trabajo)
    return fecha.strftime("%Y-%m-%d")


def buscar_mejor_material(material_solicitado, perfil_requerido=None):
    materiales = db.obtener_materiales()

    material_solicitado = (material_solicitado or "").lower().strip()
    perfil_requerido = (perfil_requerido or "").lower().strip()

    candidatos = []

    for material in materiales:
        nombre = str(material.get("material", "")).lower()
        perfil = str(material.get("perfil", "")).lower()
        estado = material.get("estado", "")

        coincide_material = material_solicitado in nombre if material_solicitado else True
        coincide_perfil = perfil_requerido in perfil if perfil_requerido else True
        disponible = estado in ["DISPONIBLE", "BAJO_STOCK"]

        if coincide_material and coincide_perfil and disponible:
            candidatos.append(material)

    if candidatos:
        candidatos.sort(key=lambda x: float(x.get("cantidad_disponible", 0)), reverse=True)
        return candidatos[0]

    return None


def obtener_tarifa_por_concepto(concepto):
    tarifas = db.obtener_tarifas_activas()
    for tarifa in tarifas:
        if tarifa["concepto_proceso"] == concepto:
            return tarifa
    return None


def calcular_costos(plantilla, material_encontrado, cantidad_piezas):
    operaciones = cargar_lista_json(plantilla.get("operaciones_base_json"))
    tiempo_base = float(plantilla.get("tiempo_base_horas") or 1.0)

    if not operaciones:
        operaciones = ["Ajuste_Manual"]

    horas_estimadas = max(tiempo_base * cantidad_piezas, 1.0)

    costo_materiales = 0.0
    if material_encontrado:
        costo_unitario = float(material_encontrado.get("costo_unitario") or 0)
        costo_materiales = costo_unitario * cantidad_piezas

    costo_maquinado = 0.0
    margen_promedio = 20.0
    detalle_procesos = []

    horas_por_operacion = horas_estimadas / len(operaciones)

    for operacion in operaciones:
        tarifa = obtener_tarifa_por_concepto(operacion)

        if tarifa:
            costo_base = float(tarifa.get("costo_base") or 0)
            tiempo_minimo = float(tarifa.get("tiempo_minimo_horas") or 0)
            margen_promedio = float(tarifa.get("margen_utilidad_porcentaje") or margen_promedio)

            horas_cobradas = max(horas_por_operacion, tiempo_minimo)
            subtotal = costo_base * horas_cobradas
        else:
            costo_base = 250.0
            horas_cobradas = horas_por_operacion
            subtotal = costo_base * horas_cobradas

        costo_maquinado += subtotal

        detalle_procesos.append({
            "proceso": operacion,
            "horas_estimadas": round(horas_cobradas, 2),
            "costo_estimado": round(subtotal, 2)
        })

    costo_herramientas = 0.0
    costo_servicios_externos = 0.0
    costo_total = costo_materiales + costo_herramientas + costo_maquinado + costo_servicios_externos
    precio_final = costo_total * (1 + margen_promedio / 100)

    return {
        "operaciones": operaciones,
        "detalle_procesos": detalle_procesos,
        "costo_materiales": round(costo_materiales, 2),
        "costo_herramientas": round(costo_herramientas, 2),
        "costo_maquinado": round(costo_maquinado, 2),
        "costo_servicios_externos": round(costo_servicios_externos, 2),
        "costo_total": round(costo_total, 2),
        "margen_utilidad_porcentaje": round(margen_promedio, 2),
        "precio_final": round(precio_final, 2),
        "horas_maquinado_estimadas": round(horas_estimadas, 2)
    }


def evaluar_reglas_basicas(plantilla, material_encontrado, cantidad_piezas):
    reglas_aplicadas = []
    advertencias = []
    requiere_validacion = False

    if plantilla:
        reglas_aplicadas.append({
            "regla": "R_PLANTILLA_DETECTADA",
            "explicacion": f"Se detectó una plantilla técnica para la pieza '{plantilla['nombre_pieza']}'."
        })
    else:
        reglas_aplicadas.append({
            "regla": "R_PLANTILLA_NO_ENCONTRADA",
            "explicacion": "No se encontró una plantilla exacta para la pieza solicitada."
        })
        advertencias.append("La cotización requiere revisión porque no existe plantilla técnica exacta.")
        requiere_validacion = True

    if material_encontrado:
        cantidad_disponible = float(material_encontrado.get("cantidad_disponible") or 0)

        if cantidad_disponible >= cantidad_piezas:
            reglas_aplicadas.append({
                "regla": "R_MATERIAL_DISPONIBLE",
                "explicacion": "El material solicitado existe en inventario con disponibilidad suficiente estimada."
            })
        else:
            reglas_aplicadas.append({
                "regla": "R_MATERIAL_INSUFICIENTE",
                "explicacion": "El material existe, pero la cantidad disponible podría no cubrir la solicitud."
            })
            advertencias.append("Revisar inventario antes de aprobar la cotización.")
            requiere_validacion = True
    else:
        reglas_aplicadas.append({
            "regla": "R_MATERIAL_NO_ENCONTRADO",
            "explicacion": "No se encontró material compatible en inventario."
        })
        advertencias.append("Se debe validar material o generar orden de compra.")
        requiere_validacion = True

    return {
        "reglas_aplicadas": reglas_aplicadas,
        "advertencias": advertencias,
        "requiere_validacion": requiere_validacion
    }


def generar_hoja_ruta(operaciones):
    pasos = []

    for i, operacion in enumerate(operaciones, start=1):
        pasos.append(f"{i}. Ejecutar proceso: {operacion}")

    pasos.append("Verificar medidas finales y calidad.")
    pasos.append("Enviar resultado a validación del supervisor.")

    return "\n".join(pasos)


def generar_explicacion(cliente_nombre, pieza_solicitada, material_final, costos, reglas):
    texto = []
    texto.append(f"Se generó una cotización preliminar para el cliente {cliente_nombre}.")
    texto.append(f"Pieza solicitada: {pieza_solicitada}.")
    texto.append(f"Material considerado: {material_final}.")
    texto.append(f"Horas estimadas de maquinado: {costos['horas_maquinado_estimadas']}.")
    texto.append(f"Costo total estimado: ${costos['costo_total']}.")
    texto.append(f"Precio final estimado: ${costos['precio_final']}.")

    texto.append("\nReglas aplicadas:")
    for regla in reglas["reglas_aplicadas"]:
        texto.append(f"- {regla['regla']}: {regla['explicacion']}")

    if reglas["advertencias"]:
        texto.append("\nAdvertencias:")
        for advertencia in reglas["advertencias"]:
            texto.append(f"- {advertencia}")

    return "\n".join(texto)


def generar_cotizacion_preliminar(
    cliente_nombre,
    pieza_solicitada,
    tipo_servicio,
    cantidad_piezas,
    material_solicitado,
    requerimientos_cliente="",
    dimensiones=None,
    id_usuario_creador=None
):
    """
    Función principal del Agente 2.
    Recibe datos estructurados y genera una cotización preliminar.
    """

    if not cliente_nombre.strip():
        raise ValueError("El nombre del cliente es obligatorio.")

    if not pieza_solicitada.strip():
        raise ValueError("La pieza solicitada es obligatoria.")

    if cantidad_piezas <= 0:
        raise ValueError("La cantidad de piezas debe ser mayor a cero.")

    dimensiones = dimensiones or {}

    plantilla = db.obtener_plantilla_por_nombre(pieza_solicitada)

    if plantilla:
        perfil_requerido = plantilla.get("perfil_requerido")
        material_encontrado = buscar_mejor_material(material_solicitado, perfil_requerido)
    else:
        perfil_requerido = None
        material_encontrado = buscar_mejor_material(material_solicitado)

    if not plantilla:
        plantilla = {
            "id_plantilla": None,
            "nombre_pieza": pieza_solicitada,
            "perfil_requerido": perfil_requerido,
            "operaciones_base_json": json.dumps(["Ajuste_Manual"]),
            "tiempo_base_horas": 1.5
        }

    material_final = material_solicitado
    if material_encontrado:
        material_final = material_encontrado["material"]

    costos = calcular_costos(plantilla, material_encontrado, cantidad_piezas)
    reglas = evaluar_reglas_basicas(plantilla, material_encontrado, cantidad_piezas)

    estado = "VALIDACION_PENDIENTE" if reglas["requiere_validacion"] else "COTIZADO"
    fecha_entrega = estimar_fecha_entrega(costos["horas_maquinado_estimadas"], reglas["requiere_validacion"])
    hoja_ruta = generar_hoja_ruta(costos["operaciones"])

    explicacion = generar_explicacion(
        cliente_nombre=cliente_nombre,
        pieza_solicitada=pieza_solicitada,
        material_final=material_final,
        costos=costos,
        reglas=reglas
    )

    folio = generar_folio()

    id_cotizacion = db.crear_cotizacion(
        folio=folio,
        id_usuario_creador=id_usuario_creador,
        cliente_nombre=cliente_nombre,
        cliente_contacto=None,
        cliente_correo=None,
        cliente_telefono=None,
        id_plantilla=plantilla.get("id_plantilla"),
        pieza_solicitada=pieza_solicitada,
        tipo_servicio=tipo_servicio,
        cantidad_piezas=cantidad_piezas,
        dimensiones_json=json.dumps(dimensiones, ensure_ascii=False),
        requerimientos_cliente=requerimientos_cliente,
        material_final=material_final,
        procesos_finales_json=json.dumps(costos["detalle_procesos"], ensure_ascii=False),
        costo_materiales=costos["costo_materiales"],
        costo_herramientas=costos["costo_herramientas"],
        costo_maquinado=costos["costo_maquinado"],
        costo_servicios_externos=costos["costo_servicios_externos"],
        costo_total=costos["costo_total"],
        margen_utilidad_porcentaje=costos["margen_utilidad_porcentaje"],
        precio_final=costos["precio_final"],
        horas_maquinado_estimadas=costos["horas_maquinado_estimadas"],
        fecha_entrega_estimada=fecha_entrega,
        hoja_ruta_instrucciones=hoja_ruta,
        explicacion_inferencia=explicacion,
        estado_orden=estado,
        observaciones="Cotización generada por Agente 2 - Motor de inferencia inicial."
    )

    db.registrar_historial_inferencia(
        id_cotizacion=id_cotizacion,
        agente_origen="MOTOR_INFERENCIA",
        entrada_json=json.dumps({
            "cliente_nombre": cliente_nombre,
            "pieza_solicitada": pieza_solicitada,
            "tipo_servicio": tipo_servicio,
            "cantidad_piezas": cantidad_piezas,
            "material_solicitado": material_solicitado,
            "dimensiones": dimensiones
        }, ensure_ascii=False),
        regla_evaluada="Motor de inferencia inicial",
        condiciones_cumplidas_json=json.dumps(reglas["reglas_aplicadas"], ensure_ascii=False),
        resultado_json=json.dumps({
            "folio": folio,
            "estado": estado,
            "precio_final": costos["precio_final"],
            "requiere_validacion": reglas["requiere_validacion"]
        }, ensure_ascii=False),
        explicacion_generada=explicacion,
        confianza=0.75,
        requiere_validacion=1 if reglas["requiere_validacion"] else 0
    )

    return {
        "id_cotizacion": id_cotizacion,
        "folio": folio,
        "estado": estado,
        "precio_final": costos["precio_final"],
        "costo_total": costos["costo_total"],
        "horas_maquinado_estimadas": costos["horas_maquinado_estimadas"],
        "fecha_entrega_estimada": fecha_entrega,
        "material_final": material_final,
        "operaciones": costos["operaciones"],
        "reglas_aplicadas": reglas["reglas_aplicadas"],
        "advertencias": reglas["advertencias"],
        "hoja_ruta": hoja_ruta,
        "explicacion": explicacion
    }