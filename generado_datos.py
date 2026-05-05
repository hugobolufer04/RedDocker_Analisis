import pandas as pd
import numpy as np
from sqlalchemy import create_engine

# --- CONFIGURACIÓN VALIDADA CON DOCKER INSPECT ---
DB_CONFIG = {
    "user": "root",        # Usamos root para tener permisos totales de escritura
    "pass": "root1234",    # Contraseña verificada en el contenedor
    "host": "172.20.0.2",   # IP local para conectar desde el host al contenedor
    "port": "3306",
    "db": "example"
}

# Conexión usando SQLAlchemy y PyMySQL
engine = create_engine(f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['pass']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['db']}")

def ejecutar_proceso():
    archivo_csv = 'datos_electricidad_bueno.csv'
    
    # --- PARTE 2 DE LA PRÁCTICA: GENERACIÓN MASIVA (x100) ---
    # Esto generará el volumen necesario para estresar los nodos de Hadoop
    REGISTROS_ADICIONALES = 5000000 

    print("--- INICIANDO PASO 4: Carga y Generación Masiva ---")

    try:
        # 1. Cargar datos del CSV original
        df = pd.read_csv(archivo_csv)

        # 2. Insertar datos reales
        # Cambiamos el nombre a 'electric_data' para que Sqoop lo encuentre fácil
        print(f"1/3 Insertando registros reales en la tabla 'electric_data'...")
        df.to_sql('electric_data', con=engine, if_exists='replace', index=False, chunksize=20000)

        # 3. Generación sintética para alcanzar los 7M de registros
        print(f"2/3 Generando {REGISTROS_ADICIONALES} registros adicionales (estrés del sistema)...")
        
        nuevos_datos = {
            'fecha': np.random.choice(df['fecha'], REGISTROS_ADICIONALES),
            'consumo': np.random.uniform(df['consumo'].min(), df['consumo'].max(), REGISTROS_ADICIONALES),
            'generacion': np.random.uniform(df['generacion'].min(), df['generacion'].max(), REGISTROS_ADICIONALES),
            'hora_dia': np.random.choice(df['hora_dia'], REGISTROS_ADICIONALES),
            'idexcel': np.random.choice(df['idexcel'], REGISTROS_ADICIONALES),
            'Poblacion': np.random.choice(df['Poblacion'], REGISTROS_ADICIONALES)
        }

        df_extra = pd.DataFrame(nuevos_datos)

        # 4. Volcado masivo (Append suma a lo que ya hay)
        print(f"3/3 Volcando datos adicionales a MySQL. Por favor, espera...")
        df_extra.to_sql('electric_data', con=engine, if_exists='append', index=False, chunksize=20000)

        print("\n✅ ¡CARGA MASIVA COMPLETADA CON ÉXITO!")
        print(f"Total de registros listos para migrar con Sqoop: {len(df) + REGISTROS_ADICIONALES}")

    except Exception as e:
        print(f"\n❌ ERROR DE CONEXIÓN:")
        print(f"No se pudo conectar a MySQL. Asegúrate de que el contenedor 'mysql-practica2' esté corriendo.")
        print(f"Detalle técnico: {e}")

if __name__ == "__main__":
    ejecutar_proceso()
