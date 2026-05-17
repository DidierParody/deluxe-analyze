output "neo4j_static_ip" {
  value       = google_compute_address.neo4j_static_ip.address
  description = "Static IP for Neo4j VM — add to allowed_neo4j_ips for other environments, and use as bolt+s://<IP>:7687 in notebooks"
}

output "neo4j_vm_name" {
  value = google_compute_instance.neo4j.name
}
