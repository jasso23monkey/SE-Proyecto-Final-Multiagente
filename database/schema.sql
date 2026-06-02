-- ForgeFlow ERP - Esquema de Base de Datos SQL (SQLite)

-- 1. TABLA: Inventario de Materiales Base (Rack)
CREATE TABLE IF NOT EXISTS Inventario_Taller (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    material TEXT NOT NULL,         -- Ej. 'Acero 1018', 'Aluminio 6061', 'Bronce'
    perfil TEXT NOT NULL,           -- Ej. 'Barra Redonda', 'Placa', 'Solera'
    dimension_pulgadas REAL NOT NULL, -- Diámetro o espesor en pulgadas
    cantidad_metros REAL NOT NULL,  -- Existencia actual en metros
    costo_por_metro REAL NOT NULL   -- Costo para el cálculo de presupuesto
);

-- 2. TABLA: Inventario de Herramental (Cajón de herramientas)
CREATE TABLE IF NOT EXISTS Inventario_Herramientas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_herramienta TEXT NOT NULL, -- Ej. 'Broca de Centro', 'Machuelo 3/8', 'Cortador Especial'
    tipo TEXT NOT NULL,               -- Ej. 'Broca', 'Buril', 'Cortador', 'Machuelo'
    estado TEXT DEFAULT 'DISPONIBLE', -- 'DISPONIBLE', 'REQUERIR_AFILADO', 'AGOTADO'
    stock_unidades INTEGER NOT NULL
);

-- 3. TABLA: Tarifas del Taller (Precios de mano de obra y procesos especiales)
CREATE TABLE IF NOT EXISTS Tarifas_Taller (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    concepto_proceso TEXT NOT NULL UNIQUE, -- Ej. 'Hora_Torno', 'Acomodo_Helicoidal'
    costo_base_hora REAL NOT NULL,
    descripcion TEXT
);

-- 4. TABLA: Plantillas de Configuración de Piezas (El Cerebro del Sistema Experto)
CREATE TABLE IF NOT EXISTS Plantillas_Piezas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_pieza TEXT NOT NULL UNIQUE,       -- Ej. 'engrane_mamelon', 'rodillo_impresion_completo'
    material_predeterminado TEXT,            -- Puede ser NULL en piezas compuestas
    perfil_requerido TEXT,                   -- Ej. 'Barra Redonda'
    operaciones_base TEXT,                   -- Lista separada por comas de procesos en Tarifas_Taller
    subpiezas_requeridas TEXT                -- Lista de otras piezas de las que depende (para compuestos)
);

-- 5. TABLA: Directorio de Proveedores
CREATE TABLE IF NOT EXISTS Proveedores_Taller (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_proveedor TEXT NOT NULL,
    contacto_correo TEXT,
    especialidad TEXT                        -- Ej. 'Metales', 'Herramientas y Tornillería'
);

-- 6. TABLA: ERP - Registro Central de Cotizaciones e Historial de Producción
CREATE TABLE IF NOT EXISTS Cotizaciones_Ordenes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha_creacion TEXT NOT NULL,
    cliente_nombre TEXT NOT NULL,
    pieza_solicitada TEXT NOT NULL,
    tipo_servicio TEXT NOT NULL,             -- 'FABRICACION' o 'REPARACION'
    dimensiones_json TEXT NOT NULL,          -- Dimensiones finales que ingresó el usuario
    costo_total REAL NOT NULL,
    estado_orden TEXT DEFAULT 'COTIZADO',    -- 'COTIZADO', 'EN_PRODUCCION', 'FINALIZADA'
    horas_maquinado_estimadas REAL NOT NULL, -- Para el cálculo de cola de trabajo
    fecha_entrega_estimada TEXT,
    hoja_ruta_instrucciones TEXT             -- Secuencia de maquinado autogenerada
);