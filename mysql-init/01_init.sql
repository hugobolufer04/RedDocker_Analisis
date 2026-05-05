SET GLOBAL local_infile=1;

CREATE TABLE IF NOT EXISTS electric_data (
  idexcel INT,
  fecha VARCHAR(50),
  hora_dia INT,
  consumo DOUBLE,
  generacion DOUBLE,
  Poblacion VARCHAR(100)
);

LOAD DATA LOCAL INFILE '/tmp/datos_electricidad_bueno.csv'
INTO TABLE electric_data
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 ROWS;
