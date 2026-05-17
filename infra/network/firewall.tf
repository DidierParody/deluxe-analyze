resource "google_compute_firewall" "allow_iap_ssh" {
  name    = "allow-iap-ssh"
  network = google_compute_network.main.name

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = ["35.235.240.0/20"]  # IAP tunnel IP range
  target_tags   = ["neo4j-vm"]
}

resource "google_compute_firewall" "allow_neo4j_from_dataproc" {
  name    = "allow-neo4j-from-dataproc"
  network = google_compute_network.main.name

  allow {
    protocol = "tcp"
    ports    = ["7687"]
  }

  source_ranges = [google_compute_subnetwork.data.ip_cidr_range]
  target_tags   = ["neo4j-vm"]
}

resource "google_compute_firewall" "allow_neo4j_from_whitelist" {
  count   = length(var.allowed_neo4j_ips) > 0 ? 1 : 0
  name    = "allow-neo4j-from-whitelist"
  network = google_compute_network.main.name

  allow {
    protocol = "tcp"
    ports    = ["7687", "7474"]
  }

  source_ranges = var.allowed_neo4j_ips
  target_tags   = ["neo4j-vm"]
}
