-- ============================================================
-- SCHEMA BASE: SISTEMA EXPERTO PARA TALLER DE MECANIZADO
-- ============================================================

-- 1. TABLA: Inventario de Materiales Comerciales
CREATE TABLE IF NOT EXISTS Inventario_Taller (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    material TEXT NOT NULL,             -- Ej. 'Acero 1045', 'Acero 8620', 'Aluminio 6061', 'Nylamid'
    perfil TEXT NOT NULL,               -- Ej. 'Barra Redonda', 'Solera', 'Placa'
    dimension_comercial REAL NOT NULL,   -- Diámetro o espesor comercial en pulgadas (Ej. 0.500, 1.000)
    cantidad_metros REAL NOT NULL,      -- Cantidad física disponible en el rack
    precio_por_metro REAL NOT NULL      -- Costo base por metro para la cotización
);

-- 2. TABLA: Tarifas de Maquinaria y Operaciones Especiales
CREATE TABLE IF NOT EXISTS Tarifas_Taller (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    concepto TEXT NOT NULL UNIQUE,       -- Ej. 'Hora_Torno', 'Hora_Fresadora', 'Hora_Perfiladora', 'Hechura_Machuelo', 'Hechura_Cuñero'
    tarifa_fija REAL NOT NULL           -- Costo en MXN asignado a la operación o tiempo
);

-- 3. TABLA: Directorio de Proveedores (Para alertas de desabastecimiento)
CREATE TABLE IF NOT EXISTS Directorio_Proveedores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    contacto_correo TEXT NOT NULL,
    material_principal TEXT NOT NULL    -- Material que surte principalmente
);

-- 4. TABLA: Historial de Cotizaciones y Órdenes Validadas
CREATE TABLE IF NOT EXISTS Cotizaciones_Ordenes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha_registro TEXT DEFAULT (datetime('now', 'localtime')),
    cliente TEXT NOT NULL,
    descripcion_pieza TEXT NOT NULL,    -- Texto original que envió el cliente
    material_solicitado TEXT NOT NULL,
    diametro_final REAL NOT NULL,       -- Dimensión final requerida por el cliente
    largo_solicitado REAL NOT NULL,      -- Longitud de la pieza en cm o pulgadas
    cantidad_piezas INTEGER NOT NULL,
    
    -- Campos calculados por el motor de inferencia (Python)
    material_usado TEXT,                -- El material comercial óptimo asignado
    diametro_comercial_usado REAL,      -- El diámetro de la barra elegida del inventario
    maquina_asignada TEXT,              -- Torno, Fresadora, etc.
    herramienta_asignada TEXT,          -- Buril Normal o Buril de Pastilla (carburo)
    tiempo_estimado_minutos REAL,       -- Tiempo de maquinado calculado según dureza
    costo_total REAL DEFAULT 0.0,
    
    -- Control de estado y explicabilidad de la IA
    estado_orden TEXT NOT NULL,         -- 'VIABLE_CON_STOCK', 'PENDIENTE_PROVEEDOR', 'RECHAZADO'
    reporte_explicabilidad TEXT         -- Output del Agente 3 detallando el razonamiento técnico
);

-- 5. TABLA: Inventario de Herramientas y Utillaje
CREATE TABLE IF NOT EXISTS Inventario_Herramientas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo_herramienta TEXT NOT NULL,     -- Ej. 'Broca de Centro', 'Broca Helicoidal', 'Buril de Pastilla', 'Buril HSS'
    medida REAL NOT NULL,               -- Dimensión en pulgadas (Ej. 0.375 para la de 3/8", 0.000 si no aplica como broca de centro)
    unidades_disponibles INTEGER NOT NULL, -- Cantidad en el cajón de herramientas
    estado_herramienta TEXT NOT NULL    -- 'DISPONIBLE', 'REQUERIR_AFILADO', 'AGOTADO'
);