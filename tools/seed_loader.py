#!/usr/bin/env python3
"""Standalone seed loader — no Spark / Dataproc required.

Reads the four seed CSVs from GCS and loads them into Neo4j using the
Python neo4j driver.  Designed to run from any environment that has
`google-cloud-storage` and `neo4j` installed and valid GCP credentials.

Usage:
    pip install google-cloud-storage neo4j
    python tools/seed_loader.py \
        --neo4j-uri bolt://34.28.39.13:7687 \
        --neo4j-password changeme123 \
        --seed-bucket gs://engaged-stage-463123-e0-seed
"""

import argparse
import csv
import io
import logging
import sys
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger(__name__)

PREFIX = "csv"
BATCH_SIZE = 200

# ---------------------------------------------------------------------------
# Canonical schema — mirrors etl/etl/normalize/canonical.py
# ---------------------------------------------------------------------------

SCHEMA_QUERIES = [
    "CREATE CONSTRAINT usuario_id_unique IF NOT EXISTS FOR (u:Usuario) REQUIRE u.id IS UNIQUE",
    "CREATE CONSTRAINT evento_id_unique IF NOT EXISTS FOR (e:Evento) REQUIRE e.id IS UNIQUE",
    "CREATE CONSTRAINT mesa_id_unique IF NOT EXISTS FOR (m:Mesa) REQUIRE m.id IS UNIQUE",
    "CREATE INDEX usuario_telegram_idx IF NOT EXISTS FOR (u:Usuario) ON (u.telegram_id)",
    "CREATE INDEX evento_date_idx IF NOT EXISTS FOR (e:Evento) ON (e.event_date)",
]

CONOCE_A_CYPHER = """
MATCH (u1:Usuario)-[a1:ASISTIO_A]->(e:Evento)<-[a2:ASISTIO_A]-(u2:Usuario)
WHERE u1.id < u2.id
WITH u1, u2, count(e) AS shared_events,
     sum(CASE WHEN a1.ticket_tier = 'vip' AND a2.ticket_tier = 'vip' THEN 1 ELSE 0 END) AS shared_vip_events,
     min(e.event_date) AS first_shared_event, max(e.event_date) AS last_shared_event
OPTIONAL MATCH (u1)-[r1:RESERVO]->(:Mesa), (u2)-[r2:RESERVO]->(:Mesa)
WHERE r1.event_id = r2.event_id AND u1.id < u2.id
WITH u1, u2, shared_events, shared_vip_events, first_shared_event, last_shared_event,
     count(r1) AS shared_reservations
WHERE shared_events >= 1
MERGE (u1)-[r:CONOCE_A]-(u2)
SET r.shared_events = shared_events,
    r.shared_vip_events = shared_vip_events,
    r.shared_reservations = shared_reservations,
    r.first_shared_event = first_shared_event,
    r.last_shared_event = last_shared_event,
    r.tie_strength = round(toFloat(shared_events) + toFloat(shared_vip_events) * 0.5
                           + toFloat(shared_reservations) * 0.75, 3)
"""


# ---------------------------------------------------------------------------
# GCS helpers
# ---------------------------------------------------------------------------

def _read_gcs_csv(bucket_name: str, blob_name: str) -> list[dict[str, str]]:
    from google.cloud import storage  # type: ignore
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    content = blob.download_as_text(encoding="utf-8")
    reader = csv.DictReader(io.StringIO(content))
    return [dict(row) for row in reader]


def _parse_gcs_uri(uri: str) -> tuple[str, str]:
    """gs://bucket/prefix  →  (bucket, prefix)"""
    without_scheme = uri.removeprefix("gs://")
    bucket, _, prefix = without_scheme.partition("/")
    return bucket, prefix


# ---------------------------------------------------------------------------
# Row normalisation — mirrors etl/etl/normalize/from_csv.py
# ---------------------------------------------------------------------------

def _ns(raw_id: str) -> str:
    return f"{PREFIX}:{raw_id}"


def _to_float(v: str) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _to_int(v: str) -> int | None:
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def normalise_usuario(row: dict[str, str]) -> dict[str, Any]:
    raw_id = row["id"].strip()
    return {
        "id": _ns(raw_id),
        "telegram_id": row.get("telegram_id", "").strip() or None,
        "username": row.get("username", "").strip() or None,
        "social_role": row.get("social_role", "").strip() or None,
        "social_group_id": row.get("social_group_id", "").strip() or None,
        "secondary_group_id": row.get("secondary_group_id", "").strip() or None,
        "attendance_level": row.get("attendance_level", "").strip() or None,
        "vip_affinity": _to_float(row.get("vip_affinity", "")),
        "invite_power": _to_float(row.get("invite_power", "")),
        "table_preference": row.get("table_preference", "").strip() or None,
        "rfm_seed_segment": row.get("rfm_seed_segment", "").strip() or None,
        "newcomer_affinity": _to_float(row.get("newcomer_affinity", "")),
        "mixing_score": _to_float(row.get("mixing_score", "")),
        "source": PREFIX,
    }


def normalise_evento(row: dict[str, str]) -> dict[str, Any]:
    raw_id = row["id"].strip()
    event_date = row.get("event_date", "").strip() or None
    bucket = row.get("start_hour_bucket", "").strip()
    start_time = (
        f"{event_date}T{bucket.zfill(2)}:00:00" if event_date and bucket else None
    )
    return {
        "id": _ns(raw_id),
        "name": row.get("name", "").strip() or None,
        "event_type": row.get("event_type", "").strip() or None,
        "expected_demand_level": row.get("expected_demand_level", "").strip() or None,
        "vip_pull": _to_float(row.get("vip_pull", "")),
        "event_date": event_date,
        "start_time": start_time,
        "end_time": None,
        "event_state_id": _to_int(row.get("event_state", "")),
        "source": PREFIX,
    }


def normalise_mesa(row: dict[str, str]) -> dict[str, Any]:
    raw_id = row["id"].strip()
    vip_suit = _to_float(row.get("vip_suitability", ""))
    is_vip = (vip_suit > 0.5) if vip_suit is not None else False
    return {
        "id": _ns(raw_id),
        "table_number": _to_int(row.get("number", "")),
        "capacity": _to_int(row.get("capacity", "")),
        "is_vip": is_vip,
        "event_id": None,
        "source": PREFIX,
    }


def normalise_asistio_a(row: dict[str, str]) -> dict[str, Any] | None:
    """Works with attendance_seed.csv (user_id, event_id, ticket_tier) or tickets.csv."""
    uid = row.get("user_id", "").strip()
    eid = row.get("event_id", "").strip()
    if not uid or not eid:
        return None
    return {
        "user_id": _ns(uid),
        "event_id": _ns(eid),
        "ticket_tier": row.get("ticket_tier", "").strip() or None,
        "source": PREFIX,
    }


def normalise_reservo(row: dict[str, str]) -> dict[str, Any] | None:
    uid = row.get("user_id", "").strip()
    tid = row.get("table_id", "").strip()
    eid = row.get("event_id", "").strip()
    if not uid or not tid:
        return None
    return {
        "user_id": _ns(uid),
        "table_id": _ns(tid),
        "event_id": _ns(eid) if eid else None,
        "source": PREFIX,
    }


# ---------------------------------------------------------------------------
# Neo4j helpers
# ---------------------------------------------------------------------------

def _batch(lst: list, n: int):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def merge_nodes(session, label: str, rows: list[dict], key: str = "id") -> int:
    count = 0
    for chunk in _batch(rows, BATCH_SIZE):
        session.run(
            f"UNWIND $rows AS r MERGE (n:{label} {{{key}: r.{key}}}) SET n += r",
            rows=chunk,
        )
        count += len(chunk)
    return count


def merge_asistio_a(session, rows: list[dict]) -> int:
    count = 0
    for chunk in _batch(rows, BATCH_SIZE):
        session.run(
            """
            UNWIND $rows AS r
            MATCH (u:Usuario {id: r.user_id})
            MATCH (e:Evento  {id: r.event_id})
            MERGE (u)-[rel:ASISTIO_A]->(e)
            SET rel.ticket_tier = r.ticket_tier,
                rel.source      = r.source
            """,
            rows=chunk,
        )
        count += len(chunk)
    return count


def merge_reservo(session, rows: list[dict]) -> int:
    count = 0
    for chunk in _batch(rows, BATCH_SIZE):
        session.run(
            """
            UNWIND $rows AS r
            MATCH (u:Usuario {id: r.user_id})
            MATCH (m:Mesa    {id: r.table_id})
            MERGE (u)-[rel:RESERVO]->(m)
            SET rel.event_id = r.event_id,
                rel.source   = r.source
            """,
            rows=chunk,
        )
        count += len(chunk)
    return count


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Load CSV seed data into Neo4j")
    parser.add_argument("--neo4j-uri", required=True, help="Bolt URI, e.g. bolt://34.28.39.13:7687")
    parser.add_argument("--neo4j-user", default="neo4j")
    parser.add_argument("--neo4j-password", required=True)
    parser.add_argument("--neo4j-database", default="neo4j")
    parser.add_argument("--seed-bucket", required=True, help="GCS URI, e.g. gs://my-bucket/prefix")
    args = parser.parse_args()

    bucket_name, prefix = _parse_gcs_uri(args.seed_bucket)
    prefix = prefix.rstrip("/")

    def gcs(filename: str) -> list[dict]:
        blob = f"{prefix}/{filename}" if prefix else filename
        log.info("Reading gs://%s/%s …", bucket_name, blob)
        return _read_gcs_csv(bucket_name, blob)

    from neo4j import GraphDatabase  # type: ignore
    driver = GraphDatabase.driver(
        args.neo4j_uri,
        auth=(args.neo4j_user, args.neo4j_password),
    )

    with driver.session(database=args.neo4j_database) as session:
        log.info("Setting up schema constraints and indexes …")
        for q in SCHEMA_QUERIES:
            session.run(q)

        # ── Usuarios ─────────────────────────────────────────────────────────
        usuarios = [normalise_usuario(r) for r in gcs("users.csv")]
        n = merge_nodes(session, "Usuario", usuarios)
        log.info("Merged %d Usuario nodes", n)

        # ── Eventos ───────────────────────────────────────────────────────────
        eventos = [normalise_evento(r) for r in gcs("events.csv")]
        n = merge_nodes(session, "Evento", eventos)
        log.info("Merged %d Evento nodes", n)

        # ── Mesas (optional) ─────────────────────────────────────────────────
        try:
            mesas = [normalise_mesa(r) for r in gcs("dico_tables.csv")]
            n = merge_nodes(session, "Mesa", mesas)
            log.info("Merged %d Mesa nodes", n)
        except Exception as exc:
            log.warning("dico_tables.csv not found, skipping Mesas: %s", exc)

        # ── ASISTIO_A (optional — attendance_seed.csv or tickets.csv) ─────────
        for fname in ("attendance_seed.csv", "tickets.csv"):
            try:
                rows_raw = gcs(fname)
                rows = [r for r in (normalise_asistio_a(x) for x in rows_raw) if r]
                n = merge_asistio_a(session, rows)
                log.info("Merged %d ASISTIO_A edges from %s", n, fname)
                break
            except Exception as exc:
                log.debug("%s not found: %s", fname, exc)

        # ── RESERVO (optional) ───────────────────────────────────────────────
        try:
            rows_raw = gcs("reservations.csv")
            rows = [r for r in (normalise_reservo(x) for x in rows_raw) if r]
            n = merge_reservo(session, rows)
            log.info("Merged %d RESERVO edges", n)
        except Exception as exc:
            log.debug("reservations.csv not found, skipping: %s", exc)

        # ── CONOCE_A derivation (only if ASISTIO_A edges exist) ───────────────
        has_edges = session.run(
            "MATCH ()-[r:ASISTIO_A]->() RETURN count(r) AS cnt"
        ).single()["cnt"]

        if has_edges > 0:
            log.info("Deriving CONOCE_A edges from %d ASISTIO_A …", has_edges)
            session.execute_write(lambda tx: tx.run(CONOCE_A_CYPHER))
            result = session.run("MATCH ()-[r:CONOCE_A]-() RETURN count(r) AS cnt").single()
            log.info("Created %d CONOCE_A edge-records", result["cnt"])
        else:
            log.info("No ASISTIO_A edges found, skipping CONOCE_A derivation")

    driver.close()
    log.info("Seed load complete.")


if __name__ == "__main__":
    main()
