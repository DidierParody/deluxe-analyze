import time
from google.cloud import dataproc_v1
from google.cloud.dataproc_v1.types import Batch

from .config import Settings


def submit_batch(project: str, region: str, s3_uris: list[str], config: Settings) -> str:
    client = dataproc_v1.BatchControllerClient(
        client_options={"api_endpoint": f"{region}-dataproc.googleapis.com:443"}
    )

    batch = Batch(
        pyspark_batch=dataproc_v1.PySparkBatch(
            main_python_file_uri=f"gs://{config.ETL_ARTIFACTS_BUCKET}/jobs/main.py",
            args=["--mode", "cdc", "--s3-uris", ",".join(s3_uris)],
        ),
        runtime_config=dataproc_v1.RuntimeConfig(
            properties={
                "spark.jars.packages": (
                    f"org.neo4j:neo4j-connector-apache-spark_2.13:"
                    f"{config.NEO4J_CONNECTOR_VERSION}_for_spark_3"
                )
            }
        ),
        environment_config=dataproc_v1.EnvironmentConfig(
            execution_config=dataproc_v1.ExecutionConfig(
                subnetwork_uri=config.ETL_SUBNET,
            )
        ),
    )

    operation = client.create_batch(
        parent=f"projects/{project}/locations/{region}",
        batch=batch,
    )

    return operation.metadata.batch


def wait_for_batch(
    batch_name: str,
    poll_interval_seconds: int = 30,
    timeout_seconds: int = 1800,
) -> bool:
    client = dataproc_v1.BatchControllerClient()
    deadline = time.monotonic() + timeout_seconds

    while True:
        if time.monotonic() > deadline:
            raise TimeoutError(f"Batch {batch_name} did not complete within {timeout_seconds}s")

        batch = client.get_batch(name=batch_name)
        state = batch.state

        if state == dataproc_v1.Batch.State.SUCCEEDED:
            return True
        if state in (
            dataproc_v1.Batch.State.FAILED,
            dataproc_v1.Batch.State.CANCELLED,
        ):
            return False

        time.sleep(poll_interval_seconds)
