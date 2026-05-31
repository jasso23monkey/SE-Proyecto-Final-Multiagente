import sqlite3
import os

def inicializar_y_poblar_bd():
    # Rutas relativas para asegurar la portabilidad del proyecto
    base_dir = os.path.dirname(os.path.abspath(__file__))
    schema_path = os.path.join(base_dir, 'schema.sql')
    db_path = os.path.join(base_dir, '..', 'taller.db') # Se creará en la raíz del proyecto

    print("Conectando a la base de datos local SQLite...")
    conexion = sqlite3.connect(db_path)
    cursor = conexion.cursor()

    # 1. Leer y ejecutar el archivo schema.sql
    print("Leyendo esquema de tablas...")
    if os.path.exists(schema_path):
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        cursor.executescript(schema_sql)
        print("✓ Tablas creadas con éxito.")
    else:
        print(f"❌ Error: No se encontró el archivo schema.sql en {schema_path}")
        return

    # 2. Insertar Datos Semilla: Tarifas de Maquinaria y Hechuras Especiales
    print("Insertando tarifas de operación...")
    tarifas = [
        ('Hora_Torno', 450.00),         # Precio por hora en MXN
        ('Hora_Fresadora', 500.00),     # Precio por hora en MXN
        ('Hora_Perfiladora', 400.00),   # Precio por hora en MXN
        ('Hechura_Machuelo', 80.00),    # Costo por unidad/barreno machuelado
        ('Hechura_Cuñero', 150.00)      # Costo por cuñero individual
    ]
    
    # Usamos INSERT OR IGNORE para evitar duplicados si corres el script más de una vez
    cursor.executemany("""
        INSERT OR IGNORE INTO Tarifas_Taller (concepto, tarifa_fija) 
        VALUES (?, ?);
    """, tarifas)

    # 3. Insertar Datos Semilla: Inventario de Materiales (Aceros, Aluminio, Plásticos)
    # Dimensiones comerciales expresadas en pulgadas decimales
    print("Poblando rack de inventario de materiales...")
    inventario = [
        # Material, Perfil, Dimensión Comercial (pulgadas), Cantidad (metros), Precio/metro MXN
        ('Acero 1018', 'Barra Redonda', 0.500, 6.0, 180.00),
        ('Acero 1018', 'Barra Redonda', 1.000, 12.0, 350.00),
        ('Acero 1018', 'Barra Redonda', 1.500, 4.5, 580.00),
        ('Acero 1018', 'Barra Redonda', 2.000, 3.0, 920.00),
        ('Acero 1018', 'Barra Redonda', 2.500, 1.5, 1400.00),
        
        ('Acero 1045', 'Barra Redonda', 0.500, 8.0, 220.00),
        ('Acero 1045', 'Barra Redonda', 1.000, 10.0, 420.00),
        ('Acero 1045', 'Barra Redonda', 1.500, 6.0, 710.00),
        ('Acero 1045', 'Barra Redonda', 2.000, 4.0, 1150.00),
        ('Acero 1045', 'Barra Redonda', 2.500, 2.0, 1750.00),
        
        ('Aluminio 6061', 'Barra Redonda', 1.000, 5.0, 650.00),
        ('Aluminio 6061', 'Barra Redonda', 2.000, 2.5, 1900.00),
        
        ('Acero 8620', 'Barra Redonda', 1.000, 0.0, 620.00),   # 0 metros para forzar regla de desabastecimiento
        ('Acero 8620', 'Barra Redonda', 1.500, 2.0, 980.00),
        
        ('Nylamid', 'Barra Redonda', 1.000, 4.0, 280.00),
        ('Bronce', 'Barra Redonda', 1.000, 2.0, 1500.00)
    ]
    
    cursor.executemany("""
        INSERT INTO Inventario_Taller (material, perfil, dimension_comercial, cantidad_metros, precio_por_metro)
        VALUES (?, ?, ?, ?, ?);
    """, inventario)

    # 4. Insertar Datos Semilla: Directorio de Proveedores de Respaldo
    print("Registrando directorio de proveedores...")
    proveedores = [
        ('Aceros Monterrey S.A.', 'proveedor_mty@taller.com', 'Acero 1018, Acero 1045, Acero 8620'),
        ('Metales y Aluminios del Centro', 'contacto_metales@taller.com', 'Aluminio 6061, Bronce'),
        ('Plásticos Industriales Bajío', 'ventas_plasticos@taller.com', 'Nylamid')
    ]
    
    cursor.executemany("""
        INSERT INTO Directorio_Proveedores (nombre, contacto_correo, material_principal)
        VALUES (?, ?, ?);
    """, proveedores)

    # Guardar cambios y cerrar de forma segura
    conexion.commit()
    conexion.close()
    print("\n✓ ¡Base de datos 'taller.db' inicializada y poblada correctamente de forma local!")

if __name__ == "__main__":
    inicializar_y_poblar_bd()