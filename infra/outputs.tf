# ── Network ───────────────────────────────────────────────────────────────────

output "vpc_name" {
  value = google_compute_network.main.name
}

output "subnet_data_self_link" {
  value = google_compute_subnetwork.data.self_link
}

output "subnet_graph_self_link" {
  value = google_compute_subnetwork.graph.self_link
}

# ── Compute ───────────────────────────────────────────────────────────────────

output "neo4j_static_ip" {
  value       = google_compute_address.neo4j_static_ip.address
  description = "Static IP for Neo4j VM — add to allowed_neo4j_ips for other envs, use as bolt+s://<IP>:7687 in notebooks"
}

output "neo4j_vm_name" {
  value = google_compute_instance.neo4j.name
}

# ── IAM / WIF ─────────────────────────────────────────────────────────────────

output "dataproc_etl_sa_email" {
  value = google_service_account.dataproc_etl.email
}

output "dispatcher_sa_email" {
  value = google_service_account.dispatcher.email
}

output "wif_provider_name" {
  value       = google_iam_workload_identity_pool_provider.github.name
  description = "Use this in GitHub Actions: id-token with audience set to this value"
}

output "github_actions_sa_email" {
  value = google_service_account.github_actions.email
}

# ── Storage ───────────────────────────────────────────────────────────────────

output "etl_artifacts_bucket" {
  value = google_storage_bucket.etl_artifacts.name
}

output "dataproc_subnet" {
  value = google_compute_subnetwork.data.self_link
}

output "dataproc_sa_email" {
  value = google_service_account.dataproc_etl.email
}

# ── Secrets ───────────────────────────────────────────────────────────────────

output "neo4j_password_secret_id" {
  description = "Resource ID of the neo4j-password secret"
  value       = google_secret_manager_secret.neo4j_password.id
}

output "aws_hmac_access_key_secret_id" {
  description = "Resource ID of the aws-hmac-access-key secret"
  value       = google_secret_manager_secret.aws_hmac_access_key.id
}

output "aws_hmac_secret_key_secret_id" {
  description = "Resource ID of the aws-hmac-secret-key secret"
  value       = google_secret_manager_secret.aws_hmac_secret_key.id
}
