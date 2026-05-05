#!/bin/bash
echo ">>> Esperando HDFS..."
until hdfs dfsadmin -fs hdfs://Nodo-principal2:9000 -report > /dev/null 2>&1; do
  sleep 10
done

echo ">>> Saliendo de Safe Mode..."
hdfs dfsadmin -fs hdfs://Nodo-principal2:9000 -safemode leave

echo ">>> Esperando MySQL..."
until nc -z mysql-practica2 3306 > /dev/null 2>&1; do
  echo "MySQL no listo, esperando..."
  sleep 10
done

echo ">>> MySQL listo!"
sleep 5

if hdfs dfs -fs hdfs://Nodo-principal2:9000 -test -e /user/root/electric_data_sqoop/_SUCCESS 2>/dev/null; then
  echo ">>> Datos ya en HDFS, saltando Sqoop."
  exit 0
fi

echo ">>> Lanzando Sqoop import..."

sqoop import \
  -Dmapreduce.framework.name=yarn \
  -Dyarn.app.mapreduce.am.staging-dir=hdfs://Nodo-principal2:9000/tmp/hadoop-staging \
  -Dmapreduce.jobhistory.intermediate-done-dir=hdfs://Nodo-principal2:9000/tmp/mr-history/tmp \
  -Dmapreduce.jobhistory.done-dir=hdfs://Nodo-principal2:9000/tmp/mr-history/done \
  --connect jdbc:mysql://mysql-practica2:3306/example \
  --username alumne \
  --password alumne1234 \
  --table electric_data \
  --target-dir hdfs://Nodo-principal2:9000/user/root/electric_data_sqoop \
  --delete-target-dir \
  --num-mappers 1
echo ">>> Sqoop completado!"
