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
