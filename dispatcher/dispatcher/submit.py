"""Submit a PySpark job to the Dataproc standard single-node cluster.

Why standard cluster instead of Dataproc Serverless:
  The project CPUS_ALL_REGIONS quota is 12.  Serverless requires exactly 12
  (1 driver + 2 executors × 4 vCPU each) but the Neo4j VM (e2-small) consumes
  1 vCPU, leaving only 11 available.  A single-master Dataproc cluster on
  n1-standard-2 uses 2 vCPUs — total 3/12 — well within quota.

Why CLI args instead of spark.driverEnv.*:
  In YARN client mode spark.driverEnv.* properties are NOT propagated as OS
  environment variables to the driver process.  Config is passed as ``--flag``
  arguments and injected into os.environ in main.py before pydantic-settings
  reads them.
"""

import time

from google.cloud import dataproc_v1, secretmanager

from .config import Settings


def _get_secret(project: str, secret_id: str) -> str:
    """Fetch the latest version of a Secret Manager secret."""
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project}/secrets/{secret_id}/versions/latest"
    return client.access_secret_version(request={"name": name}).payload.data.decode()


def submit_job(project: str, region: str, s3_uris: list[str], config: Settings) -> str:
    """Submit the ETL PySpark job and return the fully-qualified job name."""
    client = dataproc_v1.JobControllerClient(
        client_options={"api_endpoint": f"{region}-dataproc.googleapis.com:443"}
    )

    artifacts = config.ETL_ARTIFACTS_BUCKET

    # Fetch AWS credentials from Secret Manager so Spark can read S3 Parquet files
    aws_key = _get_secret(project, "aws-hmac-access-key")
    aws_secret = _get_secret(project, "aws-hmac-secret-key")

    job = dataproc_v1.Job(
        placement=dataproc_v1.JobPlacement(cluster_name=config.DATAPROC_CLUSTER),
        pyspark_job=dataproc_v1.PySparkJob(
            main_python_file_uri=f"gs://{artifacts}/jobs/main.py",
            python_file_uris=[f"gs://{artifacts}/deps/etl-deps.zip"],
            jar_file_uris=[f"gs://{artifacts}/jars/neo4j-spark-connector.jar"],
            args=[
                "--mode", "cdc",
                "--s3-uris", ",".join(s3_uris),
                "--gcp-project", project,
                "--gcp-region", region,
                "--neo4j-uri", config.NEO4J_URI,
                "--neo4j-user", config.NEO4J_USER,
                "--neo4j-password", config.NEO4J_PASSWORD,
                "--neo4j-database", config.NEO4J_DATABASE,
                "--aws-access-key-id", aws_key,
                "--aws-secret-access-key", aws_secret,
            ],
        ),
    )

    response = client.submit_job(project_id=project, region=region, job=job)
    job_id = response.reference.job_id
    return f"projects/{project}/regions/{region}/jobs/{job_id}"


def wait_for_job(
    job_name: str,
    region: str,
    poll_interval_seconds: int = 30,
    timeout_seconds: int = 1800,
) -> bool:
    """Poll until the Dataproc job reaches a terminal state. Returns True on success."""
    client = dataproc_v1.JobControllerClient(
        client_options={"api_endpoint": f"{region}-dataproc.googleapis.com:443"}
    )

    # job_name = "projects/{p}/regions/{r}/jobs/{id}" — extract ids
    parts = job_name.split("/")
    project, job_id = parts[1], parts[5]

    deadline = time.monotonic() + timeout_seconds

    while True:
        if time.monotonic() > deadline:
            raise TimeoutError(f"Job {job_name} did not complete within {timeout_seconds}s")

        job = client.get_job(project_id=project, region=region, job_id=job_id)
        state = job.status.state

        if state == dataproc_v1.JobStatus.State.DONE:
            return True
        if state in (
            dataproc_v1.JobStatus.State.ERROR,
            dataproc_v1.JobStatus.State.CANCELLED,
        ):
            return False

        time.sleep(poll_interval_seconds)


# ── Backward-compat shims (used by __main__.py) ────────────────────────────

def submit_batch(project: str, region: str, s3_uris: list[str], config: Settings) -> str:
    """Alias kept so __main__.py doesn't need a simultaneous change."""
    return submit_job(project, region, s3_uris, config)


def wait_for_batch(batch_name: str, region: str = "us-central1", **kwargs) -> bool:
    """Alias kept so __main__.py doesn't need a simultaneous change."""
    return wait_for_job(batch_name, region, **kwargs)
