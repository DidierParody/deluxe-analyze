resource "google_monitoring_alert_policy" "dispatcher_failure" {
  display_name = "Dispatcher Cloud Run Job Failure"
  combiner     = "OR"

  conditions {
    display_name = "Cloud Run Job failed"
    condition_threshold {
      filter          = "resource.type=\"cloud_run_job\" AND metric.type=\"run.googleapis.com/job/completed_task_attempt_count\" AND metric.labels.result=\"failed\""
      comparison      = "COMPARISON_GT"
      threshold_value = 0
      duration        = "60s"
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }

  notification_channels = [] # Add channel IDs manually after infra apply
  alert_strategy {
    auto_close = "604800s"
  }
}

resource "google_monitoring_alert_policy" "pubsub_backlog" {
  display_name = "Pub/Sub CDC Backlog High"
  combiner     = "OR"

  conditions {
    display_name = "Undelivered messages > 10000"
    condition_threshold {
      filter          = "resource.type=\"pubsub_subscription\" AND resource.labels.subscription_id=\"cdc-events-sub\" AND metric.type=\"pubsub.googleapis.com/subscription/num_undelivered_messages\""
      comparison      = "COMPARISON_GT"
      threshold_value = 10000
      duration        = "300s"
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_MEAN"
      }
    }
  }

  notification_channels = []
  alert_strategy {
    auto_close = "604800s"
  }
}
