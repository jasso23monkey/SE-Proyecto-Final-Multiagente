import json
import os
import sqlite3
from datetime import datetime, timedelta

# Ruta donde se creara la base de datos SQLite.
DB_PATH = "database/forgeflow.db"
SCHEMA_PATH = "database/schema.sql"


def to_json(data):
    """Convierte listas/diccionarios a JSON legible para guardarlo en SQLite."""
    return json.dumps(data, ensure_ascii=False)


def now_text():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def date_plus_days(days):
    return (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")


def get_id(cursor, table, id_column, where_column, value):
    """Obtiene un ID a partir de una columna unica o identificadora."""
    cursor.execute(
        f"SELECT {id_column} FROM {table} WHERE {where_column} = ? LIMIT 1;",
        (value,),
    )
    row = cursor.fetchone()
    return row[0] if row else None


def exists(cursor, table, where_sql, params):
    cursor.execute(f"SELECT 1 FROM {table} WHERE {where_sql} LIMIT 1;", params)
    return cursor.fetchone() is not None


def init_db():
    # 1. Asegurar que exista la carpeta database/
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    if not os.path.exists(SCHEMA_PATH):
        raise FileNotFoundError(
            f"No se encontro {SCHEMA_PATH}. Coloca tu schema.sql dentro de la carpeta database/."
        )

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 2. Activar llaves foraneas en SQLite
    cursor.execute("PRAGMA foreign_keys = ON;")

    # 3. Crear estructura desde schema.sql
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = f.read()
    cursor.executescript(schema)

    print("✓ Estructura de ForgeFlow ERP creada correctamente.")

    # ============================================================
    # 1) USUARIOS INTERNOS
    # ============================================================
    usuarios = [
        (
            "Administrador ForgeFlow",
            "admin@forgeflow.local",
            "admin",
            "hash_demo_admin_no_usar_en_produccion",
            "ADMIN",
            "ACTIVO",
        ),
        (
            "Supervisor de Taller",
            "supervisor@forgeflow.local",
            "supervisor",
            "hash_demo_supervisor_no_usar_en_produccion",
            "SUPERVISOR",
            "ACTIVO",
        ),
        (
            "Operador de Maquinado",
            "operador@forgeflow.local",
            "operador",
            "hash_demo_operador_no_usar_en_produccion",
            "OPERADOR",
            "ACTIVO",
        ),
        (
            "Ventas y Atención al Cliente",
            "ventas@forgeflow.local",
            "ventas",
            "hash_demo_ventas_no_usar_en_produccion",
            "VENTAS",
            "ACTIVO",
        ),
        (
            "Encargado de Almacén",
            "almacen@forgeflow.local",
            "almacen",
            "hash_demo_almacen_no_usar_en_produccion",
            "ALMACEN",
            "ACTIVO",
        ),
    ]

    cursor.executemany(
        """
        INSERT OR IGNORE INTO Usuarios_Internos
        (nombre_completo, correo, usuario, password_hash, rol, estado)
        VALUES (?, ?, ?, ?, ?, ?);
        """,
        usuarios,
    )

    # ============================================================
    # 2) INVENTARIO DE MATERIALES
    # ============================================================
    materiales = [
        (
            "MAT-AC1018-BR-2",
            "Acero 1018",
            "Barra Redonda",
            2.0,
            "pulgadas",
            12.0,
            "metros",
            450.00,
            3.0,
            "Rack A-01",
            "DISPONIBLE",
            "Material base para engranes y piezas generales.",
        ),
        (
            "MAT-AC1045-BR-3",
            "Acero 1045",
            "Barra Redonda",
            3.0,
            "pulgadas",
            6.0,
            "metros",
            680.00,
            2.0,
            "Rack A-02",
            "DISPONIBLE",
            "Recomendado para ejes, yunques y piezas de mayor esfuerzo.",
        ),
        (
            "MAT-AL6061-BR-4",
            "Aluminio 6061",
            "Barra Redonda",
            4.0,
            "pulgadas",
            18.0,
            "metros",
            950.00,
            4.0,
            "Rack B-01",
            "DISPONIBLE",
            "Material ligero para rodillos y piezas de baja carga.",
        ),
        (
            "MAT-BR-BR-5",
            "Bronce",
            "Barra Redonda",
            5.0,
            "pulgadas",
            2.5,
            "metros",
            2400.00,
            2.0,
            "Rack C-01",
            "DISPONIBLE",
            "Material para bujes y piezas antifricción.",
        ),
        (
            "MAT-CO-BR-1",
            "Cobre",
            "Barra Redonda",
            1.0,
            "pulgadas",
            4.0,
            "metros",
            1800.00,
            1.5,
            "Rack C-02",
            "DISPONIBLE",
            "Material conductor para piezas especiales.",
        ),
        (
            "MAT-AC4140-BR-2",
            "Acero 4140",
            "Barra Redonda",
            2.0,
            "pulgadas",
            1.0,
            "metros",
            1250.00,
            2.0,
            "Rack A-03",
            "BAJO_STOCK",
            "Acero aleado para piezas críticas; stock bajo para probar reglas.",
        ),
        (
            "MAT-PL1018-PL-6",
            "Acero 1018",
            "Placa",
            6.0,
            "mm",
            8.0,
            "placas",
            520.00,
            2.0,
            "Rack P-01",
            "DISPONIBLE",
            "Placa para soportes, bases y tapas.",
        ),
    ]

    cursor.executemany(
        """
        INSERT OR IGNORE INTO Inventario_Taller
        (codigo_material, material, perfil, dimension_principal, unidad_dimension,
         cantidad_disponible, unidad_inventario, costo_unitario, stock_minimo,
         ubicacion, estado, observaciones)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """,
        materiales,
    )

    # ============================================================
    # 3) INVENTARIO DE HERRAMIENTAS
    # ============================================================
    herramientas = [
        (
            "HER-BRO-CEN-01",
            "Broca de Centro",
            "Broca",
            "No. 2",
            "HSS",
            5,
            2,
            85.00,
            "Cajón H-01",
            "DISPONIBLE",
            "Usada para centrar piezas antes del torneado.",
        ),
        (
            "HER-BUR-CAR-01",
            "Buril de Pastilla Carburo",
            "Buril",
            "1/2 pulgada",
            "Carburo",
            8,
            3,
            180.00,
            "Cajón H-02",
            "DISPONIBLE",
            "Buril general para desbaste y acabado.",
        ),
        (
            "HER-BUR-INT-01",
            "Buril de Interiores",
            "Buril",
            "10 mm",
            "HSS",
            3,
            2,
            150.00,
            "Cajón H-03",
            "DISPONIBLE",
            "Herramienta para cilindrado interno.",
        ),
        (
            "HER-COR-FRE-01",
            "Cortador de Fresadora Recto",
            "Cortador",
            "3/8 pulgada",
            "HSS",
            4,
            2,
            320.00,
            "Cajón F-01",
            "DISPONIBLE",
            "Cortador para ranuras y planeado sencillo.",
        ),
        (
            "HER-COR-RAN-01",
            "Cortador Especial de Ranuras",
            "Cortador",
            "Especial",
            "Carburo",
            1,
            2,
            550.00,
            "Cajón F-02",
            "BAJO_STOCK",
            "Stock bajo para validar reglas de compra.",
        ),
        (
            "HER-MAC-OPR-01",
            "Machuelo para Opresor",
            "Machuelo",
            "1/4-20 UNC",
            "HSS",
            4,
            2,
            95.00,
            "Cajón R-01",
            "DISPONIBLE",
            "Usado para roscas de opresor.",
        ),
        (
            "HER-INS-CAR-01",
            "Insertos de Carburo CNMG",
            "Inserto",
            "CNMG 120408",
            "Carburo",
            10,
            5,
            65.00,
            "Cajón I-01",
            "DISPONIBLE",
            "Insertos de repuesto para torno.",
        ),
    ]

    cursor.executemany(
        """
        INSERT OR IGNORE INTO Inventario_Herramientas
        (codigo_herramienta, nombre_herramienta, tipo, medida, material_herramienta,
         stock_unidades, stock_minimo, costo_unitario, ubicacion, estado, observaciones)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """,
        herramientas,
    )

    # ============================================================
    # 4) MÁQUINAS DEL TALLER
    # ============================================================
    maquinas = [
        (
            "MAQ-TOR-001",
            "Torno Paralelo 1",
            "TORNO",
            "TOS",
            "SN40",
            "Diámetro máximo 300 mm, largo entre puntos 1000 mm",
            "+/- 0.05 mm",
            350.00,
            "DISPONIBLE",
            "Área de torno",
            "2026-05-10",
            "2026-08-10",
            "Máquina principal para cilindrado, refrentado y barrenado.",
        ),
        (
            "MAQ-FRE-001",
            "Fresadora Universal 1",
            "FRESADORA",
            "Bridgeport",
            "Series I",
            "Mesa 9 x 42 pulgadas, cabezal vertical",
            "+/- 0.08 mm",
            400.00,
            "DISPONIBLE",
            "Área de fresado",
            "2026-05-15",
            "2026-08-15",
            "Usada para ranuras, planeado y engranes rectos.",
        ),
        (
            "MAQ-TAL-001",
            "Taladro de Banco",
            "TALADRO",
            "Truper Industrial",
            "TB-20",
            "Brocas hasta 20 mm",
            "+/- 0.2 mm",
            180.00,
            "DISPONIBLE",
            "Área de barrenado",
            "2026-05-20",
            "2026-08-20",
            "Apoyo para barrenado secundario y preparación de roscas.",
        ),
        (
            "MAQ-REC-001",
            "Rectificadora Plana",
            "RECTIFICADORA",
            "Okamoto",
            "PSG",
            "Superficie máxima 400 x 200 mm",
            "+/- 0.01 mm",
            500.00,
            "MANTENIMIENTO",
            "Área de rectificado",
            "2026-06-01",
            "2026-06-15",
            "En mantenimiento para probar regla de máquina no disponible.",
        ),
    ]

    cursor.executemany(
        """
        INSERT OR IGNORE INTO Maquinas_Taller
        (codigo_maquina, nombre_maquina, tipo_maquina, marca, modelo,
         capacidad_trabajo, precision_estimada, costo_hora_maquina, estado,
         ubicacion, fecha_ultimo_mantenimiento, fecha_proximo_mantenimiento, observaciones)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """,
        maquinas,
    )

    # ============================================================
    # 5) TARIFAS DEL TALLER
    # ============================================================
    tarifas = [
        (
            "Hora_Torno",
            "MAQUINA",
            350.00,
            "hora",
            20.00,
            0.50,
            "Maquinado general en torno convencional.",
            "ACTIVA",
        ),
        (
            "Hora_Fresadora",
            "MAQUINA",
            400.00,
            "hora",
            20.00,
            0.50,
            "Corte general, ranurado, planeado y fresado convencional.",
            "ACTIVA",
        ),
        (
            "Hora_Taladro",
            "MAQUINA",
            180.00,
            "hora",
            15.00,
            0.25,
            "Barrenado y preparación de roscas.",
            "ACTIVA",
        ),
        (
            "Acomodo_Especial_Helicoidal",
            "AJUSTE",
            600.00,
            "servicio",
            25.00,
            0.00,
            "Ajuste de tren de engranes y ángulo para engranes helicoidales.",
            "ACTIVA",
        ),
        (
            "Hechura_Machuelo",
            "PROCESO",
            80.00,
            "pieza",
            20.00,
            0.10,
            "Proceso de roscado con machuelo para opresor.",
            "ACTIVA",
        ),
        (
            "Ranurado_Interno_Bronce",
            "PROCESO",
            250.00,
            "pieza",
            25.00,
            0.30,
            "Recargo por ranuras internas en buje de bronce.",
            "ACTIVA",
        ),
        (
            "Cortador_Especial_Externo",
            "AJUSTE",
            180.00,
            "pieza",
            20.00,
            0.20,
            "Uso de cortador especial para ranura externa en fresadora.",
            "ACTIVA",
        ),
        (
            "Caja_Balero",
            "PROCESO",
            150.00,
            "pieza",
            20.00,
            0.25,
            "Ajuste milimétrico para alojamiento de baleros.",
            "ACTIVA",
        ),
        (
            "Ajuste_Reparacion_General",
            "MANO_OBRA",
            300.00,
            "hora",
            15.00,
            0.50,
            "Mano de obra base para rectificados o modificaciones.",
            "ACTIVA",
        ),
        (
            "Tratamiento_Termico_Externo",
            "SERVICIO_EXTERNO",
            1200.00,
            "servicio",
            25.00,
            0.00,
            "Servicio externo estimado para temple o revenido.",
            "ACTIVA",
        ),
    ]

    cursor.executemany(
        """
        INSERT OR IGNORE INTO Tarifas_Taller
        (concepto_proceso, tipo_tarifa, costo_base, unidad_cobro,
         margen_utilidad_porcentaje, tiempo_minimo_horas, descripcion, estado)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """,
        tarifas,
    )

    # ============================================================
    # 6) PROVEEDORES
    #    La tabla no tiene UNIQUE, por eso evitamos duplicados manualmente.
    # ============================================================
    proveedores = [
        (
            "Aceros Monterrey S.A.",
            "MATERIALES",
            "Ventas Industriales",
            "ventas@acerosmty.com",
            "81 0000 0001",
            "Monterrey, N.L.",
            "Aceros al carbón y aleados",
            4,
            "Crédito 15 días",
            5,
            "Proveedor principal de acero 1018, 1045 y 4140.",
        ),
        (
            "Metales y Bronces del Centro",
            "MATERIALES",
            "Atención a talleres",
            "contacto@broncescentro.com",
            "33 0000 0002",
            "Guadalajara, Jal.",
            "Bronce, cobre y metales no ferrosos",
            5,
            "Contado o transferencia",
            4,
            "Útil para bujes, cobre y piezas antifricción.",
        ),
        (
            "Herramientas Industriales GDL",
            "HERRAMIENTAS",
            "Mostrador Industrial",
            "contacto@herramientasgdl.com",
            "33 0000 0003",
            "Guadalajara, Jal.",
            "Herramientas, brocas, machuelos y cortadores",
            2,
            "Contado",
            5,
            "Proveedor rápido para reposición de herramientas.",
        ),
        (
            "Temple y Rectificado Especializado",
            "SERVICIO_EXTERNO",
            "Coordinación de producción",
            "servicios@templeespecializado.com",
            "33 0000 0004",
            "Zapopan, Jal.",
            "Tratamiento térmico y rectificado",
            7,
            "Anticipo 50%",
            4,
            "Proveedor externo para procesos que no se realizan internamente.",
        ),
    ]

    for proveedor in proveedores:
        nombre = proveedor[0]
        if not exists(cursor, "Proveedores_Taller", "nombre_proveedor = ?", (nombre,)):
            cursor.execute(
                """
                INSERT INTO Proveedores_Taller
                (nombre_proveedor, tipo_proveedor, contacto_nombre, contacto_correo,
                 contacto_telefono, direccion, especialidad, tiempo_entrega_estimado_dias,
                 condiciones_pago, calificacion, observaciones)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                proveedor,
            )

    # ============================================================
    # 7) PLANTILLAS DE PIEZAS
    # ============================================================
    id_acero_1018 = get_id(cursor, "Inventario_Taller", "id_material", "codigo_material", "MAT-AC1018-BR-2")
    id_acero_1045 = get_id(cursor, "Inventario_Taller", "id_material", "codigo_material", "MAT-AC1045-BR-3")
    id_aluminio = get_id(cursor, "Inventario_Taller", "id_material", "codigo_material", "MAT-AL6061-BR-4")
    id_bronce = get_id(cursor, "Inventario_Taller", "id_material", "codigo_material", "MAT-BR-BR-5")
    id_cobre = get_id(cursor, "Inventario_Taller", "id_material", "codigo_material", "MAT-CO-BR-1")

    plantillas = [
        (
            "engrane_recto",
            "Transmisión",
            "Engrane recto básico para transmisión mecánica.",
            id_acero_1018,
            "Barra Redonda",
            to_json(["Hora_Torno", "Hora_Fresadora"]),
            to_json(["Broca de Centro", "Buril de Pastilla Carburo", "Cortador de Fresadora Recto"]),
            to_json(["TORNO", "FRESADORA"]),
            to_json({"tolerancia_general_mm": 0.05, "requiere_chavetero": True, "requiere_dientes": True}),
            None,
            "MEDIA",
            3.5,
            "ACTIVA",
        ),
        (
            "engrane_mamelon",
            "Transmisión",
            "Engrane con mamelón y rosca para opresor.",
            id_acero_1018,
            "Barra Redonda",
            to_json(["Hora_Torno", "Hora_Fresadora", "Hechura_Machuelo"]),
            to_json(["Broca de Centro", "Buril de Pastilla Carburo", "Machuelo para Opresor"]),
            to_json(["TORNO", "FRESADORA", "TALADRO"]),
            to_json({"tolerancia_general_mm": 0.05, "requiere_mamelon": True, "requiere_opresor": True}),
            None,
            "ALTA",
            4.5,
            "ACTIVA",
        ),
        (
            "engrane_helicoidal",
            "Transmisión",
            "Engrane helicoidal con acomodo especial de fresadora.",
            id_acero_1045,
            "Barra Redonda",
            to_json(["Hora_Torno", "Hora_Fresadora", "Acomodo_Especial_Helicoidal"]),
            to_json(["Broca de Centro", "Buril de Pastilla Carburo", "Cortador de Fresadora Recto"]),
            to_json(["TORNO", "FRESADORA"]),
            to_json({"angulo_helice_grados": 20, "tolerancia_general_mm": 0.04, "requiere_validacion_supervisor": True}),
            None,
            "CRITICA",
            6.0,
            "ACTIVA",
        ),
        (
            "rodillo_aluminio",
            "Rodillos",
            "Rodillo de aluminio para impresión o transporte ligero.",
            id_aluminio,
            "Barra Redonda",
            to_json(["Hora_Torno", "Caja_Balero"]),
            to_json(["Broca de Centro", "Buril de Pastilla Carburo", "Buril de Interiores"]),
            to_json(["TORNO"]),
            to_json({"requiere_caja_balero": True, "acabado_superficial": "medio"}),
            None,
            "MEDIA",
            3.0,
            "ACTIVA",
        ),
        (
            "rodillo_acero_yunque",
            "Rodillos",
            "Rodillo de acero usado como yunque o apoyo de mayor resistencia.",
            id_acero_1045,
            "Barra Redonda",
            to_json(["Hora_Torno", "Caja_Balero"]),
            to_json(["Broca de Centro", "Buril de Pastilla Carburo", "Buril de Interiores"]),
            to_json(["TORNO"]),
            to_json({"requiere_caja_balero": True, "requiere_alineacion": True}),
            None,
            "ALTA",
            4.0,
            "ACTIVA",
        ),
        (
            "buje_bronce_ranurado",
            "Bujes",
            "Buje de bronce con ranurado interno y externo.",
            id_bronce,
            "Barra Redonda",
            to_json(["Hora_Torno", "Hora_Fresadora", "Ranurado_Interno_Bronce", "Cortador_Especial_Externo"]),
            to_json(["Buril de Interiores", "Cortador Especial de Ranuras"]),
            to_json(["TORNO", "FRESADORA"]),
            to_json({"requiere_ranura_interna": True, "requiere_ranura_externa": True, "tolerancia_general_mm": 0.03}),
            None,
            "ALTA",
            5.0,
            "ACTIVA",
        ),
        (
            "buje_cobre",
            "Bujes",
            "Buje simple de cobre para aplicación especial.",
            id_cobre,
            "Barra Redonda",
            to_json(["Hora_Torno"]),
            to_json(["Broca de Centro", "Buril de Pastilla Carburo"]),
            to_json(["TORNO"]),
            to_json({"tolerancia_general_mm": 0.08, "acabado_superficial": "básico"}),
            None,
            "BAJA",
            2.0,
            "ACTIVA",
        ),
        (
            "rodillo_impresion_completo",
            "Ensambles",
            "Ensamble compuesto por rodillo de aluminio y engrane recto.",
            None,
            None,
            to_json([]),
            to_json([]),
            to_json(["TORNO", "FRESADORA"]),
            to_json({"tipo": "ensamble", "requiere_subpiezas": True}),
            to_json(["rodillo_aluminio", "engrane_recto"]),
            "ALTA",
            7.0,
            "ACTIVA",
        ),
        (
            "yunque_completo",
            "Ensambles",
            "Ensamble compuesto por rodillo de acero tipo yunque y engrane recto.",
            None,
            None,
            to_json([]),
            to_json([]),
            to_json(["TORNO", "FRESADORA"]),
            to_json({"tipo": "ensamble", "requiere_subpiezas": True}),
            to_json(["rodillo_acero_yunque", "engrane_recto"]),
            "ALTA",
            8.0,
            "ACTIVA",
        ),
    ]

    cursor.executemany(
        """
        INSERT OR IGNORE INTO Plantillas_Piezas
        (nombre_pieza, categoria, descripcion, id_material_sugerido, perfil_requerido,
         operaciones_base_json, herramientas_sugeridas_json, maquinas_sugeridas_json,
         parametros_base_json, subpiezas_requeridas_json, dificultad, tiempo_base_horas, estado)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """,
        plantillas,
    )

    # ============================================================
    # 8) REGLAS DE INFERENCIA
    # ============================================================
    reglas = [
        (
            "R_STOCK_MATERIAL_INSUFICIENTE_001",
            "Detectar material insuficiente para fabricar pieza",
            "MOTOR_INFERENCIA",
            "inventario",
            10,
            to_json({"si": ["cantidad_disponible < cantidad_requerida", "estado_material IN ['BAJO_STOCK', 'AGOTADO']"]}),
            to_json({"entonces": ["marcar_validacion_pendiente", "generar_sugerencia_orden_compra", "notificar_almacen"]}),
            "El sistema detectó que el material disponible no cubre la cantidad requerida o está por debajo del stock mínimo.",
            1,
            "ACTIVA",
        ),
        (
            "R_HERRAMIENTA_AGOTADA_001",
            "Detectar herramienta agotada o no disponible",
            "MOTOR_INFERENCIA",
            "herramientas",
            9,
            to_json({"si": ["herramienta_requerida.estado IN ['AGOTADO', 'DAÑADA', 'REQUERIR_AFILADO']", "stock_unidades <= stock_minimo"]}),
            to_json({"entonces": ["buscar_herramienta_alternativa", "solicitar_compra_o_mantenimiento", "pedir_validacion_supervisor"]}),
            "La herramienta necesaria no está disponible en condiciones adecuadas; se requiere alternativa, compra o mantenimiento.",
            1,
            "ACTIVA",
        ),
        (
            "R_MAQUINA_NO_DISPONIBLE_001",
            "Validar disponibilidad de máquina requerida",
            "MOTOR_INFERENCIA",
            "maquinado",
            8,
            to_json({"si": ["maquina_requerida.estado != 'DISPONIBLE'"]}),
            to_json({"entonces": ["reprogramar_fecha_entrega", "solicitar_validacion_supervisor"]}),
            "La máquina requerida no está disponible; la fecha de entrega debe revisarse antes de aprobar la cotización.",
            1,
            "ACTIVA",
        ),
        (
            "R_PIEZA_COMPUESTA_001",
            "Expandir ensamble en subpiezas fabricables",
            "MOTOR_INFERENCIA",
            "plantillas",
            7,
            to_json({"si": ["plantilla.subpiezas_requeridas_json no es NULL"]}),
            to_json({"entonces": ["descomponer_en_subpiezas", "sumar_operaciones_y_materiales", "calcular_tiempo_total"]}),
            "La pieza solicitada es un ensamble; el sistema debe fabricar o cotizar sus subpiezas antes de cerrar la orden.",
            0,
            "ACTIVA",
        ),
        (
            "R_ENGRANE_HELICOIDAL_VALIDACION_001",
            "Solicitar validación para engrane helicoidal",
            "MOTOR_INFERENCIA",
            "maquinado",
            6,
            to_json({"si": ["pieza_solicitada contiene 'helicoidal'", "operaciones incluyen 'Acomodo_Especial_Helicoidal'"]}),
            to_json({"entonces": ["agregar_ajuste_helicoidal", "pedir_validacion_supervisor", "aumentar_tiempo_estimado"]}),
            "El engrane helicoidal requiere acomodo especial y validación técnica antes de aprobar producción.",
            1,
            "ACTIVA",
        ),
        (
            "R_REPARACION_SIN_PLANTILLA_001",
            "Procesar reparación sin plantilla exacta",
            "CHATBOT",
            "atencion_cliente",
            5,
            to_json({"si": ["tipo_servicio IN ['REPARACION', 'MODIFICACION']", "no hay plantilla exacta"]}),
            to_json({"entonces": ["solicitar_fotos_o_medidas", "usar_tarifa_Ajuste_Reparacion_General", "crear_borrador"]}),
            "Cuando el cliente solicita reparación sin una plantilla exacta, el chatbot debe pedir más datos y crear un borrador revisable.",
            1,
            "ACTIVA",
        ),
    ]

    cursor.executemany(
        """
        INSERT OR IGNORE INTO Reglas_Inferencia
        (codigo_regla, nombre_regla, agente_responsable, categoria, prioridad,
         condiciones_json, acciones_json, explicacion_base, requiere_validacion, estado)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """,
        reglas,
    )

    # ============================================================
    # 9) COTIZACIONES / ÓRDENES DE EJEMPLO
    #    Sirven para probar chatbot, motor de inferencia y supervisor.
    # ============================================================
    id_ventas = get_id(cursor, "Usuarios_Internos", "id_usuario", "usuario", "ventas")
    id_supervisor = get_id(cursor, "Usuarios_Internos", "id_usuario", "usuario", "supervisor")
    id_eng_recto = get_id(cursor, "Plantillas_Piezas", "id_plantilla", "nombre_pieza", "engrane_recto")
    id_buje_bronce = get_id(cursor, "Plantillas_Piezas", "id_plantilla", "nombre_pieza", "buje_bronce_ranurado")
    id_rodillo_comp = get_id(cursor, "Plantillas_Piezas", "id_plantilla", "nombre_pieza", "rodillo_impresion_completo")

    cotizaciones = [
        (
            "COT-2026-0001",
            now_text(),
            id_ventas,
            id_supervisor,
            "Empaques Flexo del Bajío",
            "Ing. Ramírez",
            "compras@flexobajio.com",
            "33 1111 2222",
            id_eng_recto,
            "engrane_recto",
            "FABRICACION",
            2,
            to_json({"diametro_exterior_mm": 80, "diametro_eje_mm": 20, "espesor_mm": 18, "dientes": 32}),
            "Cliente requiere engranes de repuesto para transmisión de máquina flexográfica.",
            "Acero 1018",
            to_json(["Hora_Torno", "Hora_Fresadora"]),
            420.00,
            90.00,
            2450.00,
            0.00,
            2960.00,
            25.00,
            3700.00,
            7.0,
            date_plus_days(5),
            "1) Cortar material. 2) Tornear diámetro exterior e interior. 3) Fresar dientes. 4) Verificar medidas.",
            "Se seleccionó acero 1018 por plantilla y procesos base de torno/fresadora.",
            "COTIZADO",
            "Ejemplo de cotización directa sin alerta crítica.",
        ),
        (
            "COT-2026-0002",
            now_text(),
            id_ventas,
            None,
            "Maquinados Industriales Jasso",
            "Taller interno",
            "taller@cliente.local",
            "33 3333 4444",
            id_buje_bronce,
            "buje_bronce_ranurado",
            "FABRICACION",
            4,
            to_json({"diametro_exterior_mm": 95, "diametro_interior_mm": 60, "largo_mm": 70, "ranuras": 2}),
            "Bujes de bronce con ranura interna y externa; validar stock de cortador especial.",
            "Bronce",
            to_json(["Hora_Torno", "Hora_Fresadora", "Ranurado_Interno_Bronce", "Cortador_Especial_Externo"]),
            1600.00,
            550.00,
            5200.00,
            0.00,
            7350.00,
            25.00,
            9187.50,
            20.0,
            date_plus_days(9),
            "1) Revisar stock de bronce. 2) Tornear exterior e interior. 3) Ranurar. 4) Validar herramienta especial.",
            "El sistema marcó validación porque el cortador especial está bajo stock y la pieza requiere ranurado.",
            "VALIDACION_PENDIENTE",
            "Ejemplo para probar el agente supervisor/explicador.",
        ),
        (
            "COT-2026-0003",
            now_text(),
            id_ventas,
            id_supervisor,
            "Soluciones de Impresión Rivera",
            "Mantenimiento Rivera",
            "mantenimiento@rivera.local",
            "33 5555 6666",
            id_rodillo_comp,
            "rodillo_impresion_completo",
            "FABRICACION",
            1,
            to_json({"rodillo_largo_mm": 450, "diametro_rodillo_mm": 90, "engrane_dientes": 28}),
            "Solicitan rodillo completo con engrane para línea de impresión.",
            "Aluminio 6061 + Acero 1018",
            to_json(["Hora_Torno", "Caja_Balero", "Hora_Fresadora"]),
            2100.00,
            180.00,
            4200.00,
            0.00,
            6480.00,
            25.00,
            8100.00,
            10.0,
            date_plus_days(7),
            "1) Fabricar rodillo. 2) Fabricar engrane. 3) Ensamblar. 4) Verificar concentricidad.",
            "La plantilla se descompuso en subpiezas: rodillo_aluminio y engrane_recto.",
            "APROBADO",
            "Ejemplo de pieza compuesta.",
        ),
    ]

    cursor.executemany(
        """
        INSERT OR IGNORE INTO Cotizaciones_Ordenes
        (folio, fecha_creacion, id_usuario_creador, id_usuario_validador,
         cliente_nombre, cliente_contacto, cliente_correo, cliente_telefono,
         id_plantilla, pieza_solicitada, tipo_servicio, cantidad_piezas,
         dimensiones_json, requerimientos_cliente, material_final, procesos_finales_json,
         costo_materiales, costo_herramientas, costo_maquinado, costo_servicios_externos,
         costo_total, margen_utilidad_porcentaje, precio_final, horas_maquinado_estimadas,
         fecha_entrega_estimada, hoja_ruta_instrucciones, explicacion_inferencia,
         estado_orden, observaciones)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """,
        cotizaciones,
    )

    # ============================================================
    # 10) HISTORIAL DE INFERENCIAS
    # ============================================================
    id_cot_1 = get_id(cursor, "Cotizaciones_Ordenes", "id_cotizacion", "folio", "COT-2026-0001")
    id_cot_2 = get_id(cursor, "Cotizaciones_Ordenes", "id_cotizacion", "folio", "COT-2026-0002")
    id_cot_3 = get_id(cursor, "Cotizaciones_Ordenes", "id_cotizacion", "folio", "COT-2026-0003")

    id_regla_stock = get_id(cursor, "Reglas_Inferencia", "id_regla", "codigo_regla", "R_STOCK_MATERIAL_INSUFICIENTE_001")
    id_regla_herr = get_id(cursor, "Reglas_Inferencia", "id_regla", "codigo_regla", "R_HERRAMIENTA_AGOTADA_001")
    id_regla_comp = get_id(cursor, "Reglas_Inferencia", "id_regla", "codigo_regla", "R_PIEZA_COMPUESTA_001")

    historiales = [
        (
            id_cot_1,
            id_regla_stock,
            id_supervisor,
            "MOTOR_INFERENCIA",
            to_json({"pieza": "engrane_recto", "material": "Acero 1018", "cantidad": 2}),
            "R_STOCK_MATERIAL_INSUFICIENTE_001 - revisión de stock",
            to_json({"stock_suficiente": True, "cantidad_disponible_m": 12.0}),
            to_json({"decision": "continuar_cotizacion", "requiere_compra": False}),
            "El material Acero 1018 está disponible para la cantidad solicitada; no se requiere compra.",
            0.95,
            0,
            1,
            "APROBADO",
            "Validación automática aceptable.",
        ),
        (
            id_cot_2,
            id_regla_herr,
            None,
            "MOTOR_INFERENCIA",
            to_json({"pieza": "buje_bronce_ranurado", "herramienta": "Cortador Especial de Ranuras", "stock": 1}),
            "R_HERRAMIENTA_AGOTADA_001 - herramienta bajo stock",
            to_json({"stock_unidades": 1, "stock_minimo": 2, "estado": "BAJO_STOCK"}),
            to_json({"decision": "validacion_pendiente", "sugerir_compra": True}),
            "La pieza requiere cortador especial, pero el stock está por debajo del mínimo; se recomienda validación y compra preventiva.",
            0.88,
            1,
            0,
            None,
            None,
        ),
        (
            id_cot_3,
            id_regla_comp,
            id_supervisor,
            "MOTOR_INFERENCIA",
            to_json({"pieza": "rodillo_impresion_completo", "subpiezas": ["rodillo_aluminio", "engrane_recto"]}),
            "R_PIEZA_COMPUESTA_001 - expansión de ensamble",
            to_json({"subpiezas_detectadas": True, "cantidad_subpiezas": 2}),
            to_json({"decision": "descomponer_ensamble", "procesos_sumados": True}),
            "La cotización se calculó sumando materiales y procesos de rodillo_aluminio y engrane_recto.",
            0.92,
            0,
            1,
            "APROBADO",
            "Supervisor aceptó la descomposición del ensamble.",
        ),
    ]

    for historial in historiales:
        id_cotizacion, id_regla, _, _, _, regla_evaluada, *_ = historial
        if not exists(
            cursor,
            "Historial_Inferencias",
            "id_cotizacion = ? AND id_regla = ? AND regla_evaluada = ?",
            (id_cotizacion, id_regla, regla_evaluada),
        ):
            cursor.execute(
                """
                INSERT INTO Historial_Inferencias
                (id_cotizacion, id_regla, id_usuario_validador, agente_origen,
                 entrada_json, regla_evaluada, condiciones_cumplidas_json, resultado_json,
                 explicacion_generada, confianza, requiere_validacion, validado,
                 decision_supervisor, comentarios_supervisor)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                historial,
            )

    # ============================================================
    # 11) ÓRDENES DE COMPRA
    # ============================================================
    id_proveedor_bronce = get_id(cursor, "Proveedores_Taller", "id_proveedor", "nombre_proveedor", "Metales y Bronces del Centro")
    id_proveedor_herr = get_id(cursor, "Proveedores_Taller", "id_proveedor", "nombre_proveedor", "Herramientas Industriales GDL")
    id_material_bronce = id_bronce
    id_herr_cortador = get_id(cursor, "Inventario_Herramientas", "id_herramienta", "codigo_herramienta", "HER-COR-RAN-01")
    id_almacen = get_id(cursor, "Usuarios_Internos", "id_usuario", "usuario", "almacen")

    ordenes_compra = [
        (
            "OC-2026-0001",
            now_text(),
            id_proveedor_bronce,
            id_cot_2,
            id_material_bronce,
            None,
            id_almacen,
            "MATERIAL",
            "Compra preventiva de barra redonda de bronce 5 pulgadas",
            3.0,
            "metros",
            2400.00,
            7200.00,
            date_plus_days(3),
            date_plus_days(5),
            "SOLICITADA",
            "Stock de bronce cercano al mínimo para cotización COT-2026-0002.",
            "Orden generada como ejemplo para probar flujo de compras.",
        ),
        (
            "OC-2026-0002",
            now_text(),
            id_proveedor_herr,
            id_cot_2,
            None,
            id_herr_cortador,
            id_almacen,
            "HERRAMIENTA",
            "Reposición de cortador especial de ranuras",
            2.0,
            "pieza",
            550.00,
            1100.00,
            date_plus_days(2),
            date_plus_days(4),
            "SOLICITADA",
            "Herramienta bajo stock detectada por regla de inferencia.",
            "Requerida para buje_bronce_ranurado.",
        ),
    ]

    cursor.executemany(
        """
        INSERT OR IGNORE INTO Ordenes_Compra
        (folio_compra, fecha_creacion, id_proveedor, id_cotizacion, id_material,
         id_herramienta, solicitante_usuario, tipo_compra, concepto, cantidad,
         unidad, costo_unitario_estimado, costo_total_estimado, fecha_requerida,
         fecha_entrega_estimada, estado_compra, motivo_compra, observaciones)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """,
        ordenes_compra,
    )

    conn.commit()

    # ============================================================
    # RESUMEN DE CARGA
    # ============================================================
    tablas = [
        "Usuarios_Internos",
        "Inventario_Taller",
        "Inventario_Herramientas",
        "Maquinas_Taller",
        "Tarifas_Taller",
        "Plantillas_Piezas",
        "Proveedores_Taller",
        "Reglas_Inferencia",
        "Cotizaciones_Ordenes",
        "Historial_Inferencias",
        "Ordenes_Compra",
    ]

    print("\nResumen de datos cargados:")
    for tabla in tablas:
        cursor.execute(f"SELECT COUNT(*) FROM {tabla};")
        total = cursor.fetchone()[0]
        print(f"✓ {tabla}: {total} registros")

    conn.close()
    print("\n✓ Datos semilla integrados exitosamente. Base de datos lista para ForgeFlow ERP.")


if __name__ == "__main__":
    init_db()
