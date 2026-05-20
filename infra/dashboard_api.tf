# ── Dashboard backend (FastAPI) — Cloud Run Service ──────────────────────────
# Separate from the dispatcher Cloud Run Job: this is a long-running service
# behind X-API-Key auth, fronting Neo4j with read-only graph analytics
# endpoints consumed by the Flutter dashboard.

resource "google_artifact_registry_repository" "dashboard_api" {
  location      = var.region
  repository_id = "dashboard-api"
  format        = "DOCKER"
  description   = "Container images for the dashboard FastAPI backend"
}

resource "google_service_account" "dashboard_api" {
  account_id   = "dashboard-api-sa"
  display_name = "Cloud Run dashboard-api service account"
}

resource "google_project_iam_member" "dashboard_api_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.dashboard_api.email}"
}

# Allow github-actions-sa to deploy new revisions
resource "google_service_account_iam_member" "github_act_as_dashboard_api" {
  service_account_id = google_service_account.dashboard_api.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.github_actions.email}"
}

resource "google_secret_manager_secret" "dashboard_api_key" {
  secret_id = "dashboard-api-key"
  replication {
    auto {}
  }
}

resource "google_cloud_run_v2_service" "dashboard_api" {
  name     = "dashboard-api"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  # Image is owned by CI (deploy-dashboard-backend.yml).
  lifecycle {
    ignore_changes = [template[0].containers[0].image]
  }

  template {
    service_account = google_service_account.dashboard_api.email

    scaling {
      min_instance_count = 0
      max_instance_count = 3
    }

    # Direct VPC egress so the container can reach Neo4j at 10.20.20.2.
    vpc_access {
      network_interfaces {
        network    = google_compute_network.main.name
        subnetwork = google_compute_subnetwork.data.name
      }
      egress = "PRIVATE_RANGES_ONLY"
    }

    containers {
      image = "us-docker.pkg.dev/cloudrun/container/hello"

      ports {
        container_port = 8080
      }

      env {
        name  = "NEO4J_URI"
        value = "bolt://10.20.20.2:7687"
      }
      env {
        name  = "NEO4J_USERNAME"
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
      env {
        name = "DASHBOARD_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.dashboard_api_key.secret_id
            version = "latest"
          }
        }
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }
    }
  }

  depends_on = [
    google_project_iam_member.dashboard_api_secret_accessor,
  ]
}

# Public access — auth happens via X-API-Key in the app.
resource "google_cloud_run_v2_service_iam_member" "dashboard_api_public" {
  location = google_cloud_run_v2_service.dashboard_api.location
  name     = google_cloud_run_v2_service.dashboard_api.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

output "dashboard_api_url" {
  value       = google_cloud_run_v2_service.dashboard_api.uri
  description = "Public URL of the dashboard backend"
}
