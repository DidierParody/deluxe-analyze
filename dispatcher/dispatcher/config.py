from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    GCP_PROJECT: str
    GCP_REGION: str = "us-central1"
    PUBSUB_SUBSCRIPTION: str = "cdc-events-sub"

    # Dataproc standard single-node cluster
    DATAPROC_CLUSTER: str = "deluxe-etl-cluster"

    # ETL artifacts bucket (bare name — no gs:// prefix)
    ETL_ARTIFACTS_BUCKET: str

    # Neo4j — use internal VPC IP so traffic stays within subnet-graph
    NEO4J_URI: str = "bolt://10.20.20.2:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str
    NEO4J_DATABASE: str = "neo4j"

    MAX_MESSAGES: int = 1000

    # Cluster auto-provisioning — used when ensure_cluster_exists() recreates
    # the cluster after idle_delete_ttl auto-deletes it.
    ETL_SUBNET: str = "projects/engaged-stage-463123-e0/regions/us-central1/subnetworks/subnet-data"
    DATAPROC_SA: str = "dataproc-etl-sa@engaged-stage-463123-e0.iam.gserviceaccount.com"

    # Kept for backward compatibility — no longer used by submit.py
    DATAPROC_BATCH_TEMPLATE: str = ""
    NEO4J_CONNECTOR_VERSION: str = "5.3.1"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
