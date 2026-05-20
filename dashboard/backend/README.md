# dashboard-api

FastAPI backend for the deluxe-analyze sales dashboard. Exposes Neo4j graph
analytics (PageRank, Louvain, betweenness, k-hop reach) as REST endpoints
guarded by an `X-API-Key` header.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/healthz` | health check (no auth) |
| GET | `/users?limit=` | user list for picker |
| GET | `/promo-reach/{user_id}` | k-hop reach + per-hop breakdown |
| GET | `/influencers?limit=` | top PageRank users |
| GET | `/event-recommendations/{user_id}?limit=` | events scored by friends' attendance |
| GET | `/communities?min_size=` | Louvain communities + niche aggregate |
| GET | `/brokers?limit=` | top betweenness users |

OpenAPI docs at `/docs` when running.

## Local development

```bash
cd dashboard/backend
pip install -e ".[dev]"

# Required env (or put them in .env)
export NEO4J_PASSWORD=<password from `gcloud secrets versions access latest --secret=neo4j-password`>
export DASHBOARD_API_KEY=dev-key-replace-me

uvicorn app.main:app --reload --port 8080
```

Then:
```bash
curl -H "X-API-Key: $DASHBOARD_API_KEY" http://localhost:8080/influencers?limit=5
```

## Tests

```bash
pytest -v
ruff check .
```

Tests mock the Neo4j layer — they don't hit the production database.

## Deploy

Built and deployed via `.github/workflows/deploy-dashboard-backend.yml` to
Cloud Run service `dashboard-api`. See `infra/dashboard_api.tf`.
