from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import BooleanType, DateType, DoubleType, IntegerType

from etl.normalize.canonical import add_namespace

# ---------------------------------------------------------------------------
# Column mapping notes (actual CSV schema → canonical)
#
# users.csv       : pk = "id" (not "user_id"); has all latent-variable cols
# events.csv      : pk = "id"; start_time/end_time absent; event_state (str)
# dico_tables.csv : pk = "id"; vip_suitability (float) used as is_vip proxy
# type_tickets.csv: ticket-tier catalog — used as asistio_a only when a
#                   dedicated tickets.csv (actual purchases) is available
# ---------------------------------------------------------------------------


def normalize_csv(raw: dict[str, DataFrame], prefix: str = "csv") -> dict[str, DataFrame]:
    # ── Usuarios ─────────────────────────────────────────────────────────────
    # CSV pk column is "id", not "user_id"
    usuarios = (
        raw["users"]
        .withColumnRenamed("id", "user_id")
        .withColumn("id", add_namespace("user_id", prefix))
        .withColumn("vip_affinity", F.col("vip_affinity").cast(DoubleType()))
        .withColumn("invite_power", F.col("invite_power").cast(DoubleType()))
        .withColumn("newcomer_affinity", F.col("newcomer_affinity").cast(DoubleType()))
        .withColumn("mixing_score", F.col("mixing_score").cast(DoubleType()))
        .withColumn("source", F.lit(prefix))
        .select(
            "id", "telegram_id", "username", "social_role", "social_group_id",
            "secondary_group_id", "attendance_level", "vip_affinity", "invite_power",
            "table_preference", "rfm_seed_segment", "newcomer_affinity", "mixing_score",
            "source",
        )
    )

    # ── Eventos ───────────────────────────────────────────────────────────────
    # CSV pk = "id"; no start_time/end_time cols; event_state is a string id
    eventos = (
        raw["events"]
        .withColumnRenamed("id", "event_id")
        .withColumn("id", add_namespace("event_id", prefix))
        .withColumn("vip_pull", F.col("vip_pull").cast(DoubleType()))
        .withColumn("event_date", F.col("event_date").cast(DateType()))
        .withColumn(
            "start_time",
            F.when(
                F.col("start_hour_bucket").isNotNull(),
                F.concat(
                    F.col("event_date"), F.lit("T"),
                    F.col("start_hour_bucket"), F.lit(":00:00"),
                ).cast("timestamp"),
            ).otherwise(F.lit(None).cast("timestamp")),
        )
        .withColumn("end_time", F.lit(None).cast("timestamp"))
        .withColumn(
            "event_state_id",
            F.col("event_state").cast(IntegerType()),
        )
        .withColumn("source", F.lit(prefix))
        .select(
            "id", "name", "event_type", "expected_demand_level", "vip_pull",
            "event_date", "start_time", "end_time", "event_state_id", "source",
        )
    )

    result: dict[str, DataFrame] = {
        "usuarios": usuarios,
        "eventos": eventos,
    }

    # ── Mesas (optional — dico_tables.csv) ───────────────────────────────────
    if "dico_tables" in raw:
        mesas = (
            raw["dico_tables"]
            .withColumnRenamed("id", "table_id")
            .withColumn("id", add_namespace("table_id", prefix))
            .withColumnRenamed("number", "table_number")
            .withColumn("table_number", F.col("table_number").cast(IntegerType()))
            .withColumn("capacity", F.col("capacity").cast(IntegerType()))
            # vip_suitability > 0.5 → is_vip; dico_tables has no per-event FK
            .withColumn(
                "is_vip",
                (F.col("vip_suitability").cast(DoubleType()) > 0.5).cast(BooleanType()),
            )
            .withColumn("event_id", F.lit(None).cast("string"))
            .withColumn("source", F.lit(prefix))
            .select("id", "table_number", "capacity", "is_vip", "event_id", "source")
        )
        result["mesas"] = mesas

    # ── Asistio_a (optional — tickets.csv with actual purchases) ─────────────
    if "tickets" in raw:
        asistio_a = (
            raw["tickets"]
            .withColumn("user_id", add_namespace("user_id", prefix))
            .withColumn("event_id", add_namespace("event_id", prefix))
            .withColumn("source", F.lit(prefix))
            .select("user_id", "event_id", "ticket_tier", "source")
        )
        result["asistio_a"] = asistio_a

    # ── Reservo (optional — reservations.csv) ─────────────────────────────────
    if "reservations" in raw:
        reservo = (
            raw["reservations"]
            .withColumn("user_id", add_namespace("user_id", prefix))
            .withColumn("table_id", add_namespace("table_id", prefix))
            .withColumn("event_id", add_namespace("event_id", prefix))
            .withColumn("source", F.lit(prefix))
            .select("user_id", "table_id", "event_id", "source")
        )
        result["reservo"] = reservo

    # ── Segmentos (optional — segments.csv) ───────────────────────────────────
    if "segments" in raw:
        segmentos = (
            raw["segments"]
            .withColumnRenamed("segment_name", "name")
            .withColumn("source", F.lit(prefix))
            .select("name", "description", "source")
        )
        result["segmentos"] = segmentos

    # ── Pertenece_a (optional — user_segments.csv) ────────────────────────────
    if "user_segments" in raw:
        pertenece_a = (
            raw["user_segments"]
            .withColumn("user_id", add_namespace("user_id", prefix))
            .withColumn("source", F.lit(prefix))
            .select("user_id", "segment_name", "source")
        )
        result["pertenece_a"] = pertenece_a

    return result
