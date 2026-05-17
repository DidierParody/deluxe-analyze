import json
from datetime import datetime, timezone

from google.cloud import storage


class Watermark:
    def __init__(self, gcs_bucket: str, job_name: str = "etl") -> None:
        self.gcs_bucket = gcs_bucket
        self.job_name = job_name
        self._client = storage.Client()

    def _bucket(self):
        return self._client.bucket(self.gcs_bucket)

    def _watermark_prefix(self) -> str:
        return f"watermark/{self.job_name}/"

    def mark_processed(self, s3_uris: list[str]) -> None:
        date_str = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
        blob_name = f"{self._watermark_prefix()}{date_str}.json"
        payload = {
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "uris": s3_uris,
        }
        blob = self._bucket().blob(blob_name)
        blob.upload_from_string(json.dumps(payload), content_type="application/json")

    def already_processed(self, s3_uri: str) -> bool:
        blobs = self._client.list_blobs(self.gcs_bucket, prefix=self._watermark_prefix())
        for blob in blobs:
            data = json.loads(blob.download_as_text())
            if s3_uri in data.get("uris", []):
                return True
        return False
