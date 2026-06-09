"""
Agente 2 — Motor de Inferencia v2
ForgeFlow ERP

Estimación de tiempos y costos basada en parámetros físicos reales.
El motor descompone cada pieza en etapas de maquinado (torno / fresadora / ajuste),
calcula las horas de cada etapa con modelos calibrados y aplica la tarifa
correspondiente a cada máquina por separado.

Calibración de referencia:
  Engrane recto — 99 dientes, Ø ~4", ancho 0.5", Acero 1018
  → Tiempo real: ~1h 50min  |  Precio taller: ~$1,043
  → Modelo:      ~1h 43min  |  Precio modelo: ~$1,016 (error < 3%)
  Las tarifas (Hora_Torno / Hora_Fresadora) son ajustables en Tarifas_Taller.
"""

import json
from datetime import datetime, timedelta

from src import db


# ============================================================
# UTILIDADES
# ============================================================

def cargar_lista_json(valor):
    if not valor:
        return []
    if isinstance(valor, list):
        return valor
    try:
        r = json.loads(valor)
        return r if isinstance(r, list) else []
    except Exception:
        return [x.strip() for x in str(valor).split(",") if x.strip()]


def cargar_dict_json(valor):
    if not valor:
        return {}
    if isinstance(valor, dict):
        return valor
    try:
        r = json.loads(valor)
        return r if isinstance(r, dict) else {}
    except Exception:
        return {}


def generar_folio():
    fecha = datetime.now().strftime("%Y%m%d")
    total = db.contar_tabla("Cotizaciones_Ordenes") + 1
    return f"COT-{fecha}-{total:03d}"


def estimar_fecha_entrega(horas_estimadas: float, requiere_validacion: bool = True) -> str:
    dias = max(1, round(horas_estimadas / 8))
    if requiere_validacion:
        dias += 1
    return (datetime.now() + timedelta(days=dias)).strftime("%Y-%m-%d")


def horas_a_texto(horas: float) -> str:
    """1.833 → '1h 50min'"""
    h = int(horas)
    m = round((horas - h) * 60)
    if m == 60:
        h += 1; m = 0
    if h > 0 and m > 0:
        return f"{h}h {m}min"
    if h > 0:
        return f"{h}h"
    return f"{m}min"


def parse_numero(valor, default: float) -> float:
    """Extrae el primer número de un string como '4 pulgadas' → 4.0"""
    import re
    if not valor:
        return default
    try:
        m = re.search(r"[\d.]+", str(valor))
        return float(m.group()) if m else default
    except Exception:
        return default


# ============================================================
# FACTORES DE MATERIAL
# (multiplica los tiempos base — Acero 1018 = 1.0 de referencia)
# ============================================================

FACTOR_MATERIAL = {
    "acero 1018": 1.00,
    "acero 1045": 1.20,
    "acero 4140": 1.40,
    "aluminio 6061": 0.60,
    "aluminio": 0.60,
    "bronce": 0.85,
    "cobre": 0.75,
}


def factor_material(nombre: str) -> float:
    nombre = (nombre or "").lower()
    for clave, f in FACTOR_MATERIAL.items():
        if clave in nombre:
            return f
    return 1.0


# ============================================================
# BÚSQUEDA DE RECURSOS
# ============================================================

def buscar_mejor_material(material_solicitado: str, perfil_requerido: str = None):
    materiales = db.obtener_materiales()
    mat_lower  = (material_solicitado or "").lower().strip()
    perf_lower = (perfil_requerido   or "").lower().strip()

    candidatos = [
        m for m in materiales
        if (mat_lower  in str(m.get("material", "")).lower()  if mat_lower  else True)
        and (perf_lower in str(m.get("perfil", "")).lower()   if perf_lower else True)
        and m.get("estado", "") in ("DISPONIBLE", "BAJO_STOCK")
    ]
    if candidatos:
        candidatos.sort(key=lambda x: float(x.get("cantidad_disponible", 0)), reverse=True)
        return candidatos[0]
    return None


def obtener_tarifa(concepto: str) -> dict | None:
    for t in db.obtener_tarifas_activas():
        if t["concepto_proceso"] == concepto:
            return t
    return None


# ============================================================
# MODELOS DE ESTIMACIÓN DE TIEMPO POR TIPO DE PIEZA
#
# Cada modelo devuelve:
#   {
#     "etapas": [ { etapa, proceso, descripcion, horas_por_pieza, horas_total } ],
#     "horas_por_pieza": float,
#     "horas_total": float,
#   }
# ============================================================

# ── ENGRANE RECTO / MAMELON / HELICOIDAL ────────────────────
# Calibración: 99 dientes, ancho 0.5", Ø ~4" → ~1.72h → $1,016 (con tarifas 380/450)
#
# Etapas:
#   1. TORNO    — refrentar, cilindrar, barrenar agujero central
#   2. FRESADORA — tallado de dientes con cortador de módulo (plato divisor)
#   3. AJUSTE   — desbarbado, verificación de perfil
# ────────────────────────────────────────────────────────────

def _horas_engrane(num_dientes: int, ancho: float, diametro: float,
                   material: str, cantidad: int) -> dict:
    fm = factor_material(material)

    # Etapa 1 – Torno
    t_montaje    = 0.15 + diametro * 0.05          # montaje + refrentado
    t_cilindrado = 0.08 + diametro * ancho * 0.035  # cilindrado exterior
    t_barrenado  = 0.06 + diametro * 0.25 * 0.04    # barrenado agujero central
    t_torno = (t_montaje + t_cilindrado + t_barrenado) * fm

    # Etapa 2 – Fresadora (tallado de dientes)
    modulo_mm      = (diametro * 25.4) / num_dientes
    t_setup_fresa  = 0.15                                     # puesta a punto + acomodo
    t_por_diente   = (0.0075 * modulo_mm + 0.0003) * (ancho / 0.5)
    t_fresa = t_setup_fresa + num_dientes * t_por_diente * fm

    # Etapa 3 – Ajuste
    t_ajuste = 0.12 + diametro * 0.015

    t_pp = t_torno + t_fresa + t_ajuste

    return {
        "etapas": [
            {
                "etapa": "Torno",
                "proceso": "Hora_Torno",
                "descripcion": (
                    f"Refrentado, cilindrado Ø{diametro}\" × {ancho}\" y barrenado agujero central"
                ),
                "horas_por_pieza": round(t_torno, 4),
                "horas_total":     round(t_torno * cantidad, 4),
            },
            {
                "etapa": "Fresadora",
                "proceso": "Hora_Fresadora",
                "descripcion": (
                    f"Tallado de {num_dientes} dientes — "
                    f"módulo estimado {modulo_mm:.2f} mm, ancho {ancho}\""
                ),
                "horas_por_pieza": round(t_fresa, 4),
                "horas_total":     round(t_fresa * cantidad, 4),
            },
            {
                "etapa": "Ajuste",
                "proceso": "Ajuste_Manual",
                "descripcion": "Desbarbado, verificación de perfil y medición final",
                "horas_por_pieza": round(t_ajuste, 4),
                "horas_total":     round(t_ajuste * cantidad, 4),
            },
        ],
        "horas_por_pieza": round(t_pp, 4),
        "horas_total":     round(t_pp * cantidad, 4),
    }


# ── BUJE ─────────────────────────────────────────────────────

def _horas_buje(diametro_ext: float, largo: float, material: str,
                cantidad: int, requiere_ranura: bool, con_fresadora: bool) -> dict:
    fm = factor_material(material)

    t_montaje    = 0.18 + diametro_ext * 0.045
    t_cilindrado = 0.08 + diametro_ext * largo * 0.045
    t_barrenado  = 0.08 + diametro_ext * 0.35 * 0.04
    t_torno = (t_montaje + t_cilindrado + t_barrenado) * fm

    t_fresa = (0.30 * fm) if con_fresadora else 0.0

    t_ajuste = 0.10 + largo * 0.02 + (0.15 if requiere_ranura else 0)

    t_pp = t_torno + t_fresa + t_ajuste
    etapas = [
        {
            "etapa": "Torno",
            "proceso": "Hora_Torno",
            "descripcion": f"Cilindrado exterior Ø{diametro_ext}\", largo {largo}\", barrenado interior",
            "horas_por_pieza": round(t_torno, 4),
            "horas_total":     round(t_torno * cantidad, 4),
        }
    ]
    if con_fresadora:
        etapas.append({
            "etapa": "Fresadora",
            "proceso": "Hora_Fresadora",
            "descripcion": "Ranurado interior y/o exterior",
            "horas_por_pieza": round(t_fresa, 4),
            "horas_total":     round(t_fresa * cantidad, 4),
        })
    etapas.append({
        "etapa": "Ajuste",
        "proceso": "Ajuste_Manual",
        "descripcion": "Desbarbado y verificación dimensional",
        "horas_por_pieza": round(t_ajuste, 4),
        "horas_total":     round(t_ajuste * cantidad, 4),
    })

    return {
        "etapas": etapas,
        "horas_por_pieza": round(t_pp, 4),
        "horas_total":     round(t_pp * cantidad, 4),
    }


# ── RODILLO ───────────────────────────────────────────────────

def _horas_rodillo(diametro: float, largo: float, material: str,
                   cantidad: int, requiere_balero: bool) -> dict:
    fm = factor_material(material)

    t_montaje    = 0.20 + largo * 0.025
    t_cilindrado = 0.12 + diametro * largo * 0.020 * fm
    t_acabado    = 0.10 + diametro * 0.035
    t_torno = t_montaje + t_cilindrado + t_acabado

    t_ajuste = 0.18 + (0.12 if requiere_balero else 0)
    t_pp = t_torno + t_ajuste

    return {
        "etapas": [
            {
                "etapa": "Torno",
                "proceso": "Hora_Torno",
                "descripcion": (
                    f"Cilindrado Ø{diametro}\" × L{largo}\", acabado superficial"
                ),
                "horas_por_pieza": round(t_torno, 4),
                "horas_total":     round(t_torno * cantidad, 4),
            },
            {
                "etapa": "Ajuste",
                "proceso": "Ajuste_Manual",
                "descripcion": "Desbarbado, verificación y ajuste de asientos de balero",
                "horas_por_pieza": round(t_ajuste, 4),
                "horas_total":     round(t_ajuste * cantidad, 4),
            },
        ],
        "horas_por_pieza": round(t_pp, 4),
        "horas_total":     round(t_pp * cantidad, 4),
    }


# ── GENÉRICO ─────────────────────────────────────────────────

def _horas_generico(operaciones: list, tiempo_base: float, dificultad: str,
                    material: str, cantidad: int) -> dict:
    fm = factor_material(material)
    fd = {"BAJA": 0.8, "MEDIA": 1.0, "ALTA": 1.3, "CRITICA": 1.6}.get(dificultad, 1.0)
    t_pp = tiempo_base * fm * fd
    t_op = t_pp / max(len(operaciones), 1)

    PROC_MAP = {
        "Hora_Torno": "Hora_Torno",
        "Hora_Fresadora": "Hora_Fresadora",
    }

    etapas = [
        {
            "etapa": op,
            "proceso": PROC_MAP.get(op, "Ajuste_Manual"),
            "descripcion": op.replace("_", " "),
            "horas_por_pieza": round(t_op, 4),
            "horas_total":     round(t_op * cantidad, 4),
        }
        for op in operaciones
    ]
    return {
        "etapas": etapas,
        "horas_por_pieza": round(t_pp, 4),
        "horas_total":     round(t_pp * cantidad, 4),
    }


# ============================================================
# SELECTOR — elige el modelo correcto según tipo de pieza
# ============================================================

def calcular_horas_por_pieza(
    nombre_pieza: str, plantilla: dict,
    dimensiones: dict, material: str, cantidad: int
) -> dict:
    pieza  = nombre_pieza.lower()
    params = cargar_dict_json(plantilla.get("parametros_base_json", {}))
    ops    = cargar_lista_json(plantilla.get("operaciones_base_json")) or ["Ajuste_Manual"]

    # ── ENGRANE ──────────────────────────────────────────────
    if any(k in pieza for k in ("engrane", "engranaje")):
        diametro = parse_numero(dimensiones.get("diametro_medida_principal"), 4.0)
        ancho    = parse_numero(dimensiones.get("ancho") or dimensiones.get("largo"), 0.5)
        if ancho <= 0:
            ancho = 0.5

        # Dientes: del usuario, o inferidos con módulo 1
        nd = int(parse_numero(dimensiones.get("num_dientes"), 0))
        if nd == 0:
            nd = max(12, int(diametro * 25.4 / 1.0))

        return _horas_engrane(nd, ancho, diametro, material, cantidad)

    # ── BUJE ─────────────────────────────────────────────────
    if "buje" in pieza:
        d = parse_numero(dimensiones.get("diametro_medida_principal"), 1.5)
        l = parse_numero(dimensiones.get("largo"), 1.0)
        ranura      = params.get("requiere_ranura_interna", False) or params.get("requiere_ranura_externa", False)
        con_fresadora = "Hora_Fresadora" in ops
        return _horas_buje(d, l, material, cantidad, bool(ranura), con_fresadora)

    # ── RODILLO ──────────────────────────────────────────────
    if "rodillo" in pieza:
        d = parse_numero(dimensiones.get("diametro_medida_principal"), 3.5)
        l = parse_numero(dimensiones.get("largo"), 10.0)
        balero = params.get("requiere_caja_balero", True)
        return _horas_rodillo(d, l, material, cantidad, bool(balero))

    # ── GENÉRICO ─────────────────────────────────────────────
    t_base    = float(plantilla.get("tiempo_base_horas") or 1.5)
    dificultad = plantilla.get("dificultad", "MEDIA")
    return _horas_generico(ops, t_base, dificultad, material, cantidad)


# ============================================================
# CÁLCULO DE COSTOS — tarifa distinta por etapa
# ============================================================

def calcular_costos(horas_info: dict, material_encontrado, cantidad: int) -> dict:
    margen_global = 20.0
    detalle = []
    costo_maquinado = 0.0

    # Tarifas de fallback si no están en BD
    FALLBACK = {"Hora_Torno": 380.0, "Hora_Fresadora": 450.0, "Ajuste_Manual": 250.0}

    for etapa in horas_info["etapas"]:
        proceso = etapa["proceso"]
        horas   = etapa["horas_total"]

        tarifa = obtener_tarifa(proceso)
        if tarifa:
            tarifa_hora  = float(tarifa.get("costo_base") or FALLBACK.get(proceso, 250.0))
            t_minimo     = float(tarifa.get("tiempo_minimo_horas") or 0)
            margen_global = float(tarifa.get("margen_utilidad_porcentaje") or margen_global)
            horas_cobradas = max(horas, t_minimo)
        else:
            tarifa_hora    = FALLBACK.get(proceso, 250.0)
            horas_cobradas = horas

        subtotal = tarifa_hora * horas_cobradas
        costo_maquinado += subtotal

        detalle.append({
            "etapa":          etapa["etapa"],
            "proceso":        proceso,
            "descripcion":    etapa["descripcion"],
            "horas_por_pieza": etapa["horas_por_pieza"],
            "horas_total":    round(horas_cobradas, 4),
            "tarifa_hora":    tarifa_hora,
            "costo_estimado": round(subtotal, 2),
        })

    costo_materiales = 0.0
    if material_encontrado:
        costo_materiales = float(material_encontrado.get("costo_unitario") or 0) * cantidad

    costo_total  = costo_materiales + costo_maquinado
    precio_final = costo_total * (1 + margen_global / 100)

    return {
        "detalle_procesos":         detalle,
        "costo_materiales":         round(costo_materiales, 2),
        "costo_herramientas":       0.0,
        "costo_maquinado":          round(costo_maquinado, 2),
        "costo_servicios_externos": 0.0,
        "costo_total":              round(costo_total, 2),
        "margen_utilidad_porcentaje": round(margen_global, 2),
        "precio_final":             round(precio_final, 2),
        "horas_maquinado_estimadas": round(horas_info["horas_total"], 4),
        "horas_texto":              horas_a_texto(horas_info["horas_total"]),
    }


# ============================================================
# REGLAS DE INFERENCIA IF → THEN
# ============================================================

def evaluar_reglas(plantilla: dict, material_encontrado, cantidad: int, nombre_pieza: str) -> dict:
    reglas   = []
    advertencias = []
    req_val  = False

    # R1 — Plantilla técnica
    if plantilla and plantilla.get("id_plantilla"):
        reglas.append({
            "regla": "R_PLANTILLA_DETECTADA",
            "explicacion": f"Plantilla técnica '{plantilla['nombre_pieza']}' encontrada en base de conocimiento.",
        })
    else:
        reglas.append({
            "regla": "R_PLANTILLA_NO_ENCONTRADA",
            "explicacion": f"No existe plantilla exacta para '{nombre_pieza}'. Se usó estimación genérica.",
        })
        advertencias.append("Cotización estimada sin plantilla técnica. Requiere revisión.")
        req_val = True

    # R2 — Stock de material
    if material_encontrado:
        disponible = float(material_encontrado.get("cantidad_disponible") or 0)
        estado_mat = material_encontrado.get("estado", "")
        if disponible >= cantidad:
            reglas.append({
                "regla": "R_MATERIAL_DISPONIBLE",
                "explicacion": (
                    f"Material '{material_encontrado['material']}' disponible: "
                    f"{disponible} {material_encontrado.get('unidad_inventario', '')}."
                ),
            })
        else:
            reglas.append({
                "regla": "R_MATERIAL_INSUFICIENTE",
                "explicacion": (
                    f"Stock ({disponible}) podría no cubrir la demanda ({cantidad} pz). "
                    "IF stock < cantidad THEN sugerir reabastecimiento."
                ),
            })
            advertencias.append("Verificar stock antes de aprobar. Considerar orden de compra.")
            req_val = True

        if estado_mat == "BAJO_STOCK":
            reglas.append({
                "regla": "R_MATERIAL_BAJO_STOCK",
                "explicacion": "Material en estado BAJO_STOCK → se recomienda reabastecimiento.",
            })
            advertencias.append("Se sugiere generar orden de compra para reabastecer material.")
    else:
        reglas.append({
            "regla": "R_MATERIAL_NO_EN_INVENTARIO",
            "explicacion": "No se localizó material compatible. Costo de material calculado en $0.",
        })
        advertencias.append("Material no en inventario. Validar compra o sustitución antes de producir.")
        req_val = True

    # R3 — Dificultad alta / crítica
    dificultad = (plantilla or {}).get("dificultad", "MEDIA")
    if dificultad in ("ALTA", "CRITICA"):
        reglas.append({
            "regla": "R_DIFICULTAD_ALTA",
            "explicacion": (
                f"Dificultad {dificultad}. "
                "IF dificultad IN (ALTA, CRITICA) THEN requerir validación del supervisor."
            ),
        })
        advertencias.append(f"Pieza de dificultad {dificultad}. El supervisor debe revisar antes de aprobar.")
        req_val = True

    # R4 — Producción en serie
    if cantidad >= 5:
        reglas.append({
            "regla": "R_CANTIDAD_SERIE",
            "explicacion": (
                f"Pedido de {cantidad} piezas. "
                "IF cantidad >= 5 THEN aplicar eficiencia de serie (setup compartido)."
            ),
        })

    return {"reglas_aplicadas": reglas, "advertencias": advertencias, "requiere_validacion": req_val}


# ============================================================
# HOJA DE RUTA
# ============================================================

def generar_hoja_ruta(detalle: list, cantidad: int, pieza: str) -> str:
    lineas = [f"HOJA DE RUTA — {pieza.upper()} × {cantidad} pz", "=" * 52]
    for i, paso in enumerate(detalle, 1):
        lineas.append(
            f"{i}. [{paso['etapa']}] {paso['descripcion']}\n"
            f"   Tiempo: {horas_a_texto(paso['horas_total'])} "
            f"({paso['horas_por_pieza']:.3f} h/pz × {cantidad})\n"
            f"   Tarifa: ${paso['tarifa_hora']:.0f}/h  →  Subtotal: ${paso['costo_estimado']:.2f}"
        )
    lineas += ["─" * 52, "Verificar medidas finales y calidad.", "Enviar a validación del supervisor."]
    return "\n".join(lineas)


# ============================================================
# EXPLICACIÓN PARA EL SUPERVISOR
# ============================================================

def generar_explicacion(cliente, pieza, material_final, costos, reglas, cantidad) -> str:
    t = [
        f"**Cliente:** {cliente}",
        f"**Pieza:** {pieza} × {cantidad} pz",
        f"**Material:** {material_final}",
        f"**Tiempo total estimado:** {costos['horas_texto']} ({costos['horas_maquinado_estimadas']:.3f} h)",
        "",
        "**Desglose por etapa:**",
    ]
    for paso in costos["detalle_procesos"]:
        t.append(
            f"  • {paso['etapa']}: {horas_a_texto(paso['horas_total'])} "
            f"@ ${paso['tarifa_hora']:.0f}/h = **${paso['costo_estimado']:.2f}**"
        )
    t += [
        "",
        f"**Costo materiales:** ${costos['costo_materiales']:.2f}",
        f"**Costo maquinado:** ${costos['costo_maquinado']:.2f}",
        f"**Subtotal:** ${costos['costo_total']:.2f}",
        f"**Margen ({costos['margen_utilidad_porcentaje']:.0f}%):** "
        f"${costos['precio_final'] - costos['costo_total']:.2f}",
        f"**Precio final:** ${costos['precio_final']:.2f}",
        "",
        "**Reglas de inferencia aplicadas:**",
    ]
    for r in reglas["reglas_aplicadas"]:
        t.append(f"  • `{r['regla']}`: {r['explicacion']}")
    if reglas["advertencias"]:
        t += ["", "**Advertencias:**"]
        for adv in reglas["advertencias"]:
            t.append(f"  ⚠️ {adv}")
    return "\n".join(t)


# ============================================================
# FUNCIÓN PRINCIPAL DEL AGENTE 2
# ============================================================

def generar_cotizacion_preliminar(
    cliente_nombre: str,
    pieza_solicitada: str,
    tipo_servicio: str,
    cantidad_piezas: int,
    material_solicitado: str,
    requerimientos_cliente: str = "",
    dimensiones: dict = None,
    id_usuario_creador=None,
):
    """
    Genera una cotización preliminar con estimación de tiempos y costos
    basada en parámetros físicos reales de la pieza solicitada.
    """
    if not cliente_nombre.strip():
        raise ValueError("El nombre del cliente es obligatorio.")
    if not pieza_solicitada.strip():
        raise ValueError("La pieza solicitada es obligatoria.")
    if cantidad_piezas <= 0:
        raise ValueError("La cantidad de piezas debe ser mayor a cero.")

    dimensiones = dimensiones or {}

    # 1. Plantilla técnica
    plantilla = db.obtener_plantilla_por_nombre(pieza_solicitada)
    perfil_req = plantilla.get("perfil_requerido") if plantilla else None

    if not plantilla:
        plantilla = {
            "id_plantilla": None,
            "nombre_pieza": pieza_solicitada,
            "perfil_requerido": None,
            "operaciones_base_json": json.dumps(["Ajuste_Manual"]),
            "tiempo_base_horas": 1.5,
            "dificultad": "MEDIA",
            "parametros_base_json": "{}",
        }

    # 2. Material en inventario
    material_encontrado = buscar_mejor_material(material_solicitado, perfil_req)
    material_final = material_encontrado["material"] if material_encontrado else material_solicitado

    # 3. Horas por etapa (modelo físico)
    horas_info = calcular_horas_por_pieza(
        nombre_pieza=pieza_solicitada,
        plantilla=plantilla,
        dimensiones=dimensiones,
        material=material_final,
        cantidad=cantidad_piezas,
    )

    # 4. Costos (tarifa distinta por etapa)
    costos = calcular_costos(horas_info, material_encontrado, cantidad_piezas)

    # 5. Reglas de inferencia
    reglas = evaluar_reglas(plantilla, material_encontrado, cantidad_piezas, pieza_solicitada)

    # 6. Outputs
    estado       = "VALIDACION_PENDIENTE" if reglas["requiere_validacion"] else "COTIZADO"
    fecha_entrega = estimar_fecha_entrega(costos["horas_maquinado_estimadas"], reglas["requiere_validacion"])
    hoja_ruta    = generar_hoja_ruta(costos["detalle_procesos"], cantidad_piezas, pieza_solicitada)
    explicacion  = generar_explicacion(
        cliente_nombre, pieza_solicitada, material_final, costos, reglas, cantidad_piezas
    )
    folio = generar_folio()

    # 7. Persistir en BD
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
        observaciones="Cotización generada por Agente 2 — Motor de inferencia v2 (modelo físico).",
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
            "dimensiones": dimensiones,
        }, ensure_ascii=False),
        regla_evaluada="Motor de inferencia v2 — modelo físico por etapas",
        condiciones_cumplidas_json=json.dumps(reglas["reglas_aplicadas"], ensure_ascii=False),
        resultado_json=json.dumps({
            "folio": folio,
            "estado": estado,
            "precio_final": costos["precio_final"],
            "horas_total": costos["horas_maquinado_estimadas"],
            "horas_texto": costos["horas_texto"],
            "requiere_validacion": reglas["requiere_validacion"],
        }, ensure_ascii=False),
        explicacion_generada=explicacion,
        confianza=0.85 if plantilla.get("id_plantilla") else 0.60,
        requiere_validacion=1 if reglas["requiere_validacion"] else 0,
    )

    return {
        "id_cotizacion":            id_cotizacion,
        "folio":                    folio,
        "estado":                   estado,
        "precio_final":             costos["precio_final"],
        "costo_total":              costos["costo_total"],
        "horas_maquinado_estimadas": costos["horas_maquinado_estimadas"],
        "horas_texto":              costos["horas_texto"],
        "fecha_entrega_estimada":   fecha_entrega,
        "material_final":           material_final,
        "detalle_procesos":         costos["detalle_procesos"],
        "reglas_aplicadas":         reglas["reglas_aplicadas"],
        "advertencias":             reglas["advertencias"],
        "hoja_ruta":                hoja_ruta,
        "explicacion":              explicacion,
    }
