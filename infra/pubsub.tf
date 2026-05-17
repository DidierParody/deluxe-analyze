resource "google_pubsub_topic" "cdc_events" {
  name = "cdc-events"
}

resource "google_pubsub_topic" "cdc_events_dlq" {
  name = "cdc-events-dlq"
}

resource "google_pubsub_subscription" "cdc_events_sub" {
  name  = "cdc-events-sub"
  topic = google_pubsub_topic.cdc_events.name

  ack_deadline_seconds       = 600
  message_retention_duration = "604800s" # 7 days

  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.cdc_events_dlq.id
    max_delivery_attempts = 5
  }

  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }
}

resource "google_pubsub_subscription" "cdc_events_dlq_sub" {
  name                 = "cdc-events-dlq-sub"
  topic                = google_pubsub_topic.cdc_events_dlq.name
  ack_deadline_seconds = 600
}
