from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    GCP_PROJECT: str
    GCP_REGION: str = "us-central1"
    PUBSUB_SUBSCRIPTION: str = "cdc-events-sub"
    DATAPROC_BATCH_TEMPLATE: str
    ETL_ARTIFACTS_BUCKET: str
    ETL_SUBNET: str
    NEO4J_CONNECTOR_VERSION: str = "5.3.1"
    MAX_MESSAGES: int = 1000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
