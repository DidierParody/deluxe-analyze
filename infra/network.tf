resource "google_compute_network" "main" {
  name                    = "deluxe-analyze-vpc"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "data" {
  name                     = "subnet-data"
  ip_cidr_range            = "10.20.10.0/24"
  region                   = var.region
  network                  = google_compute_network.main.id
  private_ip_google_access = true
}

resource "google_compute_subnetwork" "graph" {
  name                     = "subnet-graph"
  ip_cidr_range            = "10.20.20.0/24"
  region                   = var.region
  network                  = google_compute_network.main.id
  private_ip_google_access = true
}

resource "google_compute_router" "main" {
  name    = "deluxe-analyze-router"
  region  = var.region
  network = google_compute_network.main.id
}

resource "google_compute_router_nat" "main" {
  name                               = "deluxe-analyze-nat"
  router                             = google_compute_router.main.name
  region                             = var.region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"
}

resource "google_compute_firewall" "allow_iap_ssh" {
  name    = "allow-iap-ssh"
  network = google_compute_network.main.name

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = ["35.235.240.0/20"] # IAP tunnel IP range
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
