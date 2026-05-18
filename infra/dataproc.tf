# Dataproc single-node cluster for ETL PySpark jobs.
#
# Why standard cluster instead of Dataproc Serverless:
#   The project CPUS_ALL_REGIONS quota is 12.  Serverless requires exactly 12
#   vCPUs (1 driver + 2×4 executors) — but the Neo4j VM consumes 1 vCPU,
#   leaving only 11 available.  A single n1-standard-2 master uses 2 vCPUs,
#   total = 3/12.
#
# Why single-node (no workers):
#   The ETL processes GCS CSVs + S3 Parquet files that fit in driver memory for
#   the current data volume.  Workers can be added via terraform later.

resource "google_dataproc_cluster" "etl" {
  name    = "deluxe-etl-cluster"
  project = var.project_id
  region  = var.region

  cluster_config {
    master_config {
      num_instances = 1
      machine_type  = "n1-standard-2"

      disk_config {
        boot_disk_type    = "pd-standard"
        boot_disk_size_gb = 100
      }
    }

    # Zero workers — single-node Spark local mode
    worker_config {
      num_instances = 0
    }

    software_config {
      image_version = "2.2-debian12"
      # Spark 3.5 ships with image 2.2
    }

    gce_cluster_config {
      subnetwork       = google_compute_subnetwork.data.name
      service_account  = google_service_account.dataproc_etl.email
      internal_ip_only = true
      # Cloud NAT (created in network.tf) provides outbound internet for pip installs
    }

    initialization_actions {
      # Installs pydantic-settings and other Python deps not bundled in the
      # Dataproc image.  The etl-deps.zip covers the etl package itself but
      # pydantic-settings must be installed at the OS level.
      script      = "gs://${var.project_id}-etl-artifacts/init/install-etl-deps.sh"
      timeout_sec = 300
    }
  }
}
