FROM python:3.11-slim

WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir .
COPY dispatcher/ dispatcher/

ENTRYPOINT ["python", "-m", "dispatcher"]
