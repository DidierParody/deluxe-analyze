# Dataproc Streaming Runbook

## Proposito

Este documento resume como pensar el job streaming localmente, que artefactos intervienen y como validar el recorrido completo desde Cloud SQL hasta Neo4j.

## Artefactos principales

- [`deploy/spark_main.py`](C:/Users/djtor/OneDrive/Documentos/GitHub/DidierParody/deluxe-analyze/deploy/spark_main.py)
- [`deluxe_neo4j_cdc/`](C:/Users/djtor/OneDrive/Documentos/GitHub/DidierParody/deluxe-analyze/deluxe_neo4j_cdc)
- [`archive/deluxe_streaming_temp_snapshot/`](C:/Users/djtor/OneDrive/Documentos/GitHub/DidierParody/deluxe-analyze/archive/deluxe_streaming_temp_snapshot)

## Variables de entorno esperadas por el job

- `CHECKPOINT_LOCATION`
- `STREAM_BUCKET_ROOT`
- `STREAM_SOURCE_PREFIX`
- `NEO4J_URI`
- `NEO4J_DATABASE`
- `NEO4J_USERNAME`
- `NEO4J_PASSWORD`

## Consideraciones de ejecucion

- El job procesa CDC desde GCS usando Avro.
- Si el submit no agrega `spark-avro`, Spark no puede leer el origen.
- En modo incremental, no conviene ejecutar limpieza destructiva del grafo por lote.

## Validacion funcional minima

### 1. Insertar un usuario de smoke test en SQL

```sql
WITH seed AS (
    SELECT COALESCE(MAX(id), 0) + 1 AS next_id
    FROM core.users
),
resolved_customer_type AS (
    SELECT id
    FROM catalog.type_users
    WHERE LOWER(name) = 'customer'
    LIMIT 1
)
INSERT INTO core.users (
    id,
    username,
    type_user_id,
    email,
    phone_number,
    telegram_id
)
SELECT
    s.next_id,
    'cdc_smoke_' || s.next_id,
    r.id,
    'cdc_smoke_' || s.next_id || '@example.com',
    '3010' || LPAD(s.next_id::text, 6, '0'),
    9100000000 + s.next_id
FROM seed s
CROSS JOIN resolved_customer_type r
RETURNING id, username, telegram_id, created_at;
```

### 2. Consultar en Neo4j

```cypher
MATCH (u:Usuario)
WHERE u.username STARTS WITH 'cdc_smoke_'
RETURN
  u.user_id,
  u.username,
  u.telegram_id,
  properties(u)
ORDER BY u.user_id DESC
LIMIT 5;
```

## Expectativa de latencia

Si el job corre por microbatches o ventanas operativas cercanas a 15 minutos, no debes asumir aparicion inmediata del registro en Neo4j. Un resultado ausente en los primeros minutos no implica por si solo una falla del pipeline.

## Trazabilidad sugerida

Cuando un cambio no aparece donde esperas, sigue este orden:

1. confirmar el `INSERT` en Cloud SQL
2. confirmar el archivo CDC en GCS
3. confirmar que Spark haya leido el batch
4. confirmar que el batch no termino en error
5. confirmar la presencia final del nodo o relacion en Neo4j

## Nota sobre variables latentes

Los atributos latentes usados para generacion sintetica no tienen que existir obligatoriamente en los nuevos registros productivos. La proyeccion esta preparada para tolerar su ausencia y serializar esos campos como `null` cuando no esten presentes.
