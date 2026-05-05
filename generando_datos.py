import pymysql as mysql_connector
import random
from datetime import datetime, timedelta

HOST = "mysql-practica2"
PORT = 3306
USER = "alumne"
PASSWORD = "alumne1234"
DATABASE = "example"
TOTAL_ROWS = 5_000_000
BATCH_SIZE = 10_000

conn = mysql_connector.connect(
    host=HOST, port=PORT, user=USER, password=PASSWORD, database=DATABASE
)
cursor = conn.cursor()

# ── 1. Analizar datos reales ───────────────────────────────────────────────
print("Analizando datos existentes...")

cursor.execute("SELECT COUNT(*) FROM electric_data")
count = cursor.fetchone()[0]
if count > 0:
    print(f"Tabla ya tiene {count} filas. Saltando generación.")
    conn.close()
    exit(0)

cursor.execute("""
    SELECT
        MIN(consumo), MAX(consumo), AVG(consumo), STDDEV(consumo),
        MIN(generacion), MAX(generacion), AVG(generacion), STDDEV(generacion),
        MIN(hora_dia), MAX(hora_dia),
        MIN(fecha), MAX(fecha),
        COUNT(DISTINCT Poblacion),
        COALESCE(MAX(idexcel), 0)
    FROM electric_data
""")
stats = cursor.fetchone()

consumo_min, consumo_max, consumo_avg, consumo_std  = stats[0], stats[1], stats[2], stats[3]
gen_min,     gen_max,     gen_avg,     gen_std       = stats[4], stats[5], stats[6], stats[7]
hora_min,    hora_max                                 = int(stats[8]), int(stats[9])
fecha_min,   fecha_max                               = stats[10], stats[11]
last_id                                              = int(stats[13])

print(f"  consumo   : {consumo_min:.2f} – {consumo_max:.2f}  (avg={consumo_avg:.2f}, std={consumo_std:.2f})")
print(f"  generacion: {gen_min:.2f} – {gen_max:.2f}  (avg={gen_avg:.2f}, std={gen_std:.2f})")
print(f"  hora_dia  : {hora_min} – {hora_max}")
print(f"  fechas    : {fecha_min} → {fecha_max}")
print(f"  last_id   : {last_id}")

cursor.execute("SELECT DISTINCT Poblacion FROM electric_data WHERE Poblacion IS NOT NULL")
poblaciones = [row[0] for row in cursor.fetchall()]
print(f"  poblaciones encontradas: {len(poblaciones)} -> {poblaciones[:5]}...")

sample_fecha = fecha_min
for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
    try:
        dt_min = datetime.strptime(sample_fecha, fmt)
        dt_max = datetime.strptime(fecha_max, fmt)
        fecha_fmt = fmt
        break
    except (ValueError, TypeError):
        continue
else:
    dt_min = datetime(2018, 1, 1)
    dt_max = datetime(2024, 12, 31)
    fecha_fmt = "%Y-%m-%d"

date_range_days = (dt_max - dt_min).days
print(f"  formato fecha: {fecha_fmt}  |  rango: {date_range_days} días")

cursor.execute("""
    SELECT hora_dia, COUNT(*) as cnt
    FROM electric_data
    WHERE hora_dia IS NOT NULL
    GROUP BY hora_dia
    ORDER BY hora_dia
""")
hora_rows = cursor.fetchall()
hora_horas = [r[0] for r in hora_rows]
hora_pesos = [r[1] for r in hora_rows]

# ── 2. Insertar datos similares ───────────────────────────────────────────
insert_sql = """
    INSERT INTO electric_data (idexcel, fecha, hora_dia, consumo, generacion, Poblacion)
    VALUES (%s, %s, %s, %s, %s, %s)
"""

def gen_valor(avg, std, vmin, vmax):
    v = random.gauss(avg, std)
    return round(max(vmin, min(vmax, v)), 4)

batch = []
inserted = 0
current_id = last_id + 1

print(f"\nInsertando {TOTAL_ROWS:,} filas en batches de {BATCH_SIZE:,}...")

for i in range(TOTAL_ROWS):
    delta = random.randint(0, date_range_days)
    fecha = (dt_min + timedelta(days=delta)).strftime(fecha_fmt)

    hora_dia   = random.choices(hora_horas, weights=hora_pesos, k=1)[0]
    consumo    = gen_valor(consumo_avg, consumo_std, consumo_min, consumo_max)
    generacion = gen_valor(gen_avg, gen_std, gen_min, gen_max)
    poblacion  = random.choice(poblaciones)

    batch.append((current_id, fecha, hora_dia, consumo, generacion, poblacion))
    current_id += 1

    if len(batch) >= BATCH_SIZE:
        cursor.executemany(insert_sql, batch)
        conn.commit()
        inserted += len(batch)
        batch = []
        if inserted % 500_000 == 0:
            print(f"  -> {inserted:,} filas insertadas...")

if batch:
    cursor.executemany(insert_sql, batch)
    conn.commit()
    inserted += len(batch)

print(f"\nTotal insertado: {inserted:,} filas. ID final: {current_id - 1}")
cursor.close()
conn.close()
