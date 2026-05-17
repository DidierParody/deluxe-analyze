from pyspark.sql import DataFrame, SparkSession


def _table_key(s3_uri: str) -> str:
    # e.g. s3a://bucket/data/core/users/... -> "core.users"
    parts = s3_uri.replace("s3a://", "").replace("s3://", "").split("/")
    try:
        data_idx = parts.index("data")
        schema = parts[data_idx + 1]
        table = parts[data_idx + 2]
        return f"{schema}.{table}"
    except (ValueError, IndexError):
        return s3_uri


def load_cdc_parquet(
    spark: SparkSession,
    s3_uris: list[str],
    aws_access_key: str,
    aws_secret_key: str,
) -> dict[str, DataFrame]:
    spark.conf.set("fs.s3a.access.key", aws_access_key)
    spark.conf.set("fs.s3a.secret.key", aws_secret_key)
    spark.conf.set("fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    spark.conf.set("fs.s3a.aws.credentials.provider", "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider")

    grouped: dict[str, list[str]] = {}
    for uri in s3_uris:
        key = _table_key(uri)
        grouped.setdefault(key, []).append(uri)

    return {key: spark.read.parquet(*uris) for key, uris in grouped.items()}
