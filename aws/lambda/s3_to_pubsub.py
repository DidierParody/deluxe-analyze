# Lambda: s3-to-pubsub
#
# For GCP auth, this Lambda must have a GCP Workload Identity Pool configured,
# OR deploy with a GCP service account JSON stored in AWS Secrets Manager.
# The simpler approach for academic setup: store the GCP SA key in AWS SSM
# Parameter Store (SecureString) and load it at runtime via boto3.
#
# Environment variables required:
#   GCP_PROJECT  — GCP project ID
#   PUBSUB_TOPIC — Pub/Sub topic name (default: "cdc-events")

import json
import os
import urllib.request
import urllib.error
import base64
import google.auth
import google.auth.transport.requests
from google.oauth2 import service_account

GCP_PROJECT = os.environ["GCP_PROJECT"]
PUBSUB_TOPIC = os.environ.get("PUBSUB_TOPIC", "cdc-events")


def get_access_token() -> str:
    """Get GCP access token using Application Default Credentials or env var."""
    creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/pubsub"])
    creds.refresh(google.auth.transport.requests.Request())
    return creds.token


def publish_to_pubsub(s3_uri: str, table: str, token: str) -> None:
    message = {
        "messages": [{
            "data": base64.b64encode(s3_uri.encode()).decode(),
            "attributes": {"table": table}
        }]
    }
    url = f"https://pubsub.googleapis.com/v1/projects/{GCP_PROJECT}/topics/{PUBSUB_TOPIC}:publish"
    req = urllib.request.Request(
        url,
        data=json.dumps(message).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        resp.read()


def handler(event, context):
    token = get_access_token()
    for record in event["Records"]:
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]
        s3_uri = f"s3://{bucket}/{key}"
        # Extract table name from DMS path: data/<schema>/<table>/...
        parts = key.split("/")
        table = parts[2] if len(parts) > 2 else "unknown"
        publish_to_pubsub(s3_uri, table, token)
    return {"statusCode": 200}
