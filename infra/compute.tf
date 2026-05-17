resource "google_compute_address" "neo4j_static_ip" {
  name   = "neo4j-static-ip"
  region = var.region
}

resource "google_compute_instance" "neo4j" {
  name         = "neo4j-vm"
  machine_type = var.neo4j_machine_type
  zone         = var.zone
  tags         = ["neo4j-vm"]

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2204-lts"
      size  = var.neo4j_disk_size_gb
      type  = "pd-balanced"
    }
  }

  network_interface {
    subnetwork = google_compute_subnetwork.graph.self_link
    access_config {
      nat_ip = google_compute_address.neo4j_static_ip.address
    }
  }

  service_account {
    email  = google_service_account.neo4j_vm.email
    scopes = ["cloud-platform"]
  }

  metadata = {
    startup-script        = file("${path.module}/compute/startup.sh")
    neo4j-password-secret = google_secret_manager_secret.neo4j_password.secret_id
  }
}

resource "google_compute_resource_policy" "neo4j_snapshot" {
  name   = "neo4j-daily-snapshot"
  region = var.region

  snapshot_schedule_policy {
    schedule {
      daily_schedule {
        days_in_cycle = 1
        start_time    = "04:00"
      }
    }
    retention_policy {
      max_retention_days    = 7
      on_source_disk_delete = "KEEP_AUTO_SNAPSHOTS"
    }
  }
}

resource "google_compute_disk_resource_policy_attachment" "neo4j_snapshot" {
  name = google_compute_resource_policy.neo4j_snapshot.name
  disk = google_compute_instance.neo4j.boot_disk[0].source
  zone = var.zone
}
