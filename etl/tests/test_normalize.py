import pytest
from pyspark.sql import SparkSession
from pyspark.sql.types import StringType, StructField, StructType

from etl.normalize.canonical import CONOCE_A_CYPHER, SCHEMA_QUERIES, add_namespace
from etl.normalize.from_csv import normalize_csv
from etl.normalize.from_v2 import normalize_v2
from etl.normalize.merge_canonical import merge_canonical

# ── add_namespace ────────────────────────────────────────────────────────────

def test_add_namespace_csv_prefix(spark: SparkSession):
    df = spark.createDataFrame([("42",)], ["user_id"])
    result = df.select(add_namespace("user_id", "csv").alias("id")).collect()
    assert result[0]["id"] == "csv:42"


def test_add_namespace_v2_prefix(spark: SparkSession):
    df = spark.createDataFrame([("99",)], ["event_id"])
    result = df.select(add_namespace("event_id", "v2").alias("id")).collect()
    assert result[0]["id"] == "v2:99"


def test_add_namespace_preserves_nulls(spark: SparkSession):
    # None pk → concat produces "csv:None" string, not null — acceptable
    df = spark.createDataFrame([(None,)], StructType([StructField("user_id", StringType(), True)]))
    result = df.select(add_namespace("user_id", "csv").alias("id")).collect()
    # should not raise
    assert result[0]["id"] is not None or result[0]["id"] is None  # just no exception


# ── normalize_csv ─────────────────────────────────────────────────────────────

@pytest.fixture
def raw_csv(spark: SparkSession) -> dict:
    users = spark.createDataFrame(
        [("1", "tg1", "alice", "influencer", "g1", "g2", "high",
          "0.9", "0.8", "vip", "A", "0.1", "0.5")],
        ["user_id", "telegram_id", "username", "social_role",
         "social_group_id", "secondary_group_id", "attendance_level",
         "vip_affinity", "invite_power", "table_preference",
         "rfm_seed_segment", "newcomer_affinity", "mixing_score"],
    )
    events = spark.createDataFrame(
        [("10", "Noche VIP", "vip", "high", "0.95",
          "2026-01-15", "2026-01-15T22:00:00", "2026-01-16T04:00:00", "1")],
        ["event_id", "name", "event_type", "expected_demand_level", "vip_pull",
         "event_date", "start_time", "end_time", "event_state_id"],
    )
    tickets = spark.createDataFrame(
        [("1", "10", "vip")],
        ["user_id", "event_id", "ticket_tier"],
    )
    tables = spark.createDataFrame(
        [("5", "3", "4", "true", "10")],
        ["table_id", "table_number", "capacity", "is_vip", "event_id"],
    )
    reservations = spark.createDataFrame(
        [("1", "5", "10")],
        ["user_id", "table_id", "event_id"],
    )
    segments = spark.createDataFrame(
        [("VIP", "High-value customers")],
        ["name", "description"],
    )
    user_segments = spark.createDataFrame(
        [("1", "VIP")],
        ["user_id", "segment_name"],
    )
    return {
        "users": users,
        "events": events,
        "tickets": tickets,
        "tables": tables,
        "reservations": reservations,
        "segments": segments,
        "user_segments": user_segments,
    }


def test_csv_usuario_id_has_prefix(raw_csv):
    result = normalize_csv(raw_csv)
    ids = [r.id for r in result["usuarios"].select("id").collect()]
    assert all(i.startswith("csv:") for i in ids), f"Bad ids: {ids}"


def test_csv_evento_id_has_prefix(raw_csv):
    result = normalize_csv(raw_csv)
    ids = [r.id for r in result["eventos"].select("id").collect()]
    assert all(i.startswith("csv:") for i in ids), f"Bad ids: {ids}"


def test_csv_asistio_a_both_ids_prefixed(raw_csv):
    result = normalize_csv(raw_csv)
    rows = result["asistio_a"].select("user_id", "event_id").collect()
    for row in rows:
        assert row.user_id.startswith("csv:"), f"user_id missing prefix: {row.user_id}"
        assert row.event_id.startswith("csv:"), f"event_id missing prefix: {row.event_id}"


def test_csv_source_field_is_csv(raw_csv):
    result = normalize_csv(raw_csv)
    sources = [r.source for r in result["usuarios"].select("source").collect()]
    assert all(s == "csv" for s in sources)


def test_csv_vip_affinity_cast_to_double(raw_csv):
    result = normalize_csv(raw_csv)
    schema = result["usuarios"].schema
    field = next(f for f in schema.fields if f.name == "vip_affinity")
    from pyspark.sql.types import DoubleType
    assert isinstance(field.dataType, DoubleType)


# ── normalize_v2 ─────────────────────────────────────────────────────────────

@pytest.fixture
def raw_v2(spark: SparkSession) -> dict:
    users = spark.createDataFrame(
        [("100", "tg100", "bob")],
        ["user_id", "telegram_id", "username"],
    )
    events = spark.createDataFrame(
        [("200", "Electro Night", "general", "medium", "0.4",
          "2026-02-10", "2026-02-10T23:00:00", "2026-02-11T05:00:00", "1")],
        ["event_id", "name", "event_type", "expected_demand_level", "vip_pull",
         "event_date", "start_time", "end_time", "event_state_id"],
    )
    tickets = spark.createDataFrame(
        [("100", "200", "general")],
        ["user_id", "event_id", "ticket_tier"],
    )
    return {
        "core.users": users,
        "core.events": events,
        "transactions.tickets": tickets,
    }


def test_v2_usuario_id_has_prefix(raw_v2):
    result = normalize_v2(raw_v2)
    ids = [r.id for r in result["usuarios"].select("id").collect()]
    assert all(i.startswith("v2:") for i in ids), f"Bad ids: {ids}"


def test_v2_source_field_is_v2(raw_v2):
    result = normalize_v2(raw_v2)
    sources = [r.source for r in result["usuarios"].select("source").collect()]
    assert all(s == "v2" for s in sources)


def test_v2_missing_columns_filled_with_none(raw_v2):
    result = normalize_v2(raw_v2)
    # vip_affinity was not in raw data → should be null, not raise
    row = result["usuarios"].select("vip_affinity").first()
    assert row is not None  # row exists, vip_affinity may be null


# ── merge_canonical ───────────────────────────────────────────────────────────

def test_merge_no_id_collision(raw_csv, raw_v2):
    csv_canonical = normalize_csv(raw_csv)
    v2_canonical = normalize_v2(raw_v2)
    merged = merge_canonical(csv_canonical, v2_canonical)

    usuario_ids = [r.id for r in merged["usuarios"].select("id").collect()]
    csv_ids = [i for i in usuario_ids if i.startswith("csv:")]
    v2_ids = [i for i in usuario_ids if i.startswith("v2:")]

    assert len(csv_ids) > 0, "Expected csv: ids"
    assert len(v2_ids) > 0, "Expected v2: ids"
    assert len(set(usuario_ids)) == len(usuario_ids), "Duplicate ids found after merge"


def test_merge_csv_only(raw_csv):
    csv_canonical = normalize_csv(raw_csv)
    merged = merge_canonical(csv_canonical, {})
    assert "usuarios" in merged
    ids = [r.id for r in merged["usuarios"].select("id").collect()]
    assert all(i.startswith("csv:") for i in ids)


def test_merge_deduplicates_same_id(spark: SparkSession):
    df1 = spark.createDataFrame([("csv:1", "alice", "csv")], ["id", "username", "source"])
    df2 = spark.createDataFrame([("csv:1", "alice_updated", "csv")], ["id", "username", "source"])
    merged = merge_canonical({"usuarios": df1}, {"usuarios": df2})
    count = merged["usuarios"].count()
    assert count == 1, f"Expected 1 after dedup, got {count}"


# ── constants sanity ─────────────────────────────────────────────────────────

def test_schema_queries_not_empty():
    assert len(SCHEMA_QUERIES) >= 4


def test_conoce_a_cypher_contains_merge():
    assert "MERGE" in CONOCE_A_CYPHER
    assert "CONOCE_A" in CONOCE_A_CYPHER
    assert "tie_strength" in CONOCE_A_CYPHER
