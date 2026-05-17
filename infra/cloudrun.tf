resource "google_artifact_registry_repository" "dispatcher" {
  location      = var.region
  repository_id = "deluxe-dispatcher"
  format        = "DOCKER"
}

resource "google_cloud_run_v2_job" "dispatcher" {
  name     = "dispatcher"
  location = var.region

  template {
    template {
      service_account = google_service_account.dispatcher.email

      containers {
        # Placeholder image for initial apply — deploy-dispatcher.yml updates this via CI/CD
        image = "us-docker.pkg.dev/cloudrun/container/hello"

        env {
          name  = "GCP_PROJECT"
          value = var.project_id
        }
        env {
          name  = "GCP_REGION"
          value = var.region
        }
        env {
          name  = "ETL_ARTIFACTS_BUCKET"
          value = google_storage_bucket.etl_artifacts.name
        }
        env {
          name  = "ETL_SUBNET"
          value = "regions/${var.region}/subnetworks/subnet-data"
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
