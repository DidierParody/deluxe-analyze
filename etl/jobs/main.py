import argparse

from pyspark.sql import SparkSession

from etl.config import Settings
from etl.load.neo4j_writer import Neo4jWriter
from etl.normalize.canonical import CONOCE_A_CYPHER
from etl.normalize.from_csv import normalize_csv
from etl.normalize.from_v2 import normalize_v2
from etl.sources.csv_source import load_csvs
from etl.sources.s3_cdc_source import load_cdc_parquet
from etl.state.watermark import Watermark


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Deluxe ETL job")
    parser.add_argument("--mode", choices=["csv", "cdc"], required=True)
    parser.add_argument("--s3-uris", default="", help="Comma-separated S3 URIs (cdc mode only)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
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
        uris = args.s3_uris.split(",")
        raw = load_cdc_parquet(spark, uris, config.AWS_ACCESS_KEY_ID, config.AWS_SECRET_ACCESS_KEY)
        canonical = normalize_v2(raw)

    writer.write_nodes(canonical["usuarios"], "Usuario")
    writer.write_nodes(canonical["eventos"], "Evento")
    writer.write_nodes(canonical["mesas"], "Mesa")
    writer.write_nodes(canonical["segmentos"], "Segmento")
    writer.write_relationship(
        canonical["asistio_a"], "ASISTIO_A", "Usuario", "Evento", "user_id", "event_id"
    )
    writer.write_relationship(
        canonical["reservo"], "RESERVO", "Usuario", "Mesa", "user_id", "table_id"
    )
    writer.write_relationship(
        canonical["pertenece_a"], "PERTENECE_A", "Usuario", "Segmento", "user_id", "segment_name"
    )

    writer.run_cypher(CONOCE_A_CYPHER)

    if args.mode == "cdc":
        wm = Watermark(config.GCS_WATERMARK_BUCKET)
        wm.mark_processed(uris)

    writer.close()
    spark.stop()


if __name__ == "__main__":
    main()
