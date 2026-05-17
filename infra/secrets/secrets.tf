resource "google_secret_manager_secret" "neo4j_password" {
  secret_id = "neo4j-password"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "aws_hmac_access_key" {
  secret_id = "aws-hmac-access-key"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "aws_hmac_secret_key" {
  secret_id = "aws-hmac-secret-key"
  replication {
    auto {}
  }
}

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
