from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import BooleanType, DateType, DoubleType, IntegerType, TimestampType

from etl.normalize.canonical import add_namespace


def normalize_csv(raw: dict[str, DataFrame], prefix: str = "csv") -> dict[str, DataFrame]:
    usuarios = (
        raw["users"]
        .withColumn("id", add_namespace("user_id", prefix))
        .withColumn("vip_affinity", F.col("vip_affinity").cast(DoubleType()))
        .withColumn("invite_power", F.col("invite_power").cast(DoubleType()))
        .withColumn("newcomer_affinity", F.col("newcomer_affinity").cast(DoubleType()))
        .withColumn("mixing_score", F.col("mixing_score").cast(DoubleType()))
        .withColumn("source", F.lit(prefix))
        .select(
            "id", "telegram_id", "username", "social_role", "social_group_id",
            "secondary_group_id", "attendance_level", "vip_affinity", "invite_power",
            "table_preference", "rfm_seed_segment", "newcomer_affinity", "mixing_score", "source",
        )
    )

    eventos = (
        raw["events"]
        .withColumn("id", add_namespace("event_id", prefix))
        .withColumn("vip_pull", F.col("vip_pull").cast(DoubleType()))
        .withColumn("event_date", F.col("event_date").cast(DateType()))
        .withColumn("start_time", F.col("start_time").cast(TimestampType()))
        .withColumn("end_time", F.col("end_time").cast(TimestampType()))
        .withColumn("event_state_id", F.col("event_state_id").cast(IntegerType()))
        .withColumn("source", F.lit(prefix))
        .select(
            "id", "name", "event_type", "expected_demand_level", "vip_pull",
            "event_date", "start_time", "end_time", "event_state_id", "source",
        )
    )

    mesas = (
        raw["tables"]
        .withColumn("id", add_namespace("table_id", prefix))
        .withColumn("event_id", add_namespace("event_id", prefix))
        .withColumn("table_number", F.col("table_number").cast(IntegerType()))
        .withColumn("capacity", F.col("capacity").cast(IntegerType()))
        .withColumn("is_vip", F.col("is_vip").cast(BooleanType()))
        .withColumn("source", F.lit(prefix))
        .select("id", "table_number", "capacity", "is_vip", "event_id", "source")
    )

    segmentos = (
        raw["segments"]
        .withColumnRenamed("segment_name", "name")
        .withColumn("source", F.lit(prefix))
        .select("name", "description", "source")
    )

    asistio_a = (
        raw["tickets"]
        .withColumn("user_id", add_namespace("user_id", prefix))
        .withColumn("event_id", add_namespace("event_id", prefix))
        .withColumn("source", F.lit(prefix))
        .select("user_id", "event_id", "ticket_tier", "source")
    )

    reservo = (
        raw["reservations"]
        .withColumn("user_id", add_namespace("user_id", prefix))
        .withColumn("table_id", add_namespace("table_id", prefix))
        .withColumn("event_id", add_namespace("event_id", prefix))
        .withColumn("source", F.lit(prefix))
        .select("user_id", "table_id", "event_id", "source")
    )

    pertenece_a = (
        raw["user_segments"]
        .withColumn("user_id", add_namespace("user_id", prefix))
        .withColumnRenamed("segment_name", "segment_name")
        .withColumn("source", F.lit(prefix))
        .select("user_id", "segment_name", "source")
    )

    return {
        "usuarios": usuarios,
        "eventos": eventos,
        "mesas": mesas,
        "segmentos": segmentos,
        "asistio_a": asistio_a,
        "reservo": reservo,
        "pertenece_a": pertenece_a,
    }
