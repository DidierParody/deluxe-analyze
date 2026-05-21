# deluxe-analyze — Defensa académica (12 slides)

Guión completo: contenido por slide + notas del orador + assets a usar.

Diagramas SVG en `./diagrams/` — listos para subir a Canva como elementos.
Screenshots a usar en `./screenshots/` (genera tú con la app corriendo).

---

## Slide 1 · Portada

**Título:** `deluxe-analyze`
**Subtítulo:** Análisis de redes sociales de clientes nocturnos con grafos
**Tagline:** *De CDC en AWS a insights de venta en tu bolsillo*

**Visual:** logo + nombre del autor + institución + fecha + un grafo decorativo
en verde sobre fondo negro (puedes usar `diagrams/01_cover_graph.svg`).

**Notas del orador (60s):**
> Buenas, presento deluxe-analyze: un sistema de análisis de comunidades
> sociales construido sobre Neo4j en GCP, que consume datos en tiempo casi-real
> de un sistema operacional separado en AWS. La tesis es que para responder
> ciertas preguntas de negocio en hospitality nocturna —quién arrastra a quién,
> qué grupos se mueven juntos, dónde está la palanca de marketing— el modelo
> relacional es estructuralmente insuficiente y un grafo nativo resuelve la
> misma pregunta en una línea de Cypher.

---

## Slide 2 · El ecosistema deluxe

**Layout:** dos columnas, una caja por sistema, una flecha CDC en el medio.

| `deluxe-v2` (operacional, AWS) | `deluxe-analyze` (analítico, GCP) |
|---|---|
| Sistema agéntico de reservas | Análisis de comunidades sobre grafo |
| Postgres RDS (privado) | Neo4j 5.26 + GDS 2.14 |
| Funciones Lambda + DMS | Dataproc Serverless + Cloud Run |
| Lenguaje del dominio: tickets, mesas, eventos, usuarios | Lenguaje del análisis: nodos, relaciones, comunidades |

**Visual:** `diagrams/02_ecosystem.svg`

**Notas del orador (60s):**
> deluxe-v2 es el sistema operacional —reservas, tickets, mesas— corriendo en
> AWS sobre Postgres. deluxe-analyze es su hermano analítico en GCP, sobre
> Neo4j. La separación es deliberada: el sistema operacional optimiza para
> consistencia y baja latencia transaccional; el analítico optimiza para
> consultas exploratorias y algoritmos que recorren caminos largos en el grafo
> social. La pieza no trivial es cómo mantener el segundo sincronizado con el
> primero sin acoplarlos.

---

## Slide 3 · El problema: PostgreSQL no puede responder esto

**Layout:** lista de 4-5 preguntas, cada una con un ícono.

🚀 *"Si lanzo una promoción a Raúl, ¿a cuántos clientes alcanza en su red?"*
👑 *"¿Quién es el cliente más influyente de la discoteca?"*
👥 *"¿Qué clientes siempre se mueven juntos?"*
🌉 *"¿Qué clientes conectan grupos que de otra forma no se mezclarían?"*
🎯 *"¿A qué evento invito a este cliente según lo que asistieron sus amigos?"*

Debajo, una caja:
> En SQL: CTEs recursivos costosos, múltiples JOINs autoreferenciales,
> rendimiento degradado cuadráticamente.
> En Cypher: una línea con expansión `[*1..3]` y algoritmos GDS nativos.

**Notas del orador (90s):**
> Estas son preguntas que el dueño de una discoteca realmente se hace. La
> primera —alcance indirecto de una promoción a través de la red social del
> cliente— en SQL requeriría una CTE recursiva de tres niveles, lenta y
> difícil de mantener. En Cypher es literalmente
> `MATCH (u {id:$id})-[:CONOCE_A*1..3]-(v) RETURN count(DISTINCT v)`.
> Mostraremos resultado real más adelante: para Raúl, alcanza a 339 de 361
> clientes en tres saltos. Estas preguntas no son curiosidades académicas:
> son la base de decisiones de marketing y operación que mueven dinero.

---

## Slide 4 · Arquitectura end-to-end

**Visual:** `diagrams/04_architecture_full.svg` (a página completa).

Diagrama maestro que muestra:

```
[AWS]                                      [GCP]
RDS Postgres                              VPC custom (10.20.0.0/16)
  │ logical replication                   ├─ subnet-data (Dataproc + Cloud Run)
  ▼                                       └─ subnet-graph (Neo4j VM)
DMS Replication Task
  │ full-load + ongoing CDC
  ▼
S3 (Parquet)                              Cloud Scheduler (*/15 min)
  │ ObjectCreated                                │
  ▼                                              ▼
Lambda dispatcher  ─── HTTPS push ──► Pub/Sub `cdc-events` → subscription
                                                │ pull
                                                ▼
                                       Cloud Run Job `dispatcher`
                                                │ submit batch + ACK selectivo
                                                ▼
                                       Dataproc Serverless
                                       ├ lee S3 con HMAC
                                       ├ normaliza al schema canónico
                                       ├ MERGE idempotente
                                       └ Neo4j Spark Connector (Bolt)
                                                │
                                                ▼
                                       Neo4j VM (subnet-graph)
                                                │ Bolt 7687
                                                ▼
                                       FastAPI dashboard-api (Cloud Run)
                                                │ HTTPS + X-API-Key
                                                ▼
                                       Flutter app (Android / Web)
```

**Notas del orador (120s):**
> Recorramos el flujo de un cambio de datos. Un cliente reserva una mesa en
> deluxe-v2; la fila se commitea en Postgres. AWS DMS, que está escuchando el
> log de replicación lógica, escribe un Parquet en S3 con ese cambio.
> S3 dispara una Lambda que publica un mensaje en Pub/Sub de GCP cruzando la
> frontera entre clouds. Cada 15 minutos, Cloud Scheduler dispara nuestro
> Cloud Run Job dispatcher; este drena la subscription, agrupa las URIs S3
> únicas y submitea un batch en Dataproc Serverless. El batch lee desde S3
> usando credenciales HMAC, normaliza al schema canónico que veremos en la
> slide 7, y escribe en Neo4j vía el Spark Connector. La aplicación Flutter
> consume todo esto a través de un backend FastAPI también en Cloud Run.
> El sistema completo es at-least-once: el dispatcher solo ACKea los mensajes
> si el batch terminó con SUCCEEDED.

---

## Slide 5 · Pipeline AWS: CDC → S3 → Lambda → Pub/Sub

**Visual:** `diagrams/05_aws_pipeline.svg`

**Caja izquierda — Componentes:**

| Componente | Tipo | Función |
|---|---|---|
| RDS Postgres | `db.t3.small` | Origen operacional; `rds.logical_replication=1` en parameter group |
| DMS Replication Instance | `dms.t3.micro` | Lector de WAL |
| DMS Task | `full-load + cdc` | Replica `core.users`, `core.events`, `transactions.tickets`... |
| S3 bucket | `deluxe-v2-cdc-out` | Parquet particionado por schema/tabla/fecha |
| Lambda `s3_to_pubsub` | Python 3.11, 128MB | Triggered por `s3:ObjectCreated:*` |
| IAM user `gcp-cdc-reader` | HMAC keys | Lectura S3 desde Dataproc |

**Caja derecha — Pub/Sub:**

| | |
|---|---|
| Topic | `cdc-events` |
| Subscription | `cdc-events-sub` (pull, ack=600s, retention=7d) |
| Dead-letter | `cdc-events-dlq` |
| Mensaje | `data: s3://bucket/key`, `attributes: {table}` |

**Notas del orador (90s):**
> Del lado AWS, el corazón es DMS con replicación lógica. La instancia DMS lee
> el WAL de Postgres y, por cada cambio en las tablas que nos importan, escribe
> un Parquet a un bucket S3. Ese bucket tiene un trigger Lambda que, por cada
> objeto nuevo, construye un mensaje y lo publica en Pub/Sub de GCP cruzando la
> frontera entre nubes con Workload Identity Federation, sin claves estáticas.
> La autenticación cruzada cloud sin keys de larga vida es uno de los detalles
> de seguridad más relevantes del diseño. El bucket S3 tiene dos consumidores:
> Lambda para notificar, y Dataproc para leer los Parquet usando HMAC keys
> almacenadas en Secret Manager de GCP.

---

## Slide 6 · Pipeline GCP: Scheduler → Dispatcher → Dataproc → Neo4j

**Visual:** `diagrams/06_gcp_pipeline.svg`

**Tabla de recursos:**

| Recurso | Tipo | Detalle |
|---|---|---|
| Cloud Scheduler | `dispatcher-trigger` | Cron `*/15 * * * *`, OAuth token, llama Cloud Run Admin API v2 |
| Cloud Run Job | `dispatcher` | Python 3.11, drena Pub/Sub, lanza batches, ACK selectivo |
| Dataproc Cluster | `deluxe-etl-cluster` | `n1-standard-2`, master single-node, `idle_delete_ttl=1h` |
| GCS bucket | `etl-artifacts` | PySpark jobs + dependencies zip |
| GCS bucket | `watermark` | Defensa contra duplicados si ACK falla |
| Neo4j VM | `neo4j-vm` | `e2-medium`, disco pd-balanced 50GB, IP estática, snapshot diario |
| Service Accounts | 4 SAs | mínimo privilegio: dataproc-etl, dispatcher, neo4j-vm, dashboard-api |

**Decisión técnica destacada:**
> El dispatcher es un **Cloud Run Job** (no Service) porque su lifecycle es
> corto y batch — pull de Pub/Sub, submit a Dataproc, espera resultado, exit.
> Sin embargo, fue tricky de configurar: Cloud Scheduler debe usar
> `oauth_token` (no `oidc_token`) y la URI debe apuntar a la **v2 global** del
> Cloud Run Admin API (`run.googleapis.com/v2/.../jobs/:run`), no la v1
> regional que solo cubre Services. Documenté esto porque me costó tres
> iteraciones.

**Notas del orador (120s):**
> Del lado GCP el patrón es event-driven con micro-batch. Cada 15 minutos el
> Scheduler dispara el dispatcher, que es un Cloud Run Job ligero. El
> dispatcher hace pull de hasta 1000 mensajes, deduplica URIs, y submitea un
> batch a Dataproc Serverless. La parte crítica es la garantía at-least-once:
> los mensajes se ACKean solo si Dataproc termina con SUCCEEDED. Si falla, se
> hace NACK explícito reduciendo el deadline a cero, y eventualmente
> terminan en la dead-letter queue después de varios reintentos.
> Dataproc corre PySpark contra subnet-data, donde reside Neo4j —por eso
> ambos están en la misma VPC custom. El cluster usa `idle_delete_ttl=1h`
> para evitar costos cuando no hay carga; el dispatcher tiene un
> `ensure_cluster_exists()` que detecta el cluster faltante o en ERROR y lo
> recrea automáticamente.

---

## Slide 7 · Schema canónico Neo4j

**Visual:** `diagrams/07_neo4j_schema.svg` — diagrama del grafo.

**Nodos:**

| Label | PK | Origen | Propiedades clave |
|---|---|---|---|
| `Usuario` | `id` (`csv:N` o `v2:N`) | dos fuentes con namespace | username, telegram_id, vip_affinity, social_role, invite_power |
| `Evento` | `id` | dos fuentes | name, event_date, event_type, vip_pull |
| `Mesa` | `id` | dos fuentes | table_number, is_vip, capacity |
| `Segmento` | `name` (única) | derivada | description |

**Relaciones:**

| Tipo | De | A | Propiedades |
|---|---|---|---|
| `ASISTIO_A` | Usuario | Evento | ticket_tier |
| `RESERVO` | Usuario | Mesa | event_id |
| `PERTENECE_A` | Usuario | Segmento | — |
| `CONOCE_A` | Usuario | Usuario | tie_strength, shared_events, shared_vip_events, shared_reservations, first_shared_event, last_shared_event |

**Decisión clave — namespacing:** los IDs llevan prefijo `csv:` (datos
sintéticos seed) o `v2:` (CDC real) para que ambos coexistan sin colisión.

**Derivación de CONOCE_A:** se calcula en Spark a partir de co-asistencias
+ VIP compartido + reservas compartidas, con `tie_strength` ponderado.

**Notas del orador (90s):**
> El schema canónico es el contrato del grafo. Cuatro tipos de nodo y cuatro
> tipos de relación, con namespacing en los IDs porque tenemos dos fuentes:
> CSV sintéticos para seed inicial, y CDC real desde deluxe-v2. Sin el
> namespace habría colisiones cuando ambos lleguen al mismo grafo.
> La relación más interesante es `CONOCE_A`: no viene de los datos
> directamente, la inferimos. Si dos usuarios asistieron al mismo evento, se
> conocen con tie_strength bajo. Si compartieron evento VIP o reserva de mesa,
> tie_strength alto. Esto es lo que permite los algoritmos de comunidad: la
> red social no la declara nadie, emerge del comportamiento observado.

---

## Slide 8 · ETL PySpark + GDS

**Visual:** `diagrams/08_etl_flow.svg`

**Fases del job PySpark (`etl/jobs/main.py`):**

```
1. Read sources
   ├─ spark.read.csv(GCS seed)      # one-shot
   └─ spark.read.parquet(S3 a HMAC) # CDC incremental
2. Normalize → canonical schema
   ├─ from_csv.normalize_csv()      # prefijo csv:
   └─ from_v2.normalize_v2()        # prefijo v2:
3. Merge (deduplicar por id)
4. Derive CONOCE_A
   └─ co-attendance + shared VIP + shared reservations
5. Load Neo4j (Neo4j Spark Connector, MERGE idempotente)
6. Trigger GDS projection refresh
```

**Algoritmos GDS aplicados:**

| Algoritmo | Endpoint | Output |
|---|---|---|
| **PageRank** ponderado por tie_strength | `/influencers` | top influyentes |
| **Louvain** | `/communities` | comunidades naturales |
| **Betweenness centrality** | `/brokers` | brokers que conectan clusters |
| **K-hop expansion** | `/promo-reach/{id}` | alcance indirecto |
| **Collaborative filtering** simple | `/event-recommendations/{id}` | qué evento invitar |

**Notas del orador (90s):**
> El ETL es PySpark sobre Dataproc Serverless. La normalización resuelve las
> diferencias de schema entre CSV y CDC al modelo canónico. La derivación de
> CONOCE_A se hace en Spark con joins sobre ASISTIO_A — es la operación más
> cara, pero solo se recalcula para los usuarios tocados en el batch, no
> sobre toda la red. Los algoritmos GDS corren después en Neo4j, sobre una
> proyección in-memory llamada `socialGraph` que el backend mantiene viva.
> Para el grafo actual de 361 usuarios y 41.699 aristas, Louvain tarda 23s
> y PageRank 1s. Para escalar a 50.000 usuarios habría que pasar a GDS
> Enterprise por las primitivas paralelas.

---

## Slide 9 · Dashboard Flutter + FastAPI

**Visual:** `diagrams/09_dashboard_arch.svg` + screenshot del home en `screenshots/`

**Arquitectura:**

```
[Flutter app Android/Web] ─HTTPS+X-API-Key─► [FastAPI Cloud Run] ─Bolt─► [Neo4j VM]
```

**Backend (`dashboard/backend/`):**
- FastAPI + Pydantic v2 + uvicorn
- 6 endpoints: `/health`, `/users`, `/promo-reach/{id}`, `/influencers`,
  `/event-recommendations/{id}`, `/communities`, `/brokers`
- Auth: `X-API-Key` (Secret Manager, rotable)
- Cache in-memory TTL 5min sobre queries GDS (Louvain 25s → 0.3s)
- 9 tests unitarios con Neo4j mockeado, ruff clean

**Frontend (`dashboard/frontend/`):**
- Flutter 3.x mobile-first; web build para testing
- 6 pantallas + 11 widgets reutilizables
- go_router, dio con interceptor X-API-Key, Material 3, Inter via Google Fonts
- APK release: 48MB

**Selección estadística de gráficos:**

| Pregunta | Gráfico | Justificación |
|---|---|---|
| Alcance promoción | KPI + Funnel | Few 2006: insight de un vistazo; funnel > sunburst en móvil |
| Más influyentes | Bar horizontal | Cleveland-McGill 1984: posición es encoding más preciso |
| Evento recomendado | Ranked cards | Tufte small multiples: cards mejor que bars para múltiples atributos |
| Comunidades | Treemap | Shneiderman 1991: óptimo con >6 categorías de tamaño variable |
| Brokers | Lollipop | Diferenciación visual de bar chart, énfasis en valor discreto |

**Notas del orador (90s):**
> El dashboard tiene tres capas: app Flutter, backend FastAPI, Neo4j. El
> backend es el contrato: encapsula las queries Cypher y expone JSON. La
> decisión de no llamar Neo4j directo desde Flutter fue por seguridad
> —no expone credenciales— y por cacheabilidad. El cache TTL de 5 minutos
> baja Louvain de 25s a 0.3s en la segunda llamada.
> La selección de gráficos no es decorativa: cada uno responde a literatura
> estadística específica. Por ejemplo, Cleveland y McGill mostraron en 1984
> que la posición en una escala común es el encoding perceptual más preciso,
> por eso barras horizontales para rankings. Para comunidades, treemap porque
> Shneiderman demostró que con más de seis categorías de tamaños desiguales,
> los pie charts se vuelven ilegibles.

---

## Slide 10 · Infraestructura: Terraform + CI/CD + WIF

**Visual:** `diagrams/10_infra.svg`

**Todo es código** (`infra/`):

```
infra/
├ apis.tf            # enable required GCP APIs
├ network.tf         # VPC, subnets, Cloud NAT, Cloud Router
├ firewall.tf        # rules por tag/source-range, IP whitelist Neo4j
├ iam.tf             # 6 SAs + bindings mínimo privilegio + WIF
├ secrets.tf         # 5 secrets en Secret Manager
├ storage.tf         # 3 buckets (etl-artifacts, watermark, seed)
├ pubsub.tf          # topic + subscription + DLQ
├ compute.tf         # Neo4j VM + IP estática + startup.sh
├ dataproc.tf        # cluster spec
├ cloudrun.tf        # Cloud Run Job dispatcher
├ dashboard_api.tf   # Cloud Run Service dashboard-api + Direct VPC egress
├ scheduler.tf       # Cloud Scheduler */15min con OAuth Cloud Run Admin v2
└ monitoring.tf      # alerts
```

**Workload Identity Federation:**
- GitHub Actions se autentica contra GCP sin keys JSON
- Pool: `github-actions-pool`
- Provider OIDC: `token.actions.githubusercontent.com`
- Condición: `assertion.repository == 'DidierParody/deluxe-analyze'`

**CI/CD (`.github/workflows/`):**

| Workflow | Trigger | Acción |
|---|---|---|
| `ci.yml` | PR + push a main/dev | ruff + pytest (etl, dispatcher, dashboard backend) |
| `infra.yml` | tocas `infra/**` | terraform plan en PR, apply en merge |
| `deploy-etl.yml` | tocas `etl/**` | sube `main.py` a GCS |
| `deploy-dispatcher.yml` | tocas `dispatcher/**` | build + push Artifact Registry, update Cloud Run Job |
| `deploy-dashboard-backend.yml` | tocas `dashboard/backend/**` | build + push, update Cloud Run Service |

**Detalle de seguridad:** ningún SA descargable, ningún token de larga vida,
todo vía short-lived OIDC tokens o ADC.

**Notas del orador (120s):**
> Toda la infraestructura está en Terraform —14 archivos `.tf` que describen
> 30+ recursos GCP. No hay clicks manuales en la consola: si un recurso no
> está en el state, no existe. Esto permite reproducibilidad —si mañana
> tengo que migrar a otro proyecto GCP, `terraform apply` lo recrea.
> La autenticación CI usa Workload Identity Federation: GitHub Actions
> pide un OIDC token al endpoint federado de Google, que verifica que el
> token venga de mi repo específico, y devuelve credenciales temporales para
> la SA `github-actions-sa`. Cero claves JSON en GitHub Secrets. Cinco
> workflows automatizan todos los deploys.

---

## Slide 11 · Resultados (datos reales)

**Layout:** dashboard de métricas en grilla 2x4.

**Grafo Neo4j actual:**

| Métrica | Valor |
|---|---|
| Usuarios | 361 |
| Eventos | 35 |
| Mesas | 59 |
| Relaciones CONOCE_A | 41.699 |
| Relaciones ASISTIO_A | 2.097 |
| Constraints únicas | 4 |

**Performance del backend (Cloud Run, cache caliente):**

| Endpoint | Latencia p50 |
|---|---|
| `/influencers` | 1.0s |
| `/promo-reach/{id}` | 0.3s |
| `/communities` | 0.3s (cache) / 25s (cold) |
| `/brokers` | 0.3s |

**Insights de negocio descubiertos:**

| Pregunta | Hallazgo |
|---|---|
| ¿Más influyente? | Florencia (PageRank 2.38) |
| ¿Alcance promoción a Raúl? | **339 / 361 clientes = 94% de la base** |
| ¿Cuántas comunidades? | 5 dominantes (98, 73, 65, 60, 44 miembros) + 27 nichos |
| ¿Top broker? | csv:250 (betweenness 341) |
| ¿Evento recomendado para Raúl? | Noche Deluxe 6 — 129 de sus amigos asistieron |

**Deploy en producción:**

| Recurso | Estado |
|---|---|
| Backend `dashboard-api` | ✅ deployed Cloud Run `dashboard-api-67093133884.us-central1.run.app` |
| Frontend APK | ✅ 48 MB, instalable en Android |
| Pipeline CDC | ✅ Cloud Scheduler corriendo cada 15 min |
| Neo4j | ✅ 5.26 Community + GDS 2.14 en VM e2-medium |

**Notas del orador (90s):**
> Estos números son reales del sistema corriendo ahora mismo. El grafo tiene
> 361 usuarios y 42.000 aristas inferidas. El backend responde la mayoría de
> endpoints en menos de un segundo gracias al cache TTL.
> El hallazgo más impactante de negocio: si invitamos a Raúl con una
> promoción, llegamos a 339 personas en tres saltos sociales — el 94 por
> ciento de toda la base de clientes. Eso es lo que ningún sistema relacional
> podía decirnos antes en una sola query.
> Todo está en producción: backend, dashboard Android instalable, pipeline
> CDC ejecutándose cada quince minutos.

---

## Slide 12 · Conclusiones + trabajo futuro

**Layout:** dos columnas.

**Conclusiones:**

1. La separación operacional/analítico vía CDC permite que ambos sistemas
   evolucionen sin acoplarse — ya cambiamos el schema de tickets en deluxe-v2
   sin tocar deluxe-analyze.
2. Neo4j + GDS no es alternativo a PostgreSQL, es complementario: cada uno
   resuelve preguntas que el otro no puede.
3. La selección de tipo de gráfico tiene base estadística, no estética.
4. Infraestructura 100% en Terraform + CI/CD con WIF demuestra que
   "proyecto académico" no excusa malas prácticas de producción.

**Trabajo futuro:**

| Línea | Detalle |
|---|---|
| Escalar grafo | Pasar a GDS Enterprise para Louvain paralelo cuando >5K usuarios |
| Recálculo incremental de CONOCE_A | Solo aristas de usuarios tocados en el batch (ya parcialmente) |
| Embeddings de nodos | Node2Vec sobre CONOCE_A para recomendación más fina |
| ML en el dashboard | Predicción de churn por features grafo + RFM |
| Auth real en dashboard | Reemplazar X-API-Key por Firebase Auth para multi-usuario |
| Histórico temporal | Versionar las comunidades para detectar evolución de grupos |

**Notas del orador (60s):**
> Cerrando: deluxe-analyze prueba tres tesis. Primero, que un sistema
> académico puede tener disciplina de producción: IaC, CI/CD federado,
> tests, observabilidad. Segundo, que la elección de tecnología debe
> seguir a la pregunta —elegimos Neo4j no por moda sino porque las
> preguntas que pide el negocio son intrínsecamente de grafo. Tercero, que
> la traducción de un insight algorítmico complejo a una interfaz que
> alguien de ventas pueda usar en su teléfono requiere decisiones tan
> rigurosas como el algoritmo mismo.
> Gracias.

---

# Cómo usar este documento

1. Cada `## Slide N` corresponde a una diapositiva.
2. Los visuales `diagrams/NN_*.svg` se suben a Canva como elementos (importar
   archivo → arrastrar al lienzo).
3. Las **notas del orador** van pegadas al campo "speaker notes" de cada
   slide de Canva (View → Show notes).
4. Las tablas se pueden recrear visualmente en Canva o pegar como imagen
   exportada de Markdown rendering.
5. Los **screenshots** de la app puedes generarlos abriendo el APK en tu
   teléfono y haciendo capturas — guárdalos en `docs/presentation/screenshots/`.

**Sugerencia de diseño en Canva:**
- Plantilla: "Pitch Deck — Dark Mode" o "Tech Startup"
- Paleta: Emerald 500 `#10b981`, Black `#050605`, Gray `#9ca3af`
- Tipografía: Inter (Headings 700, Body 400)
- Acento: gradiente `#10b981 → #047857` para CTAs y métricas destacadas
