import json
import sys
import logging
from google.cloud import pubsub_v1
from .config import Settings
from .submit import ensure_cluster_exists, submit_batch, wait_for_batch

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    config = Settings()
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(config.GCP_PROJECT, config.PUBSUB_SUBSCRIPTION)

    response = subscriber.pull(
        request={"subscription": subscription_path, "max_messages": config.MAX_MESSAGES},
        timeout=30,
    )

    messages = response.received_messages
    if not messages:
        logger.info("No messages in subscription, exiting.")
        sys.exit(0)

    logger.info(f"Pulled {len(messages)} messages")

    ack_ids = [msg.ack_id for msg in messages]

    # Support two message formats:
    #
    # 1. Lambda (production): data = base64(s3://bucket/key), attributes = {table: ...}
    #    The Lambda in aws/lambda/s3_to_pubsub.py encodes the raw S3 URI as the
    #    message body.
    #
    # 2. JSON (manual tests / future): data = base64({"bucket":..., "key":...})
    #    Used when publishing test messages manually via gcloud pubsub topics publish.
    s3_uris = []
    for msg in messages:
        try:
            raw = msg.message.data.decode()
            if not raw:
                logger.warning("Skipping empty message")
                continue

            # Try JSON format first
            try:
                payload = json.loads(raw)
                bucket = payload.get("bucket", "")
                key = payload.get("key", "")
                s3_uri = f"s3://{bucket}/{key}" if bucket and key else None
            except json.JSONDecodeError:
                # Lambda format: raw S3 URI string
                s3_uri = raw if raw.startswith("s3://") else None

            if not s3_uri:
                logger.warning("Unrecognised message format, skipping: %.80s", raw)
                continue
            if "awsdms_status" in s3_uri:
                continue
            s3_uris.append(s3_uri)
        except AttributeError as exc:
            logger.warning("Skipping malformed message: %s", exc)
    s3_uris = list(set(s3_uris))  # deduplicate
    if not s3_uris:
        logger.info("No data URIs after filtering DMS status files; ACKing and exiting.")
        subscriber.acknowledge(request={"subscription": subscription_path, "ack_ids": ack_ids})
        sys.exit(0)

    # Ensure the cluster exists — idle_delete_ttl may have removed it
    ensure_cluster_exists(config.GCP_PROJECT, config.GCP_REGION, config)

    logger.info(f"Submitting batch for {len(s3_uris)} unique S3 URIs")
    batch_name = submit_batch(config.GCP_PROJECT, config.GCP_REGION, s3_uris, config)

    success = wait_for_batch(batch_name, region=config.GCP_REGION)

    if success:
        logger.info("Batch succeeded, ACKing messages")
        subscriber.acknowledge(request={"subscription": subscription_path, "ack_ids": ack_ids})
        sys.exit(0)
    else:
        logger.error("Batch failed, NACKing messages (will retry via dead-letter)")
        subscriber.modify_ack_deadline(
            request={
                "subscription": subscription_path,
                "ack_ids": ack_ids,
                "ack_deadline_seconds": 0,
            }
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
