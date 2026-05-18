resource "google_cloud_scheduler_job" "dispatcher" {
  name             = "dispatcher-trigger"
  description      = "Triggers the CDC dispatcher every 15 minutes"
  schedule         = "*/15 * * * *"
  time_zone        = "UTC"
  attempt_deadline = "900s"

  http_target {
    # Cloud Run Jobs are a v2 resource; the v1 regional endpoint only covers
    # Services.  Use the global v2 API endpoint for Job execution.
    uri         = "https://run.googleapis.com/v2/projects/${var.project_id}/locations/${var.region}/jobs/dispatcher:run"
    http_method = "POST"

    # Cloud Run Admin API is a Google API — it requires an OAuth 2.0 access token,
    # NOT an OIDC ID token.  Use oauth_token with the Cloud Run Admin API scope.
    oauth_token {
      service_account_email = google_service_account.dispatcher.email
      scope                 = "https://www.googleapis.com/auth/cloud-platform"
    }
  }
}
