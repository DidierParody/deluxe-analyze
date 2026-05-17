# ---------------------------------------------------------------------------
# dataproc-etl-sa bindings
# ---------------------------------------------------------------------------

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

# ---------------------------------------------------------------------------
# dispatcher-sa bindings
# ---------------------------------------------------------------------------

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

# ---------------------------------------------------------------------------
# neo4j-vm-sa bindings
# ---------------------------------------------------------------------------

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
