# ── Service accounts ──────────────────────────────────────────────────────────

resource "google_service_account" "dataproc_etl" {
  account_id   = "dataproc-etl-sa"
  display_name = "Dataproc ETL Service Account"
}

resource "google_service_account" "dispatcher" {
  account_id   = "dispatcher-sa"
  display_name = "Cloud Run Dispatcher Service Account"
}

resource "google_service_account" "neo4j_vm" {
  account_id   = "neo4j-vm-sa"
  display_name = "Neo4j VM Service Account"
}

# ── dataproc-etl-sa bindings ──────────────────────────────────────────────────

resource "google_project_iam_member" "dataproc_etl_worker" {
  project = var.project_id
  role    = "roles/dataproc.worker"
  member  = "serviceAccount:${google_service_account.dataproc_etl.email}"
}

resource "google_project_iam_member" "dataproc_etl_storage_viewer" {
  project = var.project_id
  role    = "roles/storage.objectViewer"
  member  = "serviceAccount:${google_service_account.dataproc_etl.email}"
}

resource "google_project_iam_member" "dataproc_etl_storage_admin" {
  project = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.dataproc_etl.email}"
}

resource "google_project_iam_member" "dataproc_etl_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.dataproc_etl.email}"
}

# ── dispatcher-sa bindings ────────────────────────────────────────────────────

resource "google_project_iam_member" "dispatcher_pubsub_subscriber" {
  project = var.project_id
  role    = "roles/pubsub.subscriber"
  member  = "serviceAccount:${google_service_account.dispatcher.email}"
}

resource "google_project_iam_member" "dispatcher_dataproc_editor" {
  project = var.project_id
  role    = "roles/dataproc.editor"
  member  = "serviceAccount:${google_service_account.dispatcher.email}"
}

resource "google_service_account_iam_member" "dispatcher_act_as_dataproc_etl" {
  service_account_id = google_service_account.dataproc_etl.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.dispatcher.email}"
}

# Dataproc service agent must be able to actAs dataproc-etl-sa to create
# cluster VMs with that custom service account.  Without this binding the
# cluster enters ERROR state immediately (VM never launches).
resource "google_service_account_iam_member" "dataproc_agent_act_as_etl" {
  service_account_id = google_service_account.dataproc_etl.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:service-${data.google_project.project.number}@dataproc-accounts.iam.gserviceaccount.com"
}

# dispatcher-sa reads AWS HMAC keys and neo4j-password from Secret Manager
# when building the Dataproc job submission payload.
resource "google_project_iam_member" "dispatcher_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.dispatcher.email}"
}

# ── neo4j-vm-sa bindings ──────────────────────────────────────────────────────

resource "google_project_iam_member" "neo4j_vm_log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.neo4j_vm.email}"
}

resource "google_project_iam_member" "neo4j_vm_metric_writer" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.neo4j_vm.email}"
}

# ── Workload Identity Federation (GitHub Actions) ─────────────────────────────

resource "google_iam_workload_identity_pool" "github" {
  workload_identity_pool_id = "github-actions-pool"
  display_name              = "GitHub Actions Pool"
}

resource "google_iam_workload_identity_pool_provider" "github" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-actions-provider"
  display_name                       = "GitHub Actions OIDC Provider"

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }

  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.actor"      = "assertion.actor"
    "attribute.repository" = "assertion.repository"
  }

  attribute_condition = "assertion.repository == '${var.github_repo}'"
}

resource "google_service_account" "github_actions" {
  account_id   = "github-actions-sa"
  display_name = "GitHub Actions Service Account"
}

resource "google_service_account_iam_member" "wif_binding" {
  service_account_id = google_service_account.github_actions.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github.name}/attribute.repository/${var.github_repo}"
}

resource "google_project_iam_member" "github_actions_terraform" {
  project = var.project_id
  role    = "roles/editor"
  member  = "serviceAccount:${google_service_account.github_actions.email}"
}
