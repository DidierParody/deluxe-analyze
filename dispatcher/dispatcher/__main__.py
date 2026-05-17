import sys
import logging
from google.cloud import pubsub_v1
from .config import Settings
from .submit import submit_batch, wait_for_batch

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

    s3_uris = list({msg.message.data.decode() for msg in messages})
    ack_ids = [msg.ack_id for msg in messages]

    logger.info(f"Submitting batch for {len(s3_uris)} unique S3 URIs")
    batch_name = submit_batch(config.GCP_PROJECT, config.GCP_REGION, s3_uris, config)

    success = wait_for_batch(batch_name)

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
