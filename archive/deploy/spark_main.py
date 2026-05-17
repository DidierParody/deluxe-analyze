import base64
import json
import os
import traceback
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import BinaryType, LongType, StringType, StructField, StructType, TimestampType

from deluxe_neo4j_cdc.cdc import TABLE_SPECS
from deluxe_neo4j_cdc.projection import ProjectionBundle, build_projection_bundle


def _parse_lsn(value: Any) -> int:
    if value is None:
        return -1
    text = str(value).strip()
    if not text or "/" not in text:
        return -1
    high, low = text.split("/", 1)
    try:
        return (int(high, 16) << 32) + int(low, 16)
    except ValueError:
        return -1


def _to_epoch_millis(value: Any) -> int:
    if value is None:
        return -1
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return int(value.timestamp() * 1000)
    if isinstance(value, date):
        return int(datetime(value.year, value.month, value.day, tzinfo=timezone.utc).timestamp() * 1000)
    if isinstance(value, (int, float)):
        return int(value)
    text = str(value).strip()
    if not text:
        return -1
    try:
        return int(text)
    except ValueError:
        pass
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return int(parsed.timestamp() * 1000)
    except ValueError:
        return -1


def _to_iso(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return value


def _jsonable(value: Any) -> Any:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except TypeError:
        pass
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if hasattr(value, "item"):
        return _jsonable(value.item())
    return str(value)


def _normalize_records(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [_jsonable(row) for row in rows]


def _chunked(rows: list[dict[str, Any]], size: int) -> list[list[dict[str, Any]]]:
    return [rows[index : index + size] for index in range(0, len(rows), size)]


def _bolt_to_http(uri: str) -> str:
    cleaned = uri.strip()
    if cleaned.startswith("bolt://"):
        return "http://" + cleaned[len("bolt://") :].rsplit(":", 1)[0] + ":7474"
    if cleaned.startswith("neo4j://"):
        return "http://" + cleaned[len("neo4j://") :].rsplit(":", 1)[0] + ":7474"
    if cleaned.startswith("http://") or cleaned.startswith("https://"):
        return cleaned
    raise ValueError(f"Unsupported Neo4j URI: {uri}")


class HttpNeo4jProjector:
    SCHEMA_QUERIES = (
        "CREATE CONSTRAINT usuario_user_id_unique IF NOT EXISTS FOR (u:Usuario) REQUIRE u.user_id IS UNIQUE",
        "CREATE CONSTRAINT evento_event_id_unique IF NOT EXISTS FOR (e:Evento) REQUIRE e.event_id IS UNIQUE",
        "CREATE CONSTRAINT mesa_table_id_unique IF NOT EXISTS FOR (m:Mesa) REQUIRE m.table_id IS UNIQUE",
        "CREATE CONSTRAINT segmento_name_unique IF NOT EXISTS FOR (s:Segmento) REQUIRE s.name IS UNIQUE",
        "CREATE INDEX usuario_telegram_idx IF NOT EXISTS FOR (u:Usuario) ON (u.telegram_id)",
        "CREATE INDEX evento_event_date_idx IF NOT EXISTS FOR (e:Evento) ON (e.event_date)",
    )

    USER_UPSERT = """
    UNWIND $rows AS row
    MERGE (u:Usuario {user_id: toInteger(row.user_id)})
    SET u.telegram_id = CASE WHEN row.telegram_id IS NULL THEN NULL ELSE toInteger(row.telegram_id) END,
        u.username = row.username,
        u.social_role = row.social_role,
        u.social_group_id = row.social_group_id,
        u.secondary_group_id = row.secondary_group_id,
        u.attendance_level = row.attendance_level,
        u.vip_affinity = CASE WHEN row.vip_affinity IS NULL THEN NULL ELSE toFloat(row.vip_affinity) END,
        u.invite_power = CASE WHEN row.invite_power IS NULL THEN NULL ELSE toFloat(row.invite_power) END,
        u.table_preference = row.table_preference,
        u.rfm_seed_segment = row.rfm_seed_segment,
        u.newcomer_affinity = CASE WHEN row.newcomer_affinity IS NULL THEN NULL ELSE toFloat(row.newcomer_affinity) END,
        u.mixing_score = CASE WHEN row.mixing_score IS NULL THEN NULL ELSE toFloat(row.mixing_score) END,
        u.source_deleted = coalesce(row.source_deleted, false)
    """

    EVENT_UPSERT = """
    UNWIND $rows AS row
    MERGE (e:Evento {event_id: toInteger(row.event_id)})
    SET e.name = row.name,
        e.event_type = row.event_type,
        e.expected_demand_level = row.expected_demand_level,
        e.vip_pull = CASE WHEN row.vip_pull IS NULL THEN NULL ELSE toFloat(row.vip_pull) END,
        e.event_date = CASE WHEN row.event_date IS NULL THEN NULL ELSE date(toString(row.event_date)) END,
        e.start_time = CASE WHEN row.start_time IS NULL THEN NULL ELSE localdatetime(toString(row.start_time)) END,
        e.end_time = CASE WHEN row.end_time IS NULL THEN NULL ELSE localdatetime(toString(row.end_time)) END,
        e.event_state_id = CASE WHEN row.event_state_id IS NULL THEN NULL ELSE toInteger(row.event_state_id) END,
        e.source_deleted = coalesce(row.source_deleted, false)
    """

    TABLE_UPSERT = """
    UNWIND $rows AS row
    MERGE (m:Mesa {table_id: toInteger(row.table_id)})
    SET m.number = CASE WHEN row.number IS NULL THEN NULL ELSE toInteger(row.number) END,
        m.table_type = row.table_type,
        m.capacity = CASE WHEN row.capacity IS NULL THEN NULL ELSE toInteger(row.capacity) END,
        m.vip_suitability = CASE WHEN row.vip_suitability IS NULL THEN NULL ELSE toFloat(row.vip_suitability) END,
        m.source_deleted = coalesce(row.source_deleted, false)
    """

    SEGMENT_UPSERT = """
    UNWIND $rows AS row
    MERGE (s:Segmento {name: row.name})
    SET s.projection_run_id = $run_id
    """

    SEGMENT_SWEEP = """
    MATCH (s:Segmento)
    WHERE coalesce(s.projection_run_id, '') <> $run_id
    DETACH DELETE s
    """

    BELONGS_UPSERT = """
    UNWIND $rows AS row
    MATCH (u:Usuario {user_id: toInteger(row.user_id)})
    MATCH (s:Segmento {name: row.segment_name})
    MERGE (u)-[r:PERTENECE_A]->(s)
    SET r.projection_run_id = $run_id
    """

    BELONGS_SWEEP = """
    MATCH (:Usuario)-[r:PERTENECE_A]->(:Segmento)
    WHERE coalesce(r.projection_run_id, '') <> $run_id
    DELETE r
    """

    PURCHASE_UPSERT = """
    UNWIND $rows AS row
    MATCH (u:Usuario {user_id: toInteger(row.user_id)})
    MATCH (e:Evento {event_id: toInteger(row.event_id)})
    MERGE (u)-[r:COMPRO_TICKET_PARA {ticket_id: toInteger(row.ticket_id)}]->(e)
    SET r.type_ticket_id = CASE WHEN row.type_ticket_id IS NULL THEN NULL ELSE toInteger(row.type_ticket_id) END,
        r.ticket_tier = row.ticket_tier,
        r.order_id = CASE WHEN row.order_id IS NULL THEN NULL ELSE toInteger(row.order_id) END,
        r.approved_at = CASE WHEN row.approved_at IS NULL THEN NULL ELSE localdatetime(toString(row.approved_at)) END,
        r.price_paid = CASE WHEN row.price_paid IS NULL THEN NULL ELSE toFloat(row.price_paid) END,
        r.ticket_state_id = CASE WHEN row.ticket_state_id IS NULL THEN NULL ELSE toInteger(row.ticket_state_id) END,
        r.projection_run_id = $run_id
    """

    PURCHASE_SWEEP = """
    MATCH (:Usuario)-[r:COMPRO_TICKET_PARA]->(:Evento)
    WHERE coalesce(r.projection_run_id, '') <> $run_id
    DELETE r
    """

    ATTENDANCE_UPSERT = """
    UNWIND $rows AS row
    MATCH (u:Usuario {user_id: toInteger(row.user_id)})
    MATCH (e:Evento {event_id: toInteger(row.event_id)})
    MERGE (u)-[r:ASISTIO_A {ticket_id: toInteger(row.ticket_id)}]->(e)
    SET r.type_ticket_id = CASE WHEN row.type_ticket_id IS NULL THEN NULL ELSE toInteger(row.type_ticket_id) END,
        r.used_at = CASE WHEN row.used_at IS NULL THEN NULL ELSE localdatetime(toString(row.used_at)) END,
        r.projection_run_id = $run_id
    """

    ATTENDANCE_SWEEP = """
    MATCH (:Usuario)-[r:ASISTIO_A]->(:Evento)
    WHERE coalesce(r.projection_run_id, '') <> $run_id
    DELETE r
    """

    RESERVATION_UPSERT = """
    UNWIND $rows AS row
    MATCH (u:Usuario {user_id: toInteger(row.user_id)})
    MATCH (m:Mesa {table_id: toInteger(row.table_id)})
    MERGE (u)-[r:RESERVO {reservation_id: toInteger(row.reservation_id)}]->(m)
    SET r.event_id = CASE WHEN row.event_id IS NULL THEN NULL ELSE toInteger(row.event_id) END,
        r.table_price = CASE WHEN row.table_price IS NULL THEN NULL ELSE toFloat(row.table_price) END,
        r.reservation_state_id = CASE WHEN row.reservation_state_id IS NULL THEN NULL ELSE toInteger(row.reservation_state_id) END,
        r.reserved_at = CASE WHEN row.reserved_at IS NULL THEN NULL ELSE localdatetime(toString(row.reserved_at)) END,
        r.expires_at = CASE WHEN row.expires_at IS NULL THEN NULL ELSE localdatetime(toString(row.expires_at)) END,
        r.projection_run_id = $run_id
    """

    RESERVATION_SWEEP = """
    MATCH (:Usuario)-[r:RESERVO]->(:Mesa)
    WHERE coalesce(r.projection_run_id, '') <> $run_id
    DELETE r
    """

    SOCIAL_UPSERT = """
    UNWIND $rows AS row
    MATCH (u1:Usuario {user_id: toInteger(row.user_1_id)})
    MATCH (u2:Usuario {user_id: toInteger(row.user_2_id)})
    MERGE (u1)-[r:CONOCE_A]-(u2)
    SET r.shared_attendances = CASE WHEN row.shared_attendances IS NULL THEN 0 ELSE toFloat(row.shared_attendances) END,
        r.shared_purchases = CASE WHEN row.shared_purchases IS NULL THEN 0 ELSE toFloat(row.shared_purchases) END,
        r.shared_reservations = CASE WHEN row.shared_reservations IS NULL THEN 0 ELSE toFloat(row.shared_reservations) END,
        r.tie_strength = CASE WHEN row.tie_strength IS NULL THEN 0 ELSE toFloat(row.tie_strength) END,
        r.first_shared_event = CASE WHEN row.first_shared_event IS NULL THEN NULL ELSE datetime(toString(row.first_shared_event)) END,
        r.last_shared_event = CASE WHEN row.last_shared_event IS NULL THEN NULL ELSE datetime(toString(row.last_shared_event)) END,
        r.projection_run_id = $run_id
    """

    SOCIAL_SWEEP = """
    MATCH (:Usuario)-[r:CONOCE_A]-(:Usuario)
    WHERE coalesce(r.projection_run_id, '') <> $run_id
    DELETE r
    """

    def __init__(self, uri: str, username: str, password: str, database: str, batch_size: int = 500) -> None:
        self.endpoint = f"{_bolt_to_http(uri).rstrip('/')}/db/{database}/tx/commit"
        token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("utf-8")
        self.headers = {
            "Authorization": f"Basic {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        self.batch_size = batch_size

    def _run(self, query: str, parameters: dict[str, Any] | None = None) -> None:
        payload = {
            "statements": [
                {
                    "statement": query,
                    "parameters": _jsonable(parameters or {}),
                }
            ]
        }
        request = urllib.request.Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers=self.headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            message = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Neo4j HTTP error {exc.code}: {message}") from exc
        errors = body.get("errors", [])
        if errors:
            raise RuntimeError(f"Neo4j query failed: {errors}")

    def ensure_schema(self) -> None:
        for query in self.SCHEMA_QUERIES:
            self._run(query)

    def _write_rows(self, query: str, rows: list[dict[str, Any]], run_id: str | None = None) -> None:
        if not rows:
            return
        normalized = _normalize_records(rows)
        for chunk in _chunked(normalized, self.batch_size):
            parameters: dict[str, Any] = {"rows": chunk}
            if run_id is not None:
                parameters["run_id"] = run_id
            self._run(query, parameters)

    def _sync_full_snapshot(self, upsert_query: str, sweep_query: str, rows: list[dict[str, Any]], run_id: str) -> None:
        # This job consumes incremental CDC files, not authoritative full snapshots.
        # Running a sweep on partial state after restarts or table-specific batches can
        # delete valid graph relationships that were simply absent from the current batch.
        self._write_rows(upsert_query, rows, run_id)

    def apply_projection(self, bundle: ProjectionBundle, run_id: str) -> None:
        payloads = bundle.as_records()

        self._write_rows(self.USER_UPSERT, payloads["user_node_current"])
        self._write_rows(self.EVENT_UPSERT, payloads["event_node_current"])
        self._write_rows(self.TABLE_UPSERT, payloads["table_node_current"])

        self._sync_full_snapshot(self.PURCHASE_UPSERT, self.PURCHASE_SWEEP, payloads["ticket_purchase_edge_current"], run_id)
        self._sync_full_snapshot(self.ATTENDANCE_UPSERT, self.ATTENDANCE_SWEEP, payloads["attendance_edge_current"], run_id)
        self._sync_full_snapshot(self.RESERVATION_UPSERT, self.RESERVATION_SWEEP, payloads["reservation_edge_current"], run_id)
        self._sync_full_snapshot(self.SOCIAL_UPSERT, self.SOCIAL_SWEEP, payloads["social_tie_edge_current"], run_id)

        if payloads.get("segment_node_current") and payloads.get("belongs_edge_current"):
            self._sync_full_snapshot(self.SEGMENT_UPSERT, self.SEGMENT_SWEEP, payloads["segment_node_current"], run_id)
            self._sync_full_snapshot(self.BELONGS_UPSERT, self.BELONGS_SWEEP, payloads["belongs_edge_current"], run_id)


CURRENT_STATE: dict[str, dict[tuple[Any, ...], dict[str, Any]]] = defaultdict(dict)
SEEN_EVENT_IDS: set[str] = set()
PROJECTOR = HttpNeo4jProjector(
    uri=os.environ["NEO4J_URI"],
    username=os.environ["NEO4J_USERNAME"],
    password=os.environ["NEO4J_PASSWORD"],
    database=os.getenv("NEO4J_DATABASE", "neo4j"),
)
PROJECTOR.ensure_schema()


def _primary_keys_for_table(table_name: str, source_metadata: dict[str, Any]) -> list[str]:
    source_keys = source_metadata.get("primary_keys") or []
    if source_keys:
        return [str(key) for key in source_keys]
    table_spec = TABLE_SPECS.get(table_name)
    if table_spec:
        return list(table_spec.primary_key)
    raise ValueError(f"No primary key metadata for table {table_name}")


def _record_sort_key(event_id: str, source_metadata: dict[str, Any], row_dict: dict[str, Any]) -> tuple[int, int, int, str]:
    return (
        _to_epoch_millis(row_dict.get("source_timestamp")),
        _parse_lsn(source_metadata.get("lsn")),
        _to_epoch_millis(row_dict.get("read_timestamp")),
        event_id,
    )


def _ingest_row(row_dict: dict[str, Any]) -> None:
    event_id = str(row_dict.get("uuid") or "")
    if event_id and event_id in SEEN_EVENT_IDS:
        return
    if event_id:
        SEEN_EVENT_IDS.add(event_id)

    source_metadata = row_dict.get("source_metadata") or {}
    schema_name = source_metadata.get("schema")
    table_name = source_metadata.get("table")
    if not schema_name or not table_name:
        return

    canonical_table = f"{schema_name}.{table_name}"
    payload = dict(row_dict.get("payload") or {})
    primary_keys = _primary_keys_for_table(canonical_table, source_metadata)
    pk_tuple = tuple(payload.get(column) for column in primary_keys)
    if any(value is None for value in pk_tuple):
        raise ValueError(f"Missing primary key values for table {canonical_table}: {primary_keys}")

    record = dict(payload)
    record["source_deleted"] = bool(source_metadata.get("is_deleted", False))
    record["_op"] = source_metadata.get("change_type")
    record["_source_ts"] = _to_iso(row_dict.get("source_timestamp"))
    sort_key = _record_sort_key(event_id, source_metadata, row_dict)

    current = CURRENT_STATE[canonical_table].get(pk_tuple)
    if current is None or sort_key >= current["_sort_key"]:
        record["_sort_key"] = sort_key
        CURRENT_STATE[canonical_table][pk_tuple] = record


def _build_frames() -> dict[str, pd.DataFrame]:
    frames: dict[str, pd.DataFrame] = {}
    for table_name, keyed_rows in CURRENT_STATE.items():
        rows = []
        for row in keyed_rows.values():
            cleaned = {key: value for key, value in row.items() if key != "_sort_key"}
            rows.append(cleaned)
        frames[table_name] = pd.DataFrame(rows)
    return frames


def _project_current_state(batch_id: int) -> None:
    current_frames = _build_frames()
    bundle = build_projection_bundle(current_frames)
    run_id = f"spark-batch-{batch_id}"
    PROJECTOR.apply_projection(bundle, run_id=run_id)
    counts = {
        "users": len(bundle.user_node_current.index),
        "events": len(bundle.event_node_current.index),
        "tables": len(bundle.table_node_current.index),
        "purchase_edges": len(bundle.ticket_purchase_edge_current.index),
        "attendance_edges": len(bundle.attendance_edge_current.index),
        "reservation_edges": len(bundle.reservation_edge_current.index),
        "social_edges": len(bundle.social_tie_edge_current.index),
    }
    print(json.dumps({"batch_id": batch_id, "projection_counts": counts}, sort_keys=True))


def process_microbatch(batch_df, batch_id: int) -> None:
    try:
        if batch_df.rdd.isEmpty():
            print(json.dumps({"batch_id": batch_id, "status": "empty_batch"}))
            return

        paths = [row["path"] for row in batch_df.select("path").distinct().collect()]
        if not paths:
            print(json.dumps({"batch_id": batch_id, "status": "no_paths"}))
            return

        avro_df = batch_df.sparkSession.read.format("avro").load(paths).withColumn("source_file", F.input_file_name())
        batch_count = avro_df.count()
        print(json.dumps({"batch_id": batch_id, "status": "processing", "files": len(paths), "rows": batch_count}))
        for row in avro_df.toLocalIterator():
            _ingest_row(row.asDict(recursive=True))
        _project_current_state(batch_id)
    except Exception:
        print(
            json.dumps(
                {
                    "batch_id": batch_id,
                    "status": "error",
                    "error": traceback.format_exc(),
                }
            )
        )
        raise


def main() -> None:
    builder = SparkSession.builder.appName("deluxe-neo4j-streaming")
    avro_package = os.getenv("SPARK_AVRO_PACKAGE", "org.apache.spark:spark-avro_2.12:3.5.3")
    if avro_package:
        builder = builder.config("spark.jars.packages", avro_package)
    spark = builder.getOrCreate()
    spark.sparkContext.setLogLevel("WARN")

    bucket_root = os.environ["STREAM_BUCKET_ROOT"].rstrip("/")
    source_prefix = os.environ["STREAM_SOURCE_PREFIX"].strip("/")
    checkpoint_location = os.environ["CHECKPOINT_LOCATION"]
    trigger_interval = os.getenv("TRIGGER_INTERVAL", "15 minutes")
    max_files_per_trigger = os.getenv("MAX_FILES_PER_TRIGGER", "200")
    binary_file_schema = StructType(
        [
            StructField("path", StringType(), True),
            StructField("modificationTime", TimestampType(), True),
            StructField("length", LongType(), True),
            StructField("content", BinaryType(), True),
        ]
    )

    stream_df = (
        spark.readStream.format("binaryFile")
        .schema(binary_file_schema)
        .option("recursiveFileLookup", "true")
        .option("pathGlobFilter", "*.avro")
        .option("maxFilesPerTrigger", max_files_per_trigger)
        .load(bucket_root)
        .where(F.col("path").contains(source_prefix))
        .select("path")
    )

    query = (
        stream_df.writeStream.foreachBatch(process_microbatch)
        .option("checkpointLocation", checkpoint_location)
        .trigger(processingTime=trigger_interval)
        .start()
    )
    query.awaitTermination()


if __name__ == "__main__":
    main()
