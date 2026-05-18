"""Dataproc ETL entry point.

Config is read from env vars (pydantic-settings) but can be overridden via CLI
flags.  In Dataproc YARN-client mode, ``spark.driverEnv.*`` properties are NOT
propagated as OS environment variables, so the caller must pass config as
``--flag value`` arguments; this module injects them into ``os.environ`` before
Settings() is instantiated.
"""

import argparse
import os


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Deluxe ETL job")
    parser.add_argument("--mode", choices=["csv", "cdc"], required=True)
    parser.add_argument("--s3-uris", default="", help="Comma-separated S3 URIs (cdc mode only)")
    # Config overrides — set as CLI args when env vars are not available (YARN)
    parser.add_argument("--gcp-project", default="")
    parser.add_argument("--gcp-region", default="us-central1")
    parser.add_argument("--neo4j-uri", default="")
    parser.add_argument("--neo4j-user", default="neo4j")
    parser.add_argument("--neo4j-password", default="")
    parser.add_argument("--neo4j-database", default="neo4j")
    parser.add_argument("--gcs-seed-bucket", default="")
    return parser.parse_args()


def _inject_env(args: argparse.Namespace) -> None:
    """Write CLI-supplied values into os.environ so pydantic-settings picks them up."""
    mapping = {
        "GCP_PROJECT": args.gcp_project,
        "GCP_REGION": args.gcp_region,
        "NEO4J_URI": args.neo4j_uri,
        "NEO4J_USER": args.neo4j_user,
        "NEO4J_PASSWORD": args.neo4j_password,
        "NEO4J_DATABASE": args.neo4j_database,
        "GCS_SEED_BUCKET": args.gcs_seed_bucket,
    }
    for key, val in mapping.items():
        if val and key not in os.environ:
            os.environ[key] = val


def main() -> None:
    args = _parse_args()
    _inject_env(args)

    # Deferred imports: Settings() must see env vars already set above.
    from pyspark.sql import SparkSession  # noqa: PLC0415

    from etl.config import Settings  # noqa: PLC0415
    from etl.load.neo4j_writer import Neo4jWriter  # noqa: PLC0415
    from etl.normalize.canonical import CONOCE_A_CYPHER  # noqa: PLC0415
    from etl.normalize.from_csv import normalize_csv  # noqa: PLC0415
    from etl.normalize.from_v2 import normalize_v2  # noqa: PLC0415
    from etl.sources.csv_source import load_csvs  # noqa: PLC0415
    from etl.sources.s3_cdc_source import load_cdc_parquet  # noqa: PLC0415
    from etl.state.watermark import Watermark  # noqa: PLC0415

    config = Settings()

    spark = SparkSession.builder.appName("deluxe-etl").getOrCreate()
    writer = Neo4jWriter(
        config.NEO4J_URI,
        config.NEO4J_USER,
        config.NEO4J_PASSWORD,
        config.NEO4J_DATABASE,
    )
    writer.setup_schema()

    if args.mode == "csv":
        raw = load_csvs(spark, config.GCS_SEED_BUCKET)
        canonical = normalize_csv(raw)
    else:
        uris = [u for u in args.s3_uris.split(",") if u]
        raw = load_cdc_parquet(
            spark, uris, config.AWS_ACCESS_KEY_ID, config.AWS_SECRET_ACCESS_KEY
        )
        canonical = normalize_v2(raw)

    # ── Write nodes (always present) ─────────────────────────────────────────
    writer.write_nodes(canonical["usuarios"], "Usuario")
    writer.write_nodes(canonical["eventos"], "Evento")

    # ── Write optional nodes ──────────────────────────────────────────────────
    if "mesas" in canonical:
        writer.write_nodes(canonical["mesas"], "Mesa")
    if "segmentos" in canonical:
        writer.write_nodes(canonical["segmentos"], "Segmento")

    # ── Write optional relationships ──────────────────────────────────────────
    if "asistio_a" in canonical:
        writer.write_relationship(
            canonical["asistio_a"], "ASISTIO_A", "Usuario", "Evento", "user_id", "event_id"
        )
    if "reservo" in canonical:
        writer.write_relationship(
            canonical["reservo"], "RESERVO", "Usuario", "Mesa", "user_id", "table_id"
        )
    if "pertenece_a" in canonical:
        writer.write_relationship(
            canonical["pertenece_a"],
            "PERTENECE_A",
            "Usuario",
            "Segmento",
            "user_id",
            "segment_name",
        )

    # ── Derive CONOCE_A (co-attendance inference — pure Cypher, no GDS needed)
    writer.run_cypher(CONOCE_A_CYPHER)

    # ── Watermark (CDC mode only) ─────────────────────────────────────────────
    if args.mode == "cdc":
        wm = Watermark(config.GCS_WATERMARK_BUCKET)
        wm.mark_processed(uris)

    writer.close()
    spark.stop()


if __name__ == "__main__":
    main()
