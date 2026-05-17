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
