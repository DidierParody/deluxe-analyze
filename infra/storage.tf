resource "google_storage_bucket" "etl_artifacts" {
  name          = "${var.project_id}-etl-artifacts"
  location      = var.region
  force_destroy = false

  versioning {
    enabled = true
  }

  uniform_bucket_level_access = true
}

resource "google_storage_bucket" "seed" {
  name                        = "${var.project_id}-seed"
  location                    = var.region
  force_destroy               = false
  uniform_bucket_level_access = true
}

resource "google_storage_bucket" "watermark" {
  name                        = "${var.project_id}-watermark"
  location                    = var.region
  force_destroy               = false
  uniform_bucket_level_access = true

  lifecycle_rule {
    action { type = "Delete" }
    condition { age = 30 }
  }
}
