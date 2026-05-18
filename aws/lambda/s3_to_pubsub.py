# Lambda: s3-to-pubsub
#
# GCP auth: loads a GCP service account JSON key from AWS SSM Parameter Store
# (SecureString) at cold-start and uses it to obtain short-lived OAuth tokens.
#
# Environment variables required:
#   GCP_PROJECT  — GCP project ID
#   PUBSUB_TOPIC — Pub/Sub topic name (default: "cdc-events")
#   SSM_KEY      — SSM parameter name holding the GCP SA JSON key

import json
import os
import urllib.request
import urllib.error
import base64
import boto3
import google.auth.transport.requests
from google.oauth2 import service_account

GCP_PROJECT = os.environ["GCP_PROJECT"]
PUBSUB_TOPIC = os.environ.get("PUBSUB_TOPIC", "cdc-events")
SSM_KEY = os.environ.get("SSM_KEY", "/deluxe-analyze/gcp-sa-key")

# Cache credentials across warm invocations
_credentials = None


def _load_credentials() -> service_account.Credentials:
    global _credentials
    if _credentials is not None and _credentials.valid:
        return _credentials
    ssm = boto3.client("ssm", region_name="us-east-1")
    response = ssm.get_parameter(Name=SSM_KEY, WithDecryption=True)
    key_json = response["Parameter"]["Value"]
    sa_info = json.loads(key_json)
    _credentials = service_account.Credentials.from_service_account_info(
        sa_info,
        scopes=["https://www.googleapis.com/auth/pubsub"],
    )
    return _credentials


def get_access_token() -> str:
    """Get GCP access token using service account credentials from SSM."""
    creds = _load_credentials()
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
