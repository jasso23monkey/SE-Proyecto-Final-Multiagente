import os
import sqlite3
from datetime import datetime
from typing import Any, Iterable

DB_PATH = os.getenv("FORGEFLOW_DB_PATH", "database/forgeflow.db")


class DatabaseError(Exception):
    """Error controlado para mostrar mensajes claros en Streamlit."""


def obtener_conexion() -> sqlite3.Connection:
    """Crea una conexión a SQLite y regresa filas tipo diccionario."""
    if not os.path.exists(DB_PATH):
        raise DatabaseError(
            f"No se encontró la base de datos en '{DB_PATH}'. Ejecuta primero: py seed.py"
        )

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def filas_a_diccionarios(filas: Iterable[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(fila) for fila in filas]


def ejecutar_select(sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    try:
        with obtener_conexion() as conn:
            cur = conn.execute(sql, params)
            return filas_a_diccionarios(cur.fetchall())
    except sqlite3.Error as exc:
        raise DatabaseError(f"Error al consultar la base de datos: {exc}") from exc


def ejecutar_accion(sql: str, params: tuple = ()) -> int:
    """Ejecuta INSERT/UPDATE/DELETE y regresa el último id insertado si aplica."""
    try:
        with obtener_conexion() as conn:
            cur = conn.execute(sql, params)
            conn.commit()
            return int(cur.lastrowid)
    except sqlite3.Error as exc:
        raise DatabaseError(f"Error al guardar cambios en la base de datos: {exc}") from exc


def existe_bd() -> bool:
    return os.path.exists(DB_PATH)


def fecha_actual() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ============================================================
# RESUMEN GENERAL
# ============================================================

def contar_tabla(nombre_tabla: str) -> int:
    filas = ejecutar_select(f"SELECT COUNT(*) AS total FROM {nombre_tabla};")
    return int(filas[0]["total"]) if filas else 0


def obtener_resumen_sistema() -> dict[str, int]:
    tablas = [
        "Inventario_Taller",
        "Inventario_Herramientas",
        "Maquinas_Taller",
        "Proveedores_Taller",
        "Cotizaciones_Ordenes",
        "Ordenes_Compra",
        "Reglas_Inferencia",
    ]
    return {tabla: contar_tabla(tabla) for tabla in tablas}


def obtener_alertas_inventario() -> dict[str, list[dict[str, Any]]]:
    materiales = ejecutar_select(
        """
        SELECT id_material, codigo_material, material, perfil, cantidad_disponible,
               unidad_inventario, stock_minimo, estado
        FROM Inventario_Taller
        WHERE cantidad_disponible <= stock_minimo OR estado IN ('BAJO_STOCK', 'AGOTADO')
        ORDER BY estado, cantidad_disponible ASC;
        """
    )

    herramientas = ejecutar_select(
        """
        SELECT id_herramienta, codigo_herramienta, nombre_herramienta, tipo,
               stock_unidades, stock_minimo, estado
        FROM Inventario_Herramientas
        WHERE stock_unidades <= stock_minimo OR estado IN ('BAJO_STOCK', 'AGOTADO', 'DAÑADA', 'REQUERIR_AFILADO')
        ORDER BY estado, stock_unidades ASC;
        """
    )

    return {"materiales": materiales, "herramientas": herramientas}


# ============================================================
# INVENTARIO DE MATERIALES
# ============================================================

def obtener_materiales() -> list[dict[str, Any]]:
    return ejecutar_select(
        """
        SELECT id_material, codigo_material, material, perfil, dimension_principal,
               unidad_dimension, cantidad_disponible, unidad_inventario,
               costo_unitario, stock_minimo, ubicacion, estado, fecha_actualizacion,
               observaciones
        FROM Inventario_Taller
        ORDER BY material, perfil, dimension_principal;
        """
    )


def agregar_material(
    codigo_material: str | None,
    material: str,
    perfil: str,
    dimension_principal: float,
    unidad_dimension: str,
    cantidad_disponible: float,
    unidad_inventario: str,
    costo_unitario: float,
    stock_minimo: float,
    ubicacion: str | None,
    estado: str,
    observaciones: str | None,
) -> int:
    return ejecutar_accion(
        """
        INSERT INTO Inventario_Taller
        (codigo_material, material, perfil, dimension_principal, unidad_dimension,
         cantidad_disponible, unidad_inventario, costo_unitario, stock_minimo,
         ubicacion, estado, fecha_actualizacion, observaciones)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?);
        """,
        (
            codigo_material or None,
            material.strip(),
            perfil.strip(),
            dimension_principal,
            unidad_dimension,
            cantidad_disponible,
            unidad_inventario,
            costo_unitario,
            stock_minimo,
            ubicacion or None,
            estado,
            observaciones or None,
        ),
    )


def calcular_estado_material(cantidad: float, stock_minimo: float) -> str:
    if cantidad <= 0:
        return "AGOTADO"
    if cantidad <= stock_minimo:
        return "BAJO_STOCK"
    return "DISPONIBLE"


def actualizar_stock_material(
    id_material: int,
    cantidad_disponible: float,
    estado: str | None = None,
    observaciones: str | None = None,
) -> None:
    material = ejecutar_select(
        "SELECT stock_minimo FROM Inventario_Taller WHERE id_material = ?;",
        (id_material,),
    )
    if not material:
        raise DatabaseError("No se encontró el material seleccionado.")

    estado_final = estado or calcular_estado_material(cantidad_disponible, float(material[0]["stock_minimo"]))

    ejecutar_accion(
        """
        UPDATE Inventario_Taller
        SET cantidad_disponible = ?,
            estado = ?,
            observaciones = COALESCE(?, observaciones),
            fecha_actualizacion = CURRENT_TIMESTAMP
        WHERE id_material = ?;
        """,
        (cantidad_disponible, estado_final, observaciones or None, id_material),
    )

def obtener_clientes_actuales():
    return ejecutar_select(
        """
        SELECT
            cliente_nombre,
            MAX(cliente_contacto) AS cliente_contacto,
            MAX(cliente_correo) AS cliente_correo,
            MAX(cliente_telefono) AS cliente_telefono,
            COUNT(*) AS total_cotizaciones,
            MAX(fecha_creacion) AS ultima_cotizacion
        FROM Cotizaciones_Ordenes
        WHERE cliente_nombre IS NOT NULL
        AND TRIM(cliente_nombre) != ''
        GROUP BY LOWER(TRIM(cliente_nombre))
        ORDER BY cliente_nombre;
        """
    )


# ============================================================
# INVENTARIO DE HERRAMIENTAS
# ============================================================

def obtener_herramientas() -> list[dict[str, Any]]:
    return ejecutar_select(
        """
        SELECT id_herramienta, codigo_herramienta, nombre_herramienta, tipo, medida,
               material_herramienta, stock_unidades, stock_minimo, costo_unitario,
               ubicacion, estado, fecha_actualizacion, observaciones
        FROM Inventario_Herramientas
        ORDER BY tipo, nombre_herramienta, medida;
        """
    )


def agregar_herramienta(
    codigo_herramienta: str | None,
    nombre_herramienta: str,
    tipo: str,
    medida: str | None,
    material_herramienta: str | None,
    stock_unidades: int,
    stock_minimo: int,
    costo_unitario: float,
    ubicacion: str | None,
    estado: str,
    observaciones: str | None,
) -> int:
    return ejecutar_accion(
        """
        INSERT INTO Inventario_Herramientas
        (codigo_herramienta, nombre_herramienta, tipo, medida, material_herramienta,
         stock_unidades, stock_minimo, costo_unitario, ubicacion, estado,
         fecha_actualizacion, observaciones)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?);
        """,
        (
            codigo_herramienta or None,
            nombre_herramienta.strip(),
            tipo.strip(),
            medida or None,
            material_herramienta or None,
            stock_unidades,
            stock_minimo,
            costo_unitario,
            ubicacion or None,
            estado,
            observaciones or None,
        ),
    )


def calcular_estado_herramienta(stock: int, stock_minimo: int) -> str:
    if stock <= 0:
        return "AGOTADO"
    if stock <= stock_minimo:
        return "BAJO_STOCK"
    return "DISPONIBLE"


def actualizar_stock_herramienta(
    id_herramienta: int,
    stock_unidades: int,
    estado: str | None = None,
    observaciones: str | None = None,
) -> None:
    herramienta = ejecutar_select(
        "SELECT stock_minimo FROM Inventario_Herramientas WHERE id_herramienta = ?;",
        (id_herramienta,),
    )
    if not herramienta:
        raise DatabaseError("No se encontró la herramienta seleccionada.")

    estado_final = estado or calcular_estado_herramienta(stock_unidades, int(herramienta[0]["stock_minimo"]))

    ejecutar_accion(
        """
        UPDATE Inventario_Herramientas
        SET stock_unidades = ?,
            estado = ?,
            observaciones = COALESCE(?, observaciones),
            fecha_actualizacion = CURRENT_TIMESTAMP
        WHERE id_herramienta = ?;
        """,
        (stock_unidades, estado_final, observaciones or None, id_herramienta),
    )


# ============================================================
# MAQUINAS
# ============================================================

def obtener_maquinas() -> list[dict[str, Any]]:
    return ejecutar_select(
        """
        SELECT id_maquina, codigo_maquina, nombre_maquina, tipo_maquina, marca,
               modelo, capacidad_trabajo, precision_estimada, costo_hora_maquina,
               estado, ubicacion, fecha_ultimo_mantenimiento,
               fecha_proximo_mantenimiento, observaciones
        FROM Maquinas_Taller
        ORDER BY tipo_maquina, nombre_maquina;
        """
    )


def actualizar_estado_maquina(id_maquina: int, estado: str, observaciones: str | None = None) -> None:
    ejecutar_accion(
        """
        UPDATE Maquinas_Taller
        SET estado = ?,
            observaciones = COALESCE(?, observaciones)
        WHERE id_maquina = ?;
        """,
        (estado, observaciones or None, id_maquina),
    )


# ============================================================
# PROVEEDORES
# ============================================================

def obtener_proveedores() -> list[dict[str, Any]]:
    return ejecutar_select(
        """
        SELECT id_proveedor, nombre_proveedor, tipo_proveedor, contacto_nombre,
               contacto_correo, contacto_telefono, direccion, especialidad,
               tiempo_entrega_estimado_dias, condiciones_pago, calificacion,
               estado, observaciones
        FROM Proveedores_Taller
        ORDER BY tipo_proveedor, nombre_proveedor;
        """
    )


def agregar_proveedor(
    nombre_proveedor: str,
    tipo_proveedor: str,
    contacto_nombre: str | None,
    contacto_correo: str | None,
    contacto_telefono: str | None,
    direccion: str | None,
    especialidad: str | None,
    tiempo_entrega_estimado_dias: int,
    condiciones_pago: str | None,
    calificacion: int,
    estado: str,
    observaciones: str | None,
) -> int:
    return ejecutar_accion(
        """
        INSERT INTO Proveedores_Taller
        (nombre_proveedor, tipo_proveedor, contacto_nombre, contacto_correo,
         contacto_telefono, direccion, especialidad, tiempo_entrega_estimado_dias,
         condiciones_pago, calificacion, estado, observaciones)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """,
        (
            nombre_proveedor.strip(),
            tipo_proveedor,
            contacto_nombre or None,
            contacto_correo or None,
            contacto_telefono or None,
            direccion or None,
            especialidad or None,
            tiempo_entrega_estimado_dias,
            condiciones_pago or None,
            calificacion,
            estado,
            observaciones or None,
        ),
    )


# ============================================================
# COTIZACIONES Y PRODUCCION
# ============================================================

def obtener_cotizaciones_pendientes() -> list[dict[str, Any]]:
    return ejecutar_select(
        """
        SELECT id_cotizacion, folio, fecha_creacion, cliente_nombre, pieza_solicitada,
               tipo_servicio, cantidad_piezas, costo_total, precio_final,
               fecha_entrega_estimada, estado_orden, observaciones
        FROM Cotizaciones_Ordenes
        WHERE estado_orden IN ('BORRADOR', 'COTIZADO', 'VALIDACION_PENDIENTE')
        ORDER BY fecha_creacion DESC;
        """
    )


def obtener_ordenes_produccion() -> list[dict[str, Any]]:
    return ejecutar_select(
        """
        SELECT id_cotizacion, folio, fecha_creacion, cliente_nombre, pieza_solicitada,
               tipo_servicio, cantidad_piezas, precio_final, horas_maquinado_estimadas,
               fecha_entrega_estimada, estado_orden, hoja_ruta_instrucciones
        FROM Cotizaciones_Ordenes
        WHERE estado_orden IN ('APROBADO', 'EN_PRODUCCION')
        ORDER BY fecha_entrega_estimada ASC, fecha_creacion DESC;
        """
    )

# ============================================================
# AGENTE 2 - MOTOR DE INFERENCIA
# ============================================================

def obtener_plantillas() -> list[dict[str, Any]]:
    return ejecutar_select(
        """
        SELECT id_plantilla, nombre_pieza, categoria, descripcion,
               id_material_sugerido, perfil_requerido, operaciones_base_json,
               herramientas_sugeridas_json, maquinas_sugeridas_json,
               parametros_base_json, subpiezas_requeridas_json,
               dificultad, tiempo_base_horas, estado
        FROM Plantillas_Piezas
        WHERE estado = 'ACTIVA'
        ORDER BY nombre_pieza;
        """
    )


def obtener_plantilla_por_nombre(nombre_pieza: str) -> dict[str, Any] | None:
    filas = ejecutar_select(
        """
        SELECT id_plantilla, nombre_pieza, categoria, descripcion,
               id_material_sugerido, perfil_requerido, operaciones_base_json,
               herramientas_sugeridas_json, maquinas_sugeridas_json,
               parametros_base_json, subpiezas_requeridas_json,
               dificultad, tiempo_base_horas, estado
        FROM Plantillas_Piezas
        WHERE LOWER(nombre_pieza) = LOWER(?)
          AND estado = 'ACTIVA'
        LIMIT 1;
        """,
        (nombre_pieza.strip(),)
    )

    return filas[0] if filas else None


def obtener_tarifas_activas() -> list[dict[str, Any]]:
    return ejecutar_select(
        """
        SELECT id_tarifa, concepto_proceso, tipo_tarifa, costo_base,
               unidad_cobro, margen_utilidad_porcentaje, tiempo_minimo_horas,
               descripcion, estado
        FROM Tarifas_Taller
        WHERE estado = 'ACTIVA'
        ORDER BY concepto_proceso;
        """
    )


def crear_cotizacion(
    folio: str,
    id_usuario_creador: int | None,
    cliente_nombre: str,
    cliente_contacto: str | None,
    cliente_correo: str | None,
    cliente_telefono: str | None,
    id_plantilla: int | None,
    pieza_solicitada: str,
    tipo_servicio: str,
    cantidad_piezas: int,
    dimensiones_json: str,
    requerimientos_cliente: str | None,
    material_final: str | None,
    procesos_finales_json: str,
    costo_materiales: float,
    costo_herramientas: float,
    costo_maquinado: float,
    costo_servicios_externos: float,
    costo_total: float,
    margen_utilidad_porcentaje: float,
    precio_final: float,
    horas_maquinado_estimadas: float,
    fecha_entrega_estimada: str | None,
    hoja_ruta_instrucciones: str | None,
    explicacion_inferencia: str | None,
    estado_orden: str,
    observaciones: str | None
) -> int:
    return ejecutar_accion(
        """
        INSERT INTO Cotizaciones_Ordenes
        (folio, id_usuario_creador, cliente_nombre, cliente_contacto,
         cliente_correo, cliente_telefono, id_plantilla, pieza_solicitada,
         tipo_servicio, cantidad_piezas, dimensiones_json,
         requerimientos_cliente, material_final, procesos_finales_json,
         costo_materiales, costo_herramientas, costo_maquinado,
         costo_servicios_externos, costo_total, margen_utilidad_porcentaje,
         precio_final, horas_maquinado_estimadas, fecha_entrega_estimada,
         hoja_ruta_instrucciones, explicacion_inferencia, estado_orden,
         observaciones)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """,
        (
            folio,
            id_usuario_creador,
            cliente_nombre,
            cliente_contacto,
            cliente_correo,
            cliente_telefono,
            id_plantilla,
            pieza_solicitada,
            tipo_servicio,
            cantidad_piezas,
            dimensiones_json,
            requerimientos_cliente,
            material_final,
            procesos_finales_json,
            costo_materiales,
            costo_herramientas,
            costo_maquinado,
            costo_servicios_externos,
            costo_total,
            margen_utilidad_porcentaje,
            precio_final,
            horas_maquinado_estimadas,
            fecha_entrega_estimada,
            hoja_ruta_instrucciones,
            explicacion_inferencia,
            estado_orden,
            observaciones
        )
    )

def actualizar_estado_cotizacion(id_cotizacion, nuevo_estado, observaciones=""):
    return ejecutar_accion(
        """
        UPDATE Cotizaciones_Ordenes
        SET estado_orden = ?,
            observaciones = COALESCE(observaciones, '') || ?
        WHERE id_cotizacion = ?;
        """,
        (
            nuevo_estado,
            "\n[Agente 3] " + observaciones if observaciones else "",
            id_cotizacion
        )
    )

def registrar_historial_inferencia(
    id_cotizacion: int | None,
    agente_origen: str,
    entrada_json: str,
    regla_evaluada: str | None,
    condiciones_cumplidas_json: str | None,
    resultado_json: str,
    explicacion_generada: str,
    confianza: float,
    requiere_validacion: int
) -> int:
    return ejecutar_accion(
        """
        INSERT INTO Historial_Inferencias
        (id_cotizacion, agente_origen, entrada_json, regla_evaluada,
         condiciones_cumplidas_json, resultado_json, explicacion_generada,
         confianza, requiere_validacion, validado)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0);
        """,
        (
            id_cotizacion,
            agente_origen,
            entrada_json,
            regla_evaluada,
            condiciones_cumplidas_json,
            resultado_json,
            explicacion_generada,
            confianza,
            requiere_validacion
        )
    )

def obtener_cotizacion_por_id(id_cotizacion):
    filas = ejecutar_select(
        """
        SELECT *
        FROM Cotizaciones_Ordenes
        WHERE id_cotizacion = ?
        LIMIT 1;
        """,
        (id_cotizacion,)
    )
    return filas[0] if filas else None


def obtener_cotizaciones_para_supervisor():
    return ejecutar_select(
        """
        SELECT id_cotizacion, folio, cliente_nombre, pieza_solicitada,
               material_final, cantidad_piezas, costo_total, precio_final,
               horas_maquinado_estimadas, fecha_entrega_estimada, estado_orden
        FROM Cotizaciones_Ordenes
        WHERE estado_orden IN ('COTIZADO', 'VALIDACION_PENDIENTE', 'PENDIENTE_APROBACION', 'APROBADO')
        ORDER BY id_cotizacion DESC;
        """
    )



