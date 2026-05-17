resource "google_cloud_scheduler_job" "dispatcher" {
  name             = "dispatcher-trigger"
  description      = "Triggers the CDC dispatcher every 15 minutes"
  schedule         = "*/15 * * * *"
  time_zone        = "UTC"
  attempt_deadline = "900s"

  http_target {
    uri         = "https://${var.region}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${var.project_id}/jobs/dispatcher:run"
    http_method = "POST"

    oidc_token {
      service_account_email = google_service_account.dispatcher.email
      audience              = "https://${var.region}-run.googleapis.com/"
    }
  }
}
