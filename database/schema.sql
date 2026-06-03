-- ForgeFlow ERP - Esquema de Base de Datos SQL (SQLite)
-- Proyecto: Sistema Experto Multiagente para taller de torno y fresadora
-- Este esquema integra inventario, herramientas, maquinas, tarifas, plantillas,
-- proveedores, reglas de inferencia, historial de inferencias, cotizaciones,
-- ordenes de compra y usuarios internos.

PRAGMA foreign_keys = ON;

-- ============================================================
-- 1. TABLA: Usuarios internos del sistema
--    Sirve para identificar quien atiende, valida, supervisa o administra.
-- ============================================================
CREATE TABLE IF NOT EXISTS Usuarios_Internos (
    id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_completo TEXT NOT NULL,
    correo TEXT UNIQUE,
    usuario TEXT NOT NULL UNIQUE,
    password_hash TEXT, -- Guardar hash, no contrasena en texto plano
    rol TEXT NOT NULL DEFAULT 'OPERADOR'
        CHECK (rol IN ('ADMIN', 'SUPERVISOR', 'OPERADOR', 'VENTAS', 'ALMACEN')),
    estado TEXT NOT NULL DEFAULT 'ACTIVO'
        CHECK (estado IN ('ACTIVO', 'INACTIVO')),
    fecha_creacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ultimo_acceso TEXT
);

-- ============================================================
-- 2. TABLA: Inventario de materiales del taller
--    Materiales base disponibles para fabricar piezas.
-- ============================================================
CREATE TABLE IF NOT EXISTS Inventario_Taller (
    id_material INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo_material TEXT UNIQUE,
    material TEXT NOT NULL,                  -- Ej. 'Acero 1018', 'Aluminio 6061'
    perfil TEXT NOT NULL,                    -- Ej. 'Barra Redonda', 'Placa', 'Solera'
    dimension_principal REAL NOT NULL,        -- Diametro, espesor o medida principal
    unidad_dimension TEXT NOT NULL DEFAULT 'pulgadas'
        CHECK (unidad_dimension IN ('mm', 'cm', 'm', 'pulgadas')),
    cantidad_disponible REAL NOT NULL DEFAULT 0,
    unidad_inventario TEXT NOT NULL DEFAULT 'metros'
        CHECK (unidad_inventario IN ('metros', 'piezas', 'kg', 'placas')),
    costo_unitario REAL NOT NULL DEFAULT 0,
    stock_minimo REAL NOT NULL DEFAULT 0,
    ubicacion TEXT,                          -- Ej. 'Rack A', 'Estante 2'
    estado TEXT NOT NULL DEFAULT 'DISPONIBLE'
        CHECK (estado IN ('DISPONIBLE', 'BAJO_STOCK', 'AGOTADO', 'APARTADO')),
    fecha_actualizacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    observaciones TEXT
);

-- ============================================================
-- 3. TABLA: Inventario de herramientas
--    Herramientas, consumibles y herramental necesario para procesos.
-- ============================================================
CREATE TABLE IF NOT EXISTS Inventario_Herramientas (
    id_herramienta INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo_herramienta TEXT UNIQUE,
    nombre_herramienta TEXT NOT NULL,         -- Ej. 'Broca de Centro', 'Machuelo 3/8'
    tipo TEXT NOT NULL,                       -- Ej. 'Broca', 'Buril', 'Cortador', 'Machuelo'
    medida TEXT,                              -- Ej. '3/8', '10 mm', '1/2 NPT'
    material_herramienta TEXT,                -- Ej. 'HSS', 'Carburo', 'Insertos'
    stock_unidades INTEGER NOT NULL DEFAULT 0,
    stock_minimo INTEGER NOT NULL DEFAULT 0,
    costo_unitario REAL NOT NULL DEFAULT 0,
    ubicacion TEXT,
    estado TEXT NOT NULL DEFAULT 'DISPONIBLE'
        CHECK (estado IN ('DISPONIBLE', 'BAJO_STOCK', 'REQUERIR_AFILADO', 'EN_USO', 'AGOTADO', 'DAÑADA')),
    fecha_actualizacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    observaciones TEXT
);

-- ============================================================
-- 4. TABLA: Maquinas del taller
--    Capacidad disponible para torno, fresadora, CNC, taladro, etc.
-- ============================================================
CREATE TABLE IF NOT EXISTS Maquinas_Taller (
    id_maquina INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo_maquina TEXT NOT NULL UNIQUE,
    nombre_maquina TEXT NOT NULL,             -- Ej. 'Torno paralelo 1'
    tipo_maquina TEXT NOT NULL,               -- Ej. 'TORNO', 'FRESADORA', 'CNC', 'TALADRO'
    marca TEXT,
    modelo TEXT,
    capacidad_trabajo TEXT,                   -- Ej. 'Diametro max 300 mm, largo 1000 mm'
    precision_estimada TEXT,                  -- Ej. '+/- 0.05 mm'
    costo_hora_maquina REAL NOT NULL DEFAULT 0,
    estado TEXT NOT NULL DEFAULT 'DISPONIBLE'
        CHECK (estado IN ('DISPONIBLE', 'EN_USO', 'MANTENIMIENTO', 'FUERA_SERVICIO')),
    ubicacion TEXT,
    fecha_ultimo_mantenimiento TEXT,
    fecha_proximo_mantenimiento TEXT,
    observaciones TEXT
);

-- ============================================================
-- 5. TABLA: Tarifas del taller
--    Costos por proceso, mano de obra, maquina o servicio especial.
-- ============================================================
CREATE TABLE IF NOT EXISTS Tarifas_Taller (
    id_tarifa INTEGER PRIMARY KEY AUTOINCREMENT,
    concepto_proceso TEXT NOT NULL UNIQUE,    -- Ej. 'Hora_Torno', 'Rectificado', 'Ajuste'
    tipo_tarifa TEXT NOT NULL DEFAULT 'PROCESO'
        CHECK (tipo_tarifa IN ('PROCESO', 'MAQUINA', 'MANO_OBRA', 'SERVICIO_EXTERNO', 'AJUSTE')),
    costo_base REAL NOT NULL DEFAULT 0,
    unidad_cobro TEXT NOT NULL DEFAULT 'hora'
        CHECK (unidad_cobro IN ('hora', 'pieza', 'servicio', 'metro', 'kg')),
    margen_utilidad_porcentaje REAL NOT NULL DEFAULT 0,
    tiempo_minimo_horas REAL NOT NULL DEFAULT 0,
    descripcion TEXT,
    estado TEXT NOT NULL DEFAULT 'ACTIVA'
        CHECK (estado IN ('ACTIVA', 'INACTIVA')),
    fecha_actualizacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 6. TABLA: Plantillas de piezas
--    Base de conocimiento tecnica para piezas comunes.
-- ============================================================
CREATE TABLE IF NOT EXISTS Plantillas_Piezas (
    id_plantilla INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_pieza TEXT NOT NULL UNIQUE,        -- Ej. 'engrane_mamelon', 'buje', 'flecha'
    categoria TEXT,                           -- Ej. 'Transmision', 'Repuesto', 'Eje'
    descripcion TEXT,
    id_material_sugerido INTEGER,
    perfil_requerido TEXT,                    -- Ej. 'Barra Redonda'
    operaciones_base_json TEXT NOT NULL,       -- Lista JSON de procesos: ['Hora_Torno', 'Ranurado']
    herramientas_sugeridas_json TEXT,          -- Lista JSON de herramientas recomendadas
    maquinas_sugeridas_json TEXT,              -- Lista JSON de maquinas o tipos de maquina
    parametros_base_json TEXT,                 -- Datos tecnicos: tolerancias, diametros, largos, etc.
    subpiezas_requeridas_json TEXT,            -- Para piezas compuestas
    dificultad TEXT NOT NULL DEFAULT 'MEDIA'
        CHECK (dificultad IN ('BAJA', 'MEDIA', 'ALTA', 'CRITICA')),
    tiempo_base_horas REAL NOT NULL DEFAULT 0,
    estado TEXT NOT NULL DEFAULT 'ACTIVA'
        CHECK (estado IN ('ACTIVA', 'INACTIVA')),
    fecha_creacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_material_sugerido) REFERENCES Inventario_Taller(id_material)
        ON UPDATE CASCADE
        ON DELETE SET NULL
);

-- ============================================================
-- 7. TABLA: Proveedores del taller
--    Proveedores de materiales, herramientas y servicios externos.
-- ============================================================
CREATE TABLE IF NOT EXISTS Proveedores_Taller (
    id_proveedor INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_proveedor TEXT NOT NULL,
    tipo_proveedor TEXT NOT NULL DEFAULT 'MATERIALES'
        CHECK (tipo_proveedor IN ('MATERIALES', 'HERRAMIENTAS', 'SERVICIO_EXTERNO', 'MIXTO')),
    contacto_nombre TEXT,
    contacto_correo TEXT,
    contacto_telefono TEXT,
    direccion TEXT,
    especialidad TEXT,                        -- Ej. 'Metales', 'Tornilleria', 'Tratamiento termico'
    tiempo_entrega_estimado_dias INTEGER DEFAULT 0,
    condiciones_pago TEXT,
    calificacion INTEGER DEFAULT 5
        CHECK (calificacion BETWEEN 1 AND 5),
    estado TEXT NOT NULL DEFAULT 'ACTIVO'
        CHECK (estado IN ('ACTIVO', 'INACTIVO')),
    observaciones TEXT
);

-- ============================================================
-- 8. TABLA: Reglas de inferencia
--    Reglas IF-THEN para el motor experto generador de pedidos.
-- ============================================================
CREATE TABLE IF NOT EXISTS Reglas_Inferencia (
    id_regla INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo_regla TEXT NOT NULL UNIQUE,        -- Ej. 'R_MATERIAL_INSUFICIENTE_001'
    nombre_regla TEXT NOT NULL,
    agente_responsable TEXT NOT NULL DEFAULT 'MOTOR_INFERENCIA'
        CHECK (agente_responsable IN ('CHATBOT', 'MOTOR_INFERENCIA', 'SUPERVISOR_EXPLICADOR')),
    categoria TEXT NOT NULL,                  -- Ej. 'inventario', 'cotizacion', 'maquinado'
    prioridad INTEGER NOT NULL DEFAULT 1,      -- Mayor prioridad = se evalua primero
    condiciones_json TEXT NOT NULL,            -- Condiciones IF en JSON
    acciones_json TEXT NOT NULL,               -- Acciones THEN en JSON
    explicacion_base TEXT NOT NULL,            -- Texto usado por el agente explicador
    requiere_validacion INTEGER NOT NULL DEFAULT 0
        CHECK (requiere_validacion IN (0, 1)),
    estado TEXT NOT NULL DEFAULT 'ACTIVA'
        CHECK (estado IN ('ACTIVA', 'INACTIVA', 'PRUEBA')),
    fecha_creacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 9. TABLA: Cotizaciones y ordenes
--    Registro central del flujo: solicitud, cotizacion, produccion y cierre.
-- ============================================================
CREATE TABLE IF NOT EXISTS Cotizaciones_Ordenes (
    id_cotizacion INTEGER PRIMARY KEY AUTOINCREMENT,
    folio TEXT NOT NULL UNIQUE,
    fecha_creacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    id_usuario_creador INTEGER,
    id_usuario_validador INTEGER,
    cliente_nombre TEXT NOT NULL,
    cliente_contacto TEXT,
    cliente_correo TEXT,
    cliente_telefono TEXT,
    id_plantilla INTEGER,
    pieza_solicitada TEXT NOT NULL,
    tipo_servicio TEXT NOT NULL
        CHECK (tipo_servicio IN ('FABRICACION', 'REPARACION', 'MODIFICACION', 'MANTENIMIENTO')),
    cantidad_piezas INTEGER NOT NULL DEFAULT 1,
    dimensiones_json TEXT NOT NULL,            -- Datos ingresados por chatbot/usuario
    requerimientos_cliente TEXT,
    material_final TEXT,
    procesos_finales_json TEXT,                -- Procesos elegidos por inferencia o validados
    costo_materiales REAL NOT NULL DEFAULT 0,
    costo_herramientas REAL NOT NULL DEFAULT 0,
    costo_maquinado REAL NOT NULL DEFAULT 0,
    costo_servicios_externos REAL NOT NULL DEFAULT 0,
    costo_total REAL NOT NULL DEFAULT 0,
    margen_utilidad_porcentaje REAL NOT NULL DEFAULT 0,
    precio_final REAL NOT NULL DEFAULT 0,
    horas_maquinado_estimadas REAL NOT NULL DEFAULT 0,
    fecha_entrega_estimada TEXT,
    hoja_ruta_instrucciones TEXT,              -- Secuencia de trabajo generada
    explicacion_inferencia TEXT,               -- Resumen visible para supervisor/cliente
    estado_orden TEXT NOT NULL DEFAULT 'COTIZADO'
        CHECK (estado_orden IN ('BORRADOR', 'COTIZADO', 'VALIDACION_PENDIENTE', 'APROBADO', 'EN_PRODUCCION', 'FINALIZADA', 'CANCELADA')),
    observaciones TEXT,
    FOREIGN KEY (id_usuario_creador) REFERENCES Usuarios_Internos(id_usuario)
        ON UPDATE CASCADE
        ON DELETE SET NULL,
    FOREIGN KEY (id_usuario_validador) REFERENCES Usuarios_Internos(id_usuario)
        ON UPDATE CASCADE
        ON DELETE SET NULL,
    FOREIGN KEY (id_plantilla) REFERENCES Plantillas_Piezas(id_plantilla)
        ON UPDATE CASCADE
        ON DELETE SET NULL
);

-- ============================================================
-- 10. TABLA: Historial de inferencias
--     Guarda que reglas se dispararon, por que y con que resultado.
-- ============================================================
CREATE TABLE IF NOT EXISTS Historial_Inferencias (
    id_historial INTEGER PRIMARY KEY AUTOINCREMENT,
    id_cotizacion INTEGER,
    id_regla INTEGER,
    id_usuario_validador INTEGER,
    fecha_inferencia TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    agente_origen TEXT NOT NULL
        CHECK (agente_origen IN ('CHATBOT', 'MOTOR_INFERENCIA', 'SUPERVISOR_EXPLICADOR')),
    entrada_json TEXT NOT NULL,                -- Datos usados para evaluar
    regla_evaluada TEXT,                       -- Copia textual del codigo/nombre de la regla
    condiciones_cumplidas_json TEXT,           -- Evidencia encontrada
    resultado_json TEXT NOT NULL,              -- Decision generada
    explicacion_generada TEXT NOT NULL,
    confianza REAL DEFAULT 1.0
        CHECK (confianza >= 0 AND confianza <= 1),
    requiere_validacion INTEGER NOT NULL DEFAULT 0
        CHECK (requiere_validacion IN (0, 1)),
    validado INTEGER NOT NULL DEFAULT 0
        CHECK (validado IN (0, 1)),
    decision_supervisor TEXT
        CHECK (decision_supervisor IN ('APROBADO', 'RECHAZADO', 'AJUSTADO') OR decision_supervisor IS NULL),
    comentarios_supervisor TEXT,
    FOREIGN KEY (id_cotizacion) REFERENCES Cotizaciones_Ordenes(id_cotizacion)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    FOREIGN KEY (id_regla) REFERENCES Reglas_Inferencia(id_regla)
        ON UPDATE CASCADE
        ON DELETE SET NULL,
    FOREIGN KEY (id_usuario_validador) REFERENCES Usuarios_Internos(id_usuario)
        ON UPDATE CASCADE
        ON DELETE SET NULL
);

-- ============================================================
-- 11. TABLA: Ordenes de compra
--     Solicitudes de compra ligadas a inventario, herramientas o cotizaciones.
-- ============================================================
CREATE TABLE IF NOT EXISTS Ordenes_Compra (
    id_orden_compra INTEGER PRIMARY KEY AUTOINCREMENT,
    folio_compra TEXT NOT NULL UNIQUE,
    fecha_creacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    id_proveedor INTEGER,
    id_cotizacion INTEGER,
    id_material INTEGER,
    id_herramienta INTEGER,
    solicitante_usuario INTEGER,
    tipo_compra TEXT NOT NULL DEFAULT 'MATERIAL'
        CHECK (tipo_compra IN ('MATERIAL', 'HERRAMIENTA', 'SERVICIO_EXTERNO', 'MIXTA')),
    concepto TEXT NOT NULL,
    cantidad REAL NOT NULL DEFAULT 1,
    unidad TEXT NOT NULL DEFAULT 'pieza',
    costo_unitario_estimado REAL NOT NULL DEFAULT 0,
    costo_total_estimado REAL NOT NULL DEFAULT 0,
    fecha_requerida TEXT,
    fecha_entrega_estimada TEXT,
    estado_compra TEXT NOT NULL DEFAULT 'SOLICITADA'
        CHECK (estado_compra IN ('SOLICITADA', 'APROBADA', 'ENVIADA', 'RECIBIDA', 'CANCELADA')),
    motivo_compra TEXT,                       -- Ej. 'Stock insuficiente para cotizacion X'
    observaciones TEXT,
    FOREIGN KEY (id_proveedor) REFERENCES Proveedores_Taller(id_proveedor)
        ON UPDATE CASCADE
        ON DELETE SET NULL,
    FOREIGN KEY (id_cotizacion) REFERENCES Cotizaciones_Ordenes(id_cotizacion)
        ON UPDATE CASCADE
        ON DELETE SET NULL,
    FOREIGN KEY (id_material) REFERENCES Inventario_Taller(id_material)
        ON UPDATE CASCADE
        ON DELETE SET NULL,
    FOREIGN KEY (id_herramienta) REFERENCES Inventario_Herramientas(id_herramienta)
        ON UPDATE CASCADE
        ON DELETE SET NULL,
    FOREIGN KEY (solicitante_usuario) REFERENCES Usuarios_Internos(id_usuario)
        ON UPDATE CASCADE
        ON DELETE SET NULL
);

-- ============================================================
-- INDICES RECOMENDADOS
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_inventario_material_perfil
ON Inventario_Taller(material, perfil);

CREATE INDEX IF NOT EXISTS idx_herramientas_tipo_estado
ON Inventario_Herramientas(tipo, estado);

CREATE INDEX IF NOT EXISTS idx_maquinas_tipo_estado
ON Maquinas_Taller(tipo_maquina, estado);

CREATE INDEX IF NOT EXISTS idx_tarifas_tipo_estado
ON Tarifas_Taller(tipo_tarifa, estado);

CREATE INDEX IF NOT EXISTS idx_plantillas_categoria_estado
ON Plantillas_Piezas(categoria, estado);

CREATE INDEX IF NOT EXISTS idx_proveedores_tipo_estado
ON Proveedores_Taller(tipo_proveedor, estado);

CREATE INDEX IF NOT EXISTS idx_reglas_categoria_prioridad
ON Reglas_Inferencia(categoria, prioridad DESC, estado);

CREATE INDEX IF NOT EXISTS idx_cotizaciones_estado_fecha
ON Cotizaciones_Ordenes(estado_orden, fecha_creacion);

CREATE INDEX IF NOT EXISTS idx_historial_cotizacion_fecha
ON Historial_Inferencias(id_cotizacion, fecha_inferencia);

CREATE INDEX IF NOT EXISTS idx_ordenes_compra_estado_fecha
ON Ordenes_Compra(estado_compra, fecha_creacion);

-- ============================================================
-- DATOS BASE MINIMOS OPCIONALES
-- Puedes borrar esta seccion si quieres cargar todo desde JSON.
-- ============================================================
INSERT OR IGNORE INTO Usuarios_Internos
(nombre_completo, correo, usuario, rol, estado)
VALUES
('Administrador ForgeFlow', 'admin@forgeflow.local', 'admin', 'ADMIN', 'ACTIVO');

INSERT OR IGNORE INTO Tarifas_Taller
(concepto_proceso, tipo_tarifa, costo_base, unidad_cobro, margen_utilidad_porcentaje, tiempo_minimo_horas, descripcion, estado)
VALUES
('Hora_Torno', 'MAQUINA', 350.00, 'hora', 20.00, 0.50, 'Tarifa base por hora de torno convencional', 'ACTIVA'),
('Hora_Fresadora', 'MAQUINA', 400.00, 'hora', 20.00, 0.50, 'Tarifa base por hora de fresadora', 'ACTIVA'),
('Ajuste_Manual', 'MANO_OBRA', 250.00, 'hora', 15.00, 0.25, 'Ajuste, desbaste manual y verificacion', 'ACTIVA'),
('Servicio_Externo', 'SERVICIO_EXTERNO', 0.00, 'servicio', 20.00, 0.00, 'Costo variable de servicio externo', 'ACTIVA');

INSERT OR IGNORE INTO Reglas_Inferencia
(codigo_regla, nombre_regla, agente_responsable, categoria, prioridad, condiciones_json, acciones_json, explicacion_base, requiere_validacion, estado)
VALUES
(
    'R_STOCK_MATERIAL_INSUFICIENTE_001',
    'Detectar material insuficiente para fabricar pieza',
    'MOTOR_INFERENCIA',
    'inventario',
    10,
    '{"si":"cantidad_disponible < cantidad_requerida"}',
    '{"entonces":["marcar_validacion_pendiente","generar_sugerencia_orden_compra"]}',
    'El sistema detecto que el material disponible no cubre la cantidad requerida para la cotizacion.',
    1,
    'ACTIVA'
),
(
    'R_HERRAMIENTA_AGOTADA_001',
    'Detectar herramienta agotada o no disponible',
    'MOTOR_INFERENCIA',
    'herramientas',
    9,
    '{"si":"herramienta_requerida.estado IN (AGOTADO, DAÑADA, REQUERIR_AFILADO)"}',
    '{"entonces":["buscar_alternativa","solicitar_compra_o_mantenimiento"]}',
    'La herramienta necesaria no esta disponible en condiciones adecuadas; se requiere alternativa, compra o mantenimiento.',
    1,
    'ACTIVA'
),
(
    'R_MAQUINA_NO_DISPONIBLE_001',
    'Validar disponibilidad de maquina requerida',
    'MOTOR_INFERENCIA',
    'maquinado',
    8,
    '{"si":"maquina_requerida.estado != DISPONIBLE"}',
    '{"entonces":["reprogramar_fecha_entrega","solicitar_validacion_supervisor"]}',
    'La maquina requerida no esta disponible, por lo que la fecha de entrega debe revisarse antes de aprobar la cotizacion.',
    1,
    'ACTIVA'
);
