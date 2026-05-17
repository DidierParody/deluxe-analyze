# Deluxe Analyze Workspace Guide

Este documento organiza lo desarrollado sin modificar el contenido existente del proyecto. La idea es dejar una vista clara de que piezas son fuente activa, cuales son notebooks de trabajo y que artefactos quedaron preservados como snapshot operativo.

## Estructura activa

- `deluxe_neo4j_cdc/`
  Paquete fuente del pipeline de proyeccion desde CDC hacia Neo4j. Aqui viven la reduccion de CDC, la construccion del `ProjectionBundle` y la sincronizacion con Neo4j.

- `deploy/spark_main.py`
  Entrypoint versionado del job de Dataproc/Spark Structured Streaming. Esta es la copia de trabajo que debe tratarse como referencia local del job desplegable.

- `tests/`
  Pruebas unitarias del paquete Python, enfocadas hoy en la proyeccion.

- `sketch_pipelines/`
  Notebooks y material exploratorio para ingesta, analisis y playbooks de consulta de grafo.

## Activos de apoyo

- `users.csv`
- `events.csv`
- `dico_tables.csv`
- `type_tickets.csv`
- `diagram-export-4-5-2026-13_49_16.png`

Estos archivos quedan en su ubicacion actual porque hacen parte del contexto de trabajo del proyecto y no requieren reorganizacion adicional para conservar trazabilidad.

## Snapshot archivado del trabajo temporal

- `archive/deluxe_streaming_temp_snapshot/`

Este directorio preserva de forma explicita el contenido util que estaba en `C:\Users\djtor\AppData\Local\Temp\deluxe_streaming`:

- `main.py`
- `deluxe_neo4j_cdc.zip`
- `package_src/deluxe_neo4j_cdc/`

Se omitieron artefactos generados como `__pycache__` para mantener el repo limpio. El objetivo del snapshot es conservar el estado operativo y su procedencia, no arrastrar cache de ejecucion.

## Regla de lectura rapida

- Si vas a editar la logica del pipeline, entra primero a `deluxe_neo4j_cdc/` y `deploy/spark_main.py`.
- Si necesitas contexto analitico o consultas, revisa `sketch_pipelines/`.
- Si necesitas reconstruir como estaba el entorno temporal de despliegue, usa `archive/deluxe_streaming_temp_snapshot/`.

## Nota sobre archivos locales sensibles

- `.env` existe en el workspace como configuracion local.

Debe seguir tratandose como configuracion de entorno local y no como documentacion de arquitectura.
