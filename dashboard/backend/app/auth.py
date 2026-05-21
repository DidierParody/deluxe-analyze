"""X-API-Key header authentication for the dashboard API."""
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from .config import Settings

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
_settings = Settings()


def require_api_key(api_key: str | None = Security(_api_key_header)) -> str:
    if not api_key or api_key != _settings.DASHBOARD_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid X-API-Key",
        )
    return api_key
