resource "google_artifact_registry_repository" "dispatcher" {
  location      = var.region
  repository_id = "deluxe-dispatcher"
  format        = "DOCKER"
}

resource "google_cloud_run_v2_job" "dispatcher" {
  name     = "dispatcher"
  location = var.region

  # The image is managed by deploy-dispatcher.yml CI/CD, not by Terraform.
  # Ignore changes to the image so subsequent terraform applies don't revert
  # it to the initial placeholder.
  lifecycle {
    ignore_changes = [template[0].template[0].containers[0].image]
  }

  template {
    template {
      service_account = google_service_account.dispatcher.email

      containers {
        # Placeholder image for initial apply — deploy-dispatcher.yml replaces
        # this on every push to main that touches dispatcher/.
        image = "us-docker.pkg.dev/cloudrun/container/hello"

        # ── GCP / project ───────────────────────────────────────────────────
        env {
          name  = "GCP_PROJECT"
          value = var.project_id
        }
        env {
          name  = "GCP_REGION"
          value = var.region
        }

        # ── Pub/Sub ─────────────────────────────────────────────────────────
        env {
          name  = "PUBSUB_SUBSCRIPTION"
          value = "cdc-events-sub"
        }

        # ── Dataproc ─────────────────────────────────────────────────────────
        env {
          name  = "DATAPROC_CLUSTER"
          value = "deluxe-etl-cluster"
        }
        env {
          name  = "ETL_ARTIFACTS_BUCKET"
          value = google_storage_bucket.etl_artifacts.name
        }
        env {
          name  = "ETL_SUBNET"
          value = "projects/${var.project_id}/regions/${var.region}/subnetworks/${google_compute_subnetwork.data.name}"
        }
        env {
          name  = "DATAPROC_SA"
          value = google_service_account.dataproc_etl.email
        }

        # ── Neo4j (internal VPC Bolt endpoint) ──────────────────────────────
        env {
          # Neo4j VM has a deterministic internal IP (first address in subnet-graph
          # 10.20.20.0/24).  Hardcoded here since there is no internal static-IP
          # Terraform resource for this VM.
          name  = "NEO4J_URI"
          value = "bolt://10.20.20.2:7687"
        }
        env {
          name  = "NEO4J_USER"
          value = "neo4j"
        }
        env {
          name  = "NEO4J_DATABASE"
          value = "neo4j"
        }
        env {
          name = "NEO4J_PASSWORD"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.neo4j_password.secret_id
              version = "latest"
            }
          }
        }

        # ── Watermark (CDC deduplication state) ──────────────────────────────
        env {
          name  = "GCS_WATERMARK_BUCKET"
          value = google_storage_bucket.watermark.name
        }

        resources {
          limits = {
            cpu    = "1"
            memory = "512Mi"
          }
        }
      }

      timeout = "1800s"
    }
  }
}
