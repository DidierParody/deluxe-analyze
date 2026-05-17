from pyspark.sql import DataFrame, SparkSession

# Tables present in the GCS seed bucket with their actual file names.
# Optional tables are loaded only when the file exists; missing files are skipped
# instead of raising an error — transactional tables arrive via CDC (deluxe-v2).
_REQUIRED_CSV_TABLES = [
    "users",
    "events",
]

_OPTIONAL_CSV_TABLES = [
    "dico_tables",       # physical tables in the venue (catalog)
    "type_tickets",      # ticket tier catalog per event
    "tickets",           # actual ticket purchases  (filled by CDC)
    "reservations",      # table reservations       (filled by CDC)
    "table_assignments", # guest ↔ table mapping    (filled by CDC)
    "segments",          # RFM segment definitions  (filled by CDC)
    "user_segments",     # user ↔ segment mapping   (filled by CDC)
]


def load_csvs(spark: SparkSession, gcs_seed_bucket: str) -> dict[str, DataFrame]:
    result: dict[str, DataFrame] = {}

    for table in _REQUIRED_CSV_TABLES:
        path = f"gs://{gcs_seed_bucket}/{table}.csv"
        result[table] = (
            spark.read.option("header", "true").option("inferSchema", "false").csv(path)
        )

    for table in _OPTIONAL_CSV_TABLES:
        path = f"gs://{gcs_seed_bucket}/{table}.csv"
        try:
            df = spark.read.option("header", "true").option("inferSchema", "false").csv(path)
            # csv() on a missing GCS path returns an empty DataFrame without header —
            # treat zero columns as "file not present".
            if len(df.columns) > 0:
                result[table] = df
        except Exception:  # noqa: BLE001
            pass  # optional table absent — skip silently

    return result
