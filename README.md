# deluxe-analyze

Análisis de comunidades sobre los datos generados por [deluxe-v2](https://github.com/DidierParody/deluxe-v2) — un sistema agéntico de reservas de discoteca en AWS.

Pipeline CDC moderno: PostgreSQL RDS → DMS → S3 → Pub/Sub → Dataproc Serverless (PySpark) → Neo4j + GDS.

## Arquitectura

```
deluxe-v2 (AWS)                           GCP — deluxe-analyze
─────────────────                         ──────────────────────────────────────
RDS Postgres 16
  │  logical replication
  ▼
AWS DMS (ongoing)
  │  Parquet a S3
  ▼
S3 bucket (deluxe-v2-cdc-out)
  │  s3:ObjectCreated
  ▼
Lambda s3-to-pubsub ──── HTTPS ──────►  Pub/Sub topic: cdc-events
                                               │
                                    Cloud Scheduler (*/15 min)
                                               │
                                    Cloud Run Job (dispatcher)
                                          │  pull msgs
                                          ▼
                                 Dataproc Serverless Batch
                                 (PySpark + Neo4j Connector)
                                          │  MERGE via Bolt
                                          ▼
                                 Compute Engine VM
                                 Neo4j 5.x + GDS Community
                                 IP estática — acceso desde
                                 Colab / Jupyter
```

## Estructura del monorepo

```
deluxe-analyze/
├── infra/              # Terraform — toda la infra GCP
│   ├── network/        # VPC, subnets, Cloud NAT, firewall
│   ├── iam/            # Service accounts, WIF para GitHub Actions
│   ├── compute/        # Neo4j VM + IP estática + startup.sh
│   ├── pubsub/         # Topic cdc-events + DLQ
│   ├── storage/        # GCS buckets (etl-artifacts, seed, watermark)
│   ├── secrets/        # Secret Manager (neo4j-password, AWS HMAC keys)
│   ├── scheduler/      # Cloud Scheduler cada 15 min
│   ├── cloud_run/      # Cloud Run Job dispatcher
│   ├── dataproc/       # Dataproc Serverless template (docs-as-code)
│   └── monitoring/     # Alertas Cloud Run + Pub/Sub backlog
├── etl/                # PySpark ETL package (deluxe-etl)
│   ├── etl/
│   │   ├── normalize/  # Schema canónico csv: / v2: + from_csv + from_v2
│   │   ├── sources/    # csv_source (GCS) + s3_cdc_source (Parquet)
│   │   ├── derive/     # CONOCE_A via Cypher
│   │   ├── load/       # Neo4jWriter (Spark Connector)
│   │   └── state/      # Watermark GCS (at-least-once checkpoint)
│   ├── jobs/main.py    # Entry point Dataproc Serverless
│   └── tests/          # pytest con PySpark local
├── dispatcher/         # Cloud Run Job — drena Pub/Sub → lanza Dataproc
├── aws/                # Config AWS (DMS, Lambda, IAM) — setup manual
├── notebooks-client/   # Notebook Colab/Jupyter para análisis Neo4j + GDS
├── data/               # Seed: CSVs sintéticos con variables latentes
├── sketch_pipelines/   # Notebooks académicos de referencia (NO modificar)
├── .github/workflows/  # CI (ruff+pytest), infra (tf plan/apply), deploy
└── Makefile            # tf-plan, etl-test, etl-lint, upload-etl
```

## Quick start

### 1. Bootstrap GCP (una sola vez)

```bash
# Autenticarse
gcloud auth application-default login

# Crear bucket de Terraform state (manual, antes del primer init)
gcloud storage buckets create gs://deluxe-analyze-tfstate \
  --location=us-central1

# Configurar variables
cd infra/
cp terraform.tfvars.example terraform.tfvars
# Editar: project_id, allowed_neo4j_ips (tu IP + IPs de Colab)
```

### 2. Aplicar infraestructura

```bash
terraform init
terraform plan
terraform apply

# Outputs importantes:
terraform output neo4j_static_ip    # IP para notebooks
terraform output wif_provider_name  # Para GitHub Secrets
```

### 3. Configurar GitHub Secrets

En **Settings → Secrets → Actions** del repo, añadir:

| Secret | Valor |
|---|---|
| `WIF_PROVIDER` | Output de `terraform output wif_provider_name` |
| `WIF_SERVICE_ACCOUNT` | `github-actions-sa@<project_id>.iam.gserviceaccount.com` |
| `GCP_PROJECT` | ID del proyecto GCP |
| `ETL_ARTIFACTS_BUCKET` | `<project_id>-etl-artifacts` |

### 4. Seed inicial (CSVs sintéticos)

```bash
# Subir CSVs a GCS
gsutil -m cp data/*.csv gs://<project_id>-seed/

# Subir job PySpark
make upload-etl GCS_BUCKET=<project_id>-etl-artifacts

# Ejecutar ingest CSV manual (una vez)
gcloud run jobs execute dispatcher \
  --region=us-central1 \
  --args="--mode,csv"
```

### 5. Conectar desde Colab / Jupyter

Ver `notebooks-client/connect_neo4j.ipynb`. Tu IP debe estar en `allowed_neo4j_ips` del `terraform.tfvars`.

Para IPs rotativas de Colab, usar **IAP tunnel**:
```bash
gcloud compute start-iap-tunnel neo4j-vm 7687 \
  --local-host-port=localhost:7687 \
  --zone=us-central1-a
# Luego conectar a bolt://localhost:7687 desde notebook local
```

## Desarrollo local

```bash
# Lint ETL
make etl-lint

# Tests unitarios (requiere Java 17)
make etl-test

# Terraform plan
make tf-plan
```

## Schema canónico del grafo

**Nodos**: `Usuario`, `Evento`, `Mesa`, `Segmento`
**Relaciones**: `ASISTIO_A`, `RESERVO`, `PERTENECE_A`, `CONOCE_A`

Los IDs usan namespacing para evitar colisiones entre datos sintéticos y reales:
- `csv:<id>` — datos sintéticos de `data/`
- `v2:<id>` — datos reales de deluxe-v2 via CDC

## Counts esperados (seed sintético)

| Entidad | Count |
|---|---|
| Usuario | 360 |
| Evento | 24 |
| Mesa | 24 |
| Segmento | 4 |
| ASISTIO_A | 2 097 |
| RESERVO | 196 |
| CONOCE_A | 83 398 |

## Notebooks de referencia

- `sketch_pipelines/graph_analysis_query_playbook.ipynb` — queries de análisis de comunidades (Louvain, degree centrality)
- `sketch_pipelines/ingest.ipynb` — lógica ETL original (fuente de verdad, no modificar)
- `notebooks-client/connect_neo4j.ipynb` — conexión desde Colab + demo GDS
