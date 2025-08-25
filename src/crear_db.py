# crear_db.py
import os
import sqlite3
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "asistencias.db")

# Hash opcional para usuarios
try:
    from werkzeug.security import generate_password_hash
    CAN_HASH = True
except Exception:
    print("⚠️  werkzeug no disponible: se omite migración a password_hash.")
    CAN_HASH = False


# ------------------ Helpers ------------------
def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def has_column(cur, table, column):
    cur.execute(f"PRAGMA table_info({table})")
    return any(r[1] == column for r in cur.fetchall())

def ensure_table(cur, create_sql):
    cur.execute(create_sql)

def add_column_constant_default_if_missing(cur, table, name, type_sql, default_constant=None):
    """
    Agrega columna si falta; SOLO defaults CONSTANTES (no funciones como datetime('now')).
    """
    if not has_column(cur, table, name):
        if default_constant is None:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {name} {type_sql}")
        else:
            if isinstance(default_constant, str):
                cur.execute(f"ALTER TABLE {table} ADD COLUMN {name} {type_sql} DEFAULT '{default_constant}'")
            else:
                cur.execute(f"ALTER TABLE {table} ADD COLUMN {name} {type_sql} DEFAULT {default_constant}")

def add_timestamp_column_and_backfill_now(cur, table, name):
    """
    Agrega TEXT si falta y luego rellena con datetime('now') vía UPDATE
    (evita DEFAULT con funciones que SQLite no permite en ALTER TABLE).
    """
    if not has_column(cur, table, name):
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {name} TEXT")
    cur.execute(f"UPDATE {table} SET {name} = COALESCE({name}, datetime('now'))")

def ensure_index(cur, name, table, cols):
    cur.execute(f"CREATE INDEX IF NOT EXISTS {name} ON {table} ({cols})")


# ------------------ Seeds / Migraciones ------------------
def seed_admin(cur):
    cur.execute("SELECT COUNT(*) FROM usuarios")
    count = cur.fetchone()[0]
    if count == 0:
        if has_column(cur, "usuarios", "password_hash") and CAN_HASH:
            pwd = generate_password_hash("fibra123")
            cols, vals = [], []
            seed = {
                "usuario": "admin",
                "password_hash": pwd,
                "email": None,
                "nombre": "Administrador",
                "rol": "admin",
                "foto_url": None,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            for k, v in seed.items():
                if has_column(cur, "usuarios", k):
                    cols.append(k)
                    vals.append(v)
            sql = f"INSERT INTO usuarios ({', '.join(cols)}) VALUES ({', '.join(['?']*len(cols))})"
            cur.execute(sql, vals)
        else:
            cur.execute("INSERT INTO usuarios (usuario, contrasena) VALUES (?, ?)", ("admin", "fibra123"))
        print("✅ Usuario admin creado (usuario: admin / contraseña: fibra123).")
    else:
        print("ℹ️ Ya existe al menos un usuario en la tabla usuarios.")

def migrate_passwords_to_hash(cur):
    if not CAN_HASH or not has_column(cur, "usuarios", "password_hash"):
        return 0
    cur.execute("""
        SELECT id, contrasena FROM usuarios
        WHERE (password_hash IS NULL OR TRIM(password_hash) = '')
          AND contrasena IS NOT NULL AND TRIM(contrasena) <> ''
    """)
    rows = cur.fetchall()
    migrated = 0
    for r in rows:
        new_hash = generate_password_hash(r["contrasena"])
        cur.execute(
            "UPDATE usuarios SET password_hash=?, contrasena='', updated_at=datetime('now') WHERE id=?",
            (new_hash, r["id"])
        )
        migrated += 1
    return migrated

def seed_demo_items(cur):
    # Equipos
    cur.execute("SELECT COUNT(*) FROM equipos")
    if cur.fetchone()[0] == 0:
        equipos = [
            ("Router 5G", "Red", "Router de alta velocidad 5G"),
            ("ONU", "Red", "Unidad de red óptica"),
            ("Puntero por cantidad", "Herramienta", "Puntero para señal por cantidad"),
            ("Drop por metro", "Cableado", "Cable drop vendido por metro"),
        ]
        cur.executemany("INSERT INTO equipos (nombre, tipo, descripcion) VALUES (?, ?, ?)", equipos)
        print(f"✅ Insertados {len(equipos)} equipos de prueba.")
    else:
        print("ℹ️ Equipos ya cargados.")

    # Herramientas
    cur.execute("SELECT COUNT(*) FROM herramientas")
    if cur.fetchone()[0] == 0:
        herramientas = [
            ("Crimpadora", "Herramienta de red", "crimpadora.jpg"),
            ("Tester", "Medidor de señal", "tester.jpg"),
            ("Taladro", "Herramienta eléctrica", "taladro.jpg"),
        ]
        cur.executemany("INSERT INTO herramientas (nombre, tipo, imagen) VALUES (?, ?, ?)", herramientas)
        print(f"✅ Insertadas {len(herramientas)} herramientas de prueba.")
    else:
        print("ℹ️ Herramientas ya cargadas.")

def seed_demo_map(cur):
    """
    Carga datos de demo para que el mapa muestre algo:
    - Técnico 'Juan' (id=1) con tres posiciones recientes en tecnico_pos
    - Cliente Demo
    - Ticket con lat/lng y fecha reciente
    Solo inserta si no existen datos.
    """
    # Técnico demo
    cur.execute("SELECT id FROM tecnicos LIMIT 1")
    row_tec = cur.fetchone()
    if not row_tec:
        cur.execute("INSERT INTO tecnicos (id, nombre, activo) VALUES (1, 'Juan', 1)")
        tec_id = 1
        print("✅ Técnico demo creado (Juan, id=1).")
    else:
        tec_id = row_tec["id"]

    # Posiciones demo (solo si no hay posiciones)
    cur.execute("SELECT COUNT(*) AS c FROM tecnico_pos")
    if cur.fetchone()[0] == 0:
        cur.executemany("""
            INSERT INTO tecnico_pos (tecnico_id, lat, lng, ts)
            VALUES (?, ?, ?, ?)
        """, [
            (tec_id, -25.286, -57.645, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            (tec_id, -25.290, -57.640, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            (tec_id, -25.295, -57.635, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        ])
        print("✅ Posiciones demo agregadas a tecnico_pos.")
    else:
        print("ℹ️ Ya existen posiciones en tecnico_pos.")

    # Cliente demo
    cur.execute("SELECT id FROM clientes WHERE nombre='Cliente Demo'")
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO clientes (nombre, telefono, situacion, activo)
            VALUES ('Cliente Demo','0981111111','activo',1)
        """)
        print("✅ Cliente Demo creado.")
    else:
        print("ℹ️ Cliente Demo ya existe.")

    # Ticket demo con lat/lng
    cur.execute("SELECT COUNT(*) FROM asistencias")
    if cur.fetchone()[0] == 0:
        cur.execute("""
            INSERT INTO asistencias (cliente, direccion, tipo, prioridad, tecnico, problema, fecha, pppoe, lat, lng, estado, canal)
            VALUES ('Cliente Demo', 'Centro Asunción', 'Soporte', 'Media', 'Juan', 'Problema de prueba',
                    datetime('now'), 'cliente@spynet.com', -25.286, -57.645, 'pendiente', 'web')
        """)
        print("✅ Ticket demo con coordenadas creado.")
    else:
        print("ℹ️ Ya existen asistencias, no se crean tickets demo.")


# ------------------ Main migration ------------------
def main():
    conn = connect()
    cur = conn.cursor()

    # ---------- Asistencias ----------
    ensure_table(cur, """
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
    )""")
    # ampliaciones
    add_column_constant_default_if_missing(cur, "asistencias", "estado", "TEXT", default_constant="pendiente")
    add_column_constant_default_if_missing(cur, "asistencias", "lat", "REAL")
    add_column_constant_default_if_missing(cur, "asistencias", "lng", "REAL")
    add_column_constant_default_if_missing(cur, "asistencias", "cliente_id", "INTEGER")
    add_column_constant_default_if_missing(cur, "asistencias", "cedula", "TEXT")
    add_column_constant_default_if_missing(cur, "asistencias", "programada_en", "TEXT")
    add_column_constant_default_if_missing(cur, "asistencias", "tecnico_id", "INTEGER")
    add_column_constant_default_if_missing(cur, "asistencias", "canal", "TEXT", default_constant="web")
    cur.execute("UPDATE asistencias SET estado='pendiente' WHERE estado IS NULL OR TRIM(estado)=''")
    cur.execute("UPDATE asistencias SET canal='web'      WHERE canal  IS NULL OR TRIM(canal)  =''")

    # ---------- Equipos / Herramientas / Uso ----------
    ensure_table(cur, """
    CREATE TABLE IF NOT EXISTS equipos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        tipo TEXT NOT NULL,
        descripcion TEXT
    )""")
    ensure_table(cur, """
    CREATE TABLE IF NOT EXISTS herramientas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        tipo TEXT,
        imagen TEXT
    )""")
    ensure_table(cur, """
    CREATE TABLE IF NOT EXISTS uso_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_type TEXT NOT NULL,  -- 'equipo' | 'herramienta'
        item_id INTEGER NOT NULL,
        tecnico TEXT NOT NULL,
        fecha TEXT NOT NULL,
        servicio TEXT
    )""")
    ensure_table(cur, """
    CREATE TABLE IF NOT EXISTS fotos_asistencia (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        asistencia_id INTEGER,
        tecnico TEXT,
        ruta_foto TEXT NOT NULL,
        descripcion TEXT,
        fecha TEXT
    )""")

    # ---------- Usuarios ----------
    ensure_table(cur, """
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT UNIQUE NOT NULL,
        contrasena TEXT
    )""")
    add_column_constant_default_if_missing(cur, "usuarios", "password_hash", "TEXT")
    add_column_constant_default_if_missing(cur, "usuarios", "email", "TEXT")
    add_column_constant_default_if_missing(cur, "usuarios", "nombre", "TEXT")
    add_column_constant_default_if_missing(cur, "usuarios", "rol", "TEXT", default_constant="operador")
    add_column_constant_default_if_missing(cur, "usuarios", "foto_url", "TEXT")
    add_column_constant_default_if_missing(cur, "usuarios", "telefono", "TEXT")
    add_column_constant_default_if_missing(cur, "usuarios", "area", "TEXT")
    add_column_constant_default_if_missing(cur, "usuarios", "turno", "TEXT")
    add_column_constant_default_if_missing(cur, "usuarios", "dark_mode", "INTEGER", default_constant=0)
    add_column_constant_default_if_missing(cur, "usuarios", "notifs", "INTEGER", default_constant=1)
    add_timestamp_column_and_backfill_now(cur, "usuarios", "created_at")
    add_timestamp_column_and_backfill_now(cur, "usuarios", "updated_at")

    seed_admin(cur)
    migrated = migrate_passwords_to_hash(cur)
    if migrated:
        print(f"🔐 Migradas {migrated} contraseñas a password_hash.")

    # ---------- Clientes ----------
    ensure_table(cur, """
    CREATE TABLE IF NOT EXISTS clientes (
      id           INTEGER PRIMARY KEY AUTOINCREMENT,
      external_id  TEXT,           -- ID externo
      nombre       TEXT,
      referencia   TEXT,
      barrio       TEXT,
      telefono     TEXT,
      situacion    TEXT,
      exonerado    INTEGER DEFAULT 0,
      tipo         TEXT,           -- p.ej. 'cliente'
      valor        TEXT,           -- p.ej. '130.000'
      tipo_valor   TEXT,           -- compatibilidad si viene junto
      vencimiento  TEXT,
      cedula       TEXT,
      pppoe        TEXT,
      activo       INTEGER DEFAULT 1
    )""")
    # faltantes (si ya existía)
    add_column_constant_default_if_missing(cur, "clientes", "external_id", "TEXT")
    add_column_constant_default_if_missing(cur, "clientes", "nombre",      "TEXT")
    add_column_constant_default_if_missing(cur, "clientes", "referencia",  "TEXT")
    add_column_constant_default_if_missing(cur, "clientes", "barrio",      "TEXT")
    add_column_constant_default_if_missing(cur, "clientes", "telefono",    "TEXT")
    add_column_constant_default_if_missing(cur, "clientes", "situacion",   "TEXT")
    add_column_constant_default_if_missing(cur, "clientes", "exonerado",   "INTEGER", default_constant=0)
    add_column_constant_default_if_missing(cur, "clientes", "tipo",        "TEXT")
    add_column_constant_default_if_missing(cur, "clientes", "valor",       "TEXT")
    add_column_constant_default_if_missing(cur, "clientes", "tipo_valor",  "TEXT")
    add_column_constant_default_if_missing(cur, "clientes", "vencimiento", "TEXT")
    add_column_constant_default_if_missing(cur, "clientes", "cedula",      "TEXT")
    add_column_constant_default_if_missing(cur, "clientes", "pppoe",       "TEXT")
    add_column_constant_default_if_missing(cur, "clientes", "activo",      "INTEGER", default_constant=1)

    # ---------- Técnicos ----------
    ensure_table(cur, """
    CREATE TABLE IF NOT EXISTS tecnicos (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      nombre TEXT,
      telefono TEXT,
      activo INTEGER DEFAULT 1
    )""")
    add_column_constant_default_if_missing(cur, "tecnicos", "telefono_whatsapp", "TEXT")
    add_column_constant_default_if_missing(cur, "tecnicos", "movil", "TEXT")
    add_column_constant_default_if_missing(cur, "tecnicos", "tracking_token", "TEXT")
    add_column_constant_default_if_missing(cur, "tecnicos", "lat", "REAL")
    add_column_constant_default_if_missing(cur, "tecnicos", "lng", "REAL")
    add_column_constant_default_if_missing(cur, "tecnicos", "pos_updated_at", "TEXT")

    # ---------- Tracking de técnicos (histórico) ----------
    ensure_table(cur, """
    CREATE TABLE IF NOT EXISTS tecnico_tracks (
      id         INTEGER PRIMARY KEY AUTOINCREMENT,
      tecnico_id INTEGER NOT NULL,
      movil      TEXT,
      lat        REAL NOT NULL,
      lng        REAL NOT NULL,
      accuracy   REAL,
      battery    REAL,
      source     TEXT,
      ts         TEXT NOT NULL
    )""")

    # ---------- Posiciones puntuales (para el mapa) ----------
    ensure_table(cur, """
    CREATE TABLE IF NOT EXISTS tecnico_pos (
      id         INTEGER PRIMARY KEY AUTOINCREMENT,
      tecnico_id INTEGER NOT NULL,
      lat        REAL NOT NULL,
      lng        REAL NOT NULL,
      ts         TEXT NOT NULL
    )""")

    # ---------- ticket_fotos (opcional) ----------
    ensure_table(cur, """
    CREATE TABLE IF NOT EXISTS ticket_fotos (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      ticket_id INTEGER NOT NULL,
      archivo TEXT NOT NULL,
      created_at TEXT
    )""")
    add_timestamp_column_and_backfill_now(cur, "ticket_fotos", "created_at")

    # ---------- Índices ----------
    ensure_index(cur, "idx_asistencias_fecha",   "asistencias", "fecha")
    ensure_index(cur, "idx_asistencias_estado",  "asistencias", "estado")
    ensure_index(cur, "idx_asistencias_prog",    "asistencias", "programada_en")
    ensure_index(cur, "idx_asistencias_tecnico", "asistencias", "tecnico_id")

    ensure_index(cur, "idx_clientes_external", "clientes", "external_id")
    ensure_index(cur, "idx_clientes_tel",      "clientes", "telefono")
    ensure_index(cur, "idx_clientes_cedula",   "clientes", "cedula")
    ensure_index(cur, "idx_clientes_pppoe",    "clientes", "pppoe")

    ensure_index(cur, "idx_tracks_tecnico_ts",      "tecnico_tracks", "tecnico_id, ts")
    ensure_index(cur, "idx_tecnico_pos_tecnico_ts", "tecnico_pos",    "tecnico_id, ts")
    ensure_index(cur, "idx_uso_items_fecha",        "uso_items",      "fecha")

    # ---------- Seeds ----------
    seed_demo_items(cur)
    seed_demo_map(cur)

    conn.commit()
    conn.close()
    print("\n✅ Tablas, columnas e índices verificados/creados. BD lista.")


if __name__ == "__main__":
    main()