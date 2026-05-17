# GCP Runtime Context

Este documento resume el contexto operativo observado durante la puesta a punto del pipeline. No guarda secretos; solo identifica los recursos y su papel dentro de la arquitectura actual.

## Proyecto GCP

- `beaming-prism-413004`

## Fuente relacional

- Cloud SQL instance: `mi-postgres-db`
- Region: `us-central1`
- Database observada: `deluxe_analyze`

## CDC

- Servicio: Datastream
- El flujo operativo escribe CDC en GCS
- Bucket de trabajo observado: `gs://beaming-prism-413004-datastream-cdc`
- Prefijo usado en el stream: `datastream/streaming/deluxe-neo4j-cdc`

## Mensajeria

La arquitectura conceptual contempla Pub/Sub. En la implementacion observada, Spark consume desde GCS. Tambien existe notificacion de eventos sobre el bucket, pero no es la ruta principal del procesamiento actual.

## Procesamiento streaming

- Servicio: Dataproc
- Cluster observado: `deluxe-stream-cluster`
- Region: `us-central1`
- Entrypoint local organizado: [`deploy/spark_main.py`](C:/Users/djtor/OneDrive/Documentos/GitHub/DidierParody/deluxe-analyze/deploy/spark_main.py)

## Destino de grafo

- Servicio: Neo4j autogestionado en GCP
- Modo observado: despliegue sobre VM con Docker

## Notas operativas relevantes

- El job de Spark necesita acceso al datasource Avro en submit.
- El paquete Python de proyeccion vive de forma mantenible en [`deluxe_neo4j_cdc/`](C:/Users/djtor/OneDrive/Documentos/GitHub/DidierParody/deluxe-analyze/deluxe_neo4j_cdc).
- El snapshot de `Temp` quedo preservado en [`archive/deluxe_streaming_temp_snapshot/`](C:/Users/djtor/OneDrive/Documentos/GitHub/DidierParody/deluxe-analyze/archive/deluxe_streaming_temp_snapshot).

## Uso recomendado de este documento

Usalo como hoja de referencia cuando tengas que:

- reconstruir el mapa de infraestructura
- recordar que componente lee desde GCS y no desde Pub/Sub
- ubicar la separacion entre codigo fuente activo y snapshot temporal archivado
