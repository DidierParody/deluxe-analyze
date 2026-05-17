from pyspark.sql import DataFrame, SparkSession


_CSV_TABLES = [
    "users",
    "events",
    "tickets",
    "reservations",
    "tables",
    "table_assignments",
    "segments",
    "user_segments",
]


def load_csvs(spark: SparkSession, gcs_seed_bucket: str) -> dict[str, DataFrame]:
    result: dict[str, DataFrame] = {}
    for table in _CSV_TABLES:
        path = f"gs://{gcs_seed_bucket}/{table}.csv"
        result[table] = (
            spark.read.option("header", "true").option("inferSchema", "false").csv(path)
        )
    return result
