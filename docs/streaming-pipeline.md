# Streaming Pipeline

## Flujo actual

La implementacion operativa hoy sigue este recorrido:

1. `Cloud SQL PostgreSQL`
2. `Datastream CDC`
3. `Google Cloud Storage`
4. `Dataproc / Spark Structured Streaming`
5. `Neo4j`
6. `Analytics / Grafana`

Aunque el diseno conceptual contempla Pub/Sub, el flujo efectivo hoy usa almacenamiento CDC en GCS como origen de lectura para Spark.

## Componentes versionados localmente

- [`deluxe_neo4j_cdc/cdc.py`](C:/Users/djtor/OneDrive/Documentos/GitHub/DidierParody/deluxe-analyze/deluxe_neo4j_cdc/cdc.py)
  Define tablas requeridas y reduccion de eventos CDC a estado corriente.

- [`deluxe_neo4j_cdc/projection.py`](C:/Users/djtor/OneDrive/Documentos/GitHub/DidierParody/deluxe-analyze/deluxe_neo4j_cdc/projection.py)
  Construye los nodos y relaciones que se materializan en Neo4j.

- [`deluxe_neo4j_cdc/neo4j_sync.py`](C:/Users/djtor/OneDrive/Documentos/GitHub/DidierParody/deluxe-analyze/deluxe_neo4j_cdc/neo4j_sync.py)
  Contiene la logica de escritura HTTP hacia Neo4j.

- [`deploy/spark_main.py`](C:/Users/djtor/OneDrive/Documentos/GitHub/DidierParody/deluxe-analyze/deploy/spark_main.py)
  Entrypoint del job de Spark.

## Proyeccion de dominio actual

La proyeccion local esta preparada para construir:

- nodos `Usuario`
- nodos `Evento`
- nodos `Mesa`
- relaciones `COMPRO_TICKET_PARA`
- relaciones `ASISTIO_A`
- relaciones `RESERVO`
- relaciones `CONOCE_A`
- nodos y relaciones de segmentacion cuando existan

## Decisiones que quedaron incorporadas

- Los campos faltantes o latentes ausentes se normalizan a `null` antes de serializar payloads.
- La importacion de `Neo4jProjector` quedo opcional en el paquete para no romper el runtime de Spark si la dependencia `neo4j` no esta instalada alli.
- El job local de Spark contempla `spark-avro` como paquete externo para lectura de CDC en Avro.
- La sincronizacion incremental evita barridos destructivos tipo snapshot en cada microbatch.

## Que problema resolvio esta iteracion

El pipeline estaba fallando despues de detectar archivos CDC y antes de persistir correctamente en Neo4j. Los ajustes locales dejaron controlados los puntos mas fragiles:

- serializacion de `NaN`
- dependencia ausente de `neo4j`
- lectura Avro en Spark
- trazabilidad de errores por microbatch

## Estado de referencia

El directorio `archive/deluxe_streaming_temp_snapshot/` conserva el material temporal desde el cual se recupero y ordeno parte del trabajo operativo. La fuente editable recomendada, sin embargo, es el codigo que ya vive en el arbol principal del repo.
