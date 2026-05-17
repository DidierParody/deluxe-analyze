# Deluxe Streaming Temp Snapshot

Este directorio conserva una copia limpia de los artefactos utiles que estaban en:

`C:\Users\djtor\AppData\Local\Temp\deluxe_streaming`

## Contenido preservado

- `main.py`
- `deluxe_neo4j_cdc.zip`
- `package_src/deluxe_neo4j_cdc/`

## Proposito

Este snapshot sirve como respaldo trazable del estado temporal que se uso durante la puesta a punto del pipeline. No reemplaza la fuente activa del proyecto. La fuente editable recomendada sigue siendo:

- [`deploy/spark_main.py`](C:/Users/djtor/OneDrive/Documentos/GitHub/DidierParody/deluxe-analyze/deploy/spark_main.py)
- [`deluxe_neo4j_cdc/`](C:/Users/djtor/OneDrive/Documentos/GitHub/DidierParody/deluxe-analyze/deluxe_neo4j_cdc)

## Integridad de archivos preservados

- `main.py`
  `SHA256 163D61B7221D572CE62616572C6E61E284FC396949266F685E05E48461CBD367`

- `deluxe_neo4j_cdc.zip`
  `SHA256 3FE551CDC0BBB5485860F1B4D5660D2961BE2C8E32085AEFD4169208353DD9B1`

## Relacion con la copia versionada local

La copia actual en [`deploy/spark_main.py`](C:/Users/djtor/OneDrive/Documentos/GitHub/DidierParody/deluxe-analyze/deploy/spark_main.py) no es identica al `main.py` archivado. Se preservan ambos porque cumplen papeles distintos:

- `archive/.../main.py`
  fotografia del artefacto temporal usado en el entorno de trabajo

- `deploy/spark_main.py`
  version local organizada para mantenimiento y despliegue

## Limpieza intencional

No se copiaron directorios `__pycache__` porque son artefactos generados y no agregan valor de mantenimiento ni trazabilidad funcional.
