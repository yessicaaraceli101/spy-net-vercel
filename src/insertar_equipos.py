import sqlite3

conn = sqlite3.connect("asistencias.db")
cursor = conn.cursor()

# Tabla asistencias
cursor.execute("""
CREATE TABLE IF NOT EXISTS asistencias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente TEXT,
    direccion TEXT,
    tipo TEXT,
    prioridad TEXT,
    tecnico TEXT,
    problema TEXT,
    fecha TEXT,
    pppoe TEXT
)
""")

# Tabla equipos
cursor.execute("""
CREATE TABLE IF NOT EXISTS equipos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    tipo TEXT NOT NULL,
    descripcion TEXT
)
""")

# Tabla herramientas
cursor.execute("""
CREATE TABLE IF NOT EXISTS herramientas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    tipo TEXT,
    imagen TEXT
)
""")

# Tabla uso de equipos y herramientas
cursor.execute("""
CREATE TABLE IF NOT EXISTS uso_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_type TEXT NOT NULL,
    item_id INTEGER NOT NULL,
    tecnico TEXT NOT NULL,
    fecha TEXT NOT NULL,
    servicio TEXT
)
""")

# Tabla fotos de asistencia o instalación
cursor.execute("""
CREATE TABLE IF NOT EXISTS fotos_asistencia (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asistencia_id INTEGER,
    tecnico TEXT,
    ruta_foto TEXT NOT NULL,
    descripcion TEXT,
    fecha TEXT
)
""")

# Insertar equipos si no existen
cursor.execute("SELECT COUNT(*) FROM equipos")
if cursor.fetchone()[0] == 0:
    equipos = [
        ("Router 5G", "Red", "Router de alta velocidad 5G"),
        ("ONU", "Red", "Unidad de red óptica"),
        ("Puntero por cantidad", "Herramienta", "Puntero para señal por cantidad"),
        ("Drop por metro", "Cableado", "Cable drop vendido por metro")
    ]
    cursor.executemany("INSERT INTO equipos (nombre, tipo, descripcion) VALUES (?, ?, ?)", equipos)
    print(f"✅ Insertados {len(equipos)} equipos de prueba.")
else:
    print("ℹ️ Equipos ya cargados.")

# Insertar herramientas si no existen
cursor.execute("SELECT COUNT(*) FROM herramientas")
if cursor.fetchone()[0] == 0:
    herramientas = [
        ("Crimpadora", "Herramienta de red", "crimpadora.jpg"),
        ("Tester", "Medidor de señal", "tester.jpg"),
        ("Taladro", "Herramienta eléctrica", "taladro.jpg")
    ]
    cursor.executemany("INSERT INTO herramientas (nombre, tipo, imagen) VALUES (?, ?, ?)", herramientas)
    print(f"✅ Insertadas {len(herramientas)} herramientas de prueba.")
else:
    print("ℹ️ Herramientas ya cargadas.")

conn.commit()
conn.close()

print("\n✅ Tablas y datos iniciales creados correctamente.")
