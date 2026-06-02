import sqlite3
import os
from datetime import datetime

DB_PATH = "database/forgeflow.db"

def init_db():
    # Asegurar que el directorio exista
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Leer y ejecutar el archivo schema.sql
    with open("database/schema.sql", "r", encoding="utf-8") as f:
        schema = f.read()
    cursor.executescript(schema)
    
    print("✓ Estructura de ForgeFlow ERP creada correctamente.")

    # 1. Inyectar Catálogo de Tarifas Base y Procesos Especiales
    tarifas = [
        ('Hora_Torno', 350.00, 'Maquinado general en torno convencional'),
        ('Hora_Fresadora', 400.00, 'Corte general de dientes o planeado en fresa'),
        ('Acomodo_Especial_Helicoidal', 600.00, 'Tarifa fija por ajuste de tren de engranes y ángulo en fresadora'),
        ('Hechura_Machuelo', 80.00, 'Proceso de roscado con machuelo para opresor'),
        ('Ranurado_Interno_Bronce', 250.00, 'Recargo por maquinado de ranuras internas en bronce con machuelo'),
        ('Cortador_Especial_Externo', 180.00, 'Uso de herramienta/cortador especial para ranura externa en fresa'),
        ('Caja_Balero', 150.00, 'Ajuste milimétrico de precisión para baleros (interiores)'),
        ('Ajuste_Reparacion_General', 300.00, 'Tarifa base de mano de obra para rectificados o modificaciones')
    ]
    cursor.executemany("INSERT OR IGNORE INTO Tarifas_Taller (concepto_proceso, costo_base_hora, descripcion) VALUES (?, ?, ?);", tarifas)

    # 2. Inyectar Inventario de Materiales Base (Rack Inicial)
    materiales = [
        ('Acero 1018', 'Barra Redonda', 2.0, 12.0, 450.00),
        ('Acero 1045', 'Barra Redonda', 3.0, 6.0, 680.00),
        ('Aluminio 6061', 'Barra Redonda', 4.0, 18.0, 950.00),
        ('Bronce', 'Barra Redonda', 5.0, 3.0, 2400.00),
        ('Cobre', 'Barra Redonda', 1.0, 4.0, 1800.00)
    ]
    cursor.executemany("INSERT OR IGNORE INTO Inventario_Taller (material, perfil, dimension_pulgadas, cantidad_metros, costo_por_metro) VALUES (?, ?, ?, ?, ?);", materiales)

    # 3. Inyectar Cajón de Herramientas de Rigor
    herramientas = [
        ('Broca de Centro', 'Broca', 'DISPONIBLE', 5),
        ('Buril de Pastilla (Carburo)', 'Buril', 'DISPONIBLE', 8),
        ('Buril de Interiores', 'Buril', 'DISPONIBLE', 3),
        ('Cortador de Fresadora Recto', 'Cortador', 'DISPONIBLE', 4),
        ('Cortador Especial de Ranuras', 'Cortador', 'DISPONIBLE', 2),
        ('Machuelo para Opresor', 'Machuelo', 'DISPONIBLE', 4)
    ]
    cursor.executemany("INSERT OR IGNORE INTO Inventario_Herramientas (nombre_herramienta, tipo, estado, stock_unidades) VALUES (?, ?, ?, ?);", herramientas)

    # 4. Inyectar Directorio de Proveedores
    # 4. Inyectar Directorio de Proveedores (Corregido 'especialidad')
    proveedores = [
        ('Aceros Monterrey S.A.', 'ventas@acerosmty.com', 'Metales'),
        ('Herramientas Industriales GDL', 'contacto@herramientasgdl.com', 'Herramientas y Tornillería')
    ]
    cursor.executemany("INSERT OR IGNORE INTO Proveedores_Taller (nombre_proveedor, contacto_correo, especialidad) VALUES (?, ?, ?);", proveedores)

    # 5. El Cerebro del Sistema Experto: Las Plantillas con Reglas de Dependencia
    # Formato: (nombre_pieza, material_predeterminado, perfil_requerido, operaciones_base, subpiezas_requeridas)
    plantillas = [
        # --- Piezas Base (Simples) ---
        ('engrane_recto', 'Acero 1018', 'Barra Redonda', 'Hora_Torno,Hora_Fresadora', None),
        ('engrane_mamelon', 'Acero 1018', 'Barra Redonda', 'Hora_Torno,Hora_Fresadora,Hechura_Machuelo', None),
        ('engrane_helicoidal', 'Acero 1045', 'Barra Redonda', 'Hora_Torno,Hora_Fresadora,Acomodo_Especial_Helicoidal', None),
        ('rodillo_aluminio', 'Aluminio 6061', 'Barra Redonda', 'Hora_Torno,Caja_Balero', None),
        ('rodillo_acero_yunque', 'Acero 1045', 'Barra Redonda', 'Hora_Torno,Caja_Balero', None),
        ('buje_bronce_ranurado', 'Bronce', 'Barra Redonda', 'Hora_Torno,Hora_Fresadora,Ranurado_Interno_Bronce,Cortador_Especial_Externo', None),
        ('buje_cobre', 'Cobre', 'Barra Redonda', 'Hora_Torno', None),
        
        # --- Ensambles Compuestos (Heredan reglas lógicamente sin duplicar código) ---
        ('rodillo_impresion_completo', None, None, None, 'rodillo_aluminio,engrane_recto'),
        ('yunque_completo', None, None, None, 'rodillo_acero_yunque,engrane_recto')
    ]
    cursor.executemany("INSERT OR IGNORE INTO Plantillas_Piezas (nombre_pieza, material_predeterminado, perfil_requerido, operaciones_base, subpiezas_requeridas) VALUES (?, ?, ?, ?, ?);", plantillas)

    conn.commit()
    conn.close()
    print("✓ Datos semilla integrados exitosamente. Base de datos lista para ForgeFlow ERP.")

if __name__ == "__main__":
    init_db()