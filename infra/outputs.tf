output "vpc_name" {
  value = google_compute_network.main.name
}

output "subnet_data_self_link" {
  value = google_compute_subnetwork.data.self_link
}

output "subnet_graph_self_link" {
  value = google_compute_subnetwork.graph.self_link
}

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
