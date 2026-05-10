import requests
import time
import subprocess

PROMETHEUS_URL = "http://localhost:9090/api/v1/query"

METRICAS = {
    'node_load1': 'cpu_load',
    'node_memory_MemAvailable_bytes': 'recurso_disponible'
}

def exportar_directo():
    print("Iniciando ingesta directa en Hive (HDFS) - (Ctrl+C para detener)...")
    while True:
        try:
            for query_prom, nombre_metrica in METRICAS.items():
                response = requests.get(PROMETHEUS_URL, params={'query': query_prom})
                results = response.json()['data']['result']
                
                for res in results:
                    ts = time.strftime('%Y-%m-%d %H:%M:%S')
                    nodo = res['metric'].get('instance', 'nodo-desconocido')
                    valor = res['value'][1]
                    
                    sql = f"INSERT INTO TABLE metricas_hadoop VALUES ('{ts}', '{nodo}', '{nombre_metrica}', {valor});"
                    
                    print(f"[{ts}] Insertando {nombre_metrica} en clúster: {nodo} -> {valor}")
                    
                    subprocess.run([
                        "docker", "exec", "hive2", "beeline", 
                        "-u", "jdbc:hive2://localhost:10000", 
                        "-n", "root",
                        "-e", sql
                    ], capture_output=True)

            time.sleep(10)
            
        except KeyboardInterrupt:
            print("\nIngesta detenida por el usuario.")
            break
        except Exception as e:
            print(f"Error en el ciclo: {e}")
            time.sleep(5)

if __name__ == "__main__":
    exportar_directo()