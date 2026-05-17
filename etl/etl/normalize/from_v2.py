from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import DateType, DoubleType, IntegerType, TimestampType

from etl.normalize.canonical import add_namespace


def normalize_v2(raw: dict[str, DataFrame], prefix: str = "v2") -> dict[str, DataFrame]:
    result: dict[str, DataFrame] = {}

    if "core.users" in raw:
        df = raw["core.users"]
        usuarios = (
            df.withColumn("id", add_namespace("user_id", prefix))
            .withColumn("vip_affinity", F.lit(None).cast(DoubleType()))
            .withColumn("invite_power", F.lit(None).cast(DoubleType()))
            .withColumn("newcomer_affinity", F.lit(None).cast(DoubleType()))
            .withColumn("mixing_score", F.lit(None).cast(DoubleType()))
            .withColumn("social_role", F.lit(None).cast("string"))
            .withColumn("social_group_id", F.lit(None).cast("string"))
            .withColumn("secondary_group_id", F.lit(None).cast("string"))
            .withColumn("attendance_level", F.lit(None).cast("string"))
            .withColumn("table_preference", F.lit(None).cast("string"))
            .withColumn("rfm_seed_segment", F.lit(None).cast("string"))
            .withColumn("source", F.lit(prefix))
            .select(
                "id",
                F.col("telegram_id") if "telegram_id" in df.columns
                else F.lit(None).cast("string").alias("telegram_id"),
                F.col("username") if "username" in df.columns
                else F.lit(None).cast("string").alias("username"),
                "social_role", "social_group_id", "secondary_group_id",
                "attendance_level", "vip_affinity", "invite_power", "table_preference",
                "rfm_seed_segment", "newcomer_affinity", "mixing_score", "source",
            )
        )
        result["usuarios"] = usuarios

    if "core.events" in raw:
        df = raw["core.events"]
        eventos = (
            df.withColumn("id", add_namespace("event_id", prefix))
            .withColumn(
                "vip_pull",
                F.col("vip_pull").cast(DoubleType()) if "vip_pull" in df.columns
                else F.lit(None).cast(DoubleType()),
            )
            .withColumn(
                "event_date",
                F.col("event_date").cast(DateType()) if "event_date" in df.columns
                else F.lit(None).cast(DateType()),
            )
            .withColumn(
                "start_time",
                F.col("start_time").cast(TimestampType()) if "start_time" in df.columns
                else F.lit(None).cast(TimestampType()),
            )
            .withColumn(
                "end_time",
                F.col("end_time").cast(TimestampType()) if "end_time" in df.columns
                else F.lit(None).cast(TimestampType()),
            )
            .withColumn(
                "event_state_id",
                F.col("event_state_id").cast(IntegerType()) if "event_state_id" in df.columns
                else F.lit(None).cast(IntegerType()),
            )
            .withColumn(
                "name",
                F.col("name") if "name" in df.columns
                else F.col("event_name").alias("name") if "event_name" in df.columns
                else F.lit(None).cast("string"),
            )
            .withColumn(
                "event_type",
                F.col("event_type") if "event_type" in df.columns
                else F.lit(None).cast("string"),
            )
            .withColumn(
                "expected_demand_level",
                F.col("expected_demand_level") if "expected_demand_level" in df.columns
                else F.lit(None).cast("string"),
            )
            .withColumn("source", F.lit(prefix))
            .select("id", "name", "event_type", "expected_demand_level", "vip_pull",
                    "event_date", "start_time", "end_time", "event_state_id", "source")
        )
        result["eventos"] = eventos

    if "core.dico_tables" in raw:
        df = raw["core.dico_tables"]
        table_num_col = "table_number" if "table_number" in df.columns else "numero_mesa" if "numero_mesa" in df.columns else None
        mesas = (
            df.withColumn("id", add_namespace("table_id", prefix))
            .withColumn("event_id", add_namespace("event_id", prefix) if "event_id" in df.columns else F.lit(None).cast("string"))
            .withColumn("table_number", (F.col(table_num_col) if table_num_col else F.lit(None)).cast(IntegerType()))
            .withColumn("capacity", F.col("capacity").cast(IntegerType()) if "capacity" in df.columns else F.lit(None).cast(IntegerType()))
            .withColumn("is_vip", F.col("is_vip").cast("boolean") if "is_vip" in df.columns else F.lit(None).cast("boolean"))
            .withColumn("source", F.lit(prefix))
            .select("id", "table_number", "capacity", "is_vip", "event_id", "source")
        )
        result["mesas"] = mesas

    if "transactions.tickets" in raw:
        df = raw["transactions.tickets"]
        asistio_a = (
            df.withColumn("user_id", add_namespace("user_id", prefix))
            .withColumn("event_id", add_namespace("event_id", prefix))
            .withColumn("ticket_tier", F.col("ticket_tier") if "ticket_tier" in df.columns else F.col("tier") if "tier" in df.columns else F.lit(None).cast("string"))
            .withColumn("source", F.lit(prefix))
            .select("user_id", "event_id", "ticket_tier", "source")
        )
        result["asistio_a"] = asistio_a

    if "transactions.reservations" in raw:
        df = raw["transactions.reservations"]
        reservo = (
            df.withColumn("user_id", add_namespace("user_id", prefix))
            .withColumn("table_id", add_namespace("table_id", prefix))
            .withColumn("event_id", add_namespace("event_id", prefix) if "event_id" in df.columns else F.lit(None).cast("string"))
            .withColumn("source", F.lit(prefix))
            .select("user_id", "table_id", "event_id", "source")
        )
        result["reservo"] = reservo

    return result
