"""Runtime configuration loaded from environment variables / .env."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    NEO4J_URI: str = "bolt://34.28.39.13:7687"
    NEO4J_USERNAME: str = "neo4j"
    NEO4J_PASSWORD: str  # no default — must be provided
    NEO4J_DATABASE: str = "neo4j"

    DASHBOARD_API_KEY: str  # 32+ chars expected

    CORS_ORIGINS: list[str] = ["*"]
    GDS_GRAPH_NAME: str = "socialGraph"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
