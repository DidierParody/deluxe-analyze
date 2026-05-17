variable "project_id" {
  type        = string
  description = "GCP project ID"
}

variable "region" {
  type    = string
  default = "us-central1"
}

variable "zone" {
  type    = string
  default = "us-central1-a"
}

variable "allowed_neo4j_ips" {
  type        = list(string)
  default     = []
  description = "CIDR ranges allowed to access Neo4j ports 7687/7474. Add your laptop and Colab IPs here."
}

variable "github_repo" {
  type        = string
  default     = "DidierParody/deluxe-analyze"
  description = "GitHub repo for Workload Identity Federation"
}

variable "neo4j_machine_type" {
  type    = string
  default = "e2-medium"
}

variable "neo4j_disk_size_gb" {
  type    = number
  default = 50
}
