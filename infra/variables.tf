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
  # e2-small (2 GB, shared-core) frees the 1 vCPU from CPUS_ALL_REGIONS
  # quota — the project limit is 12, and Dataproc Serverless needs all 12.
  default = "e2-small"
}

variable "neo4j_disk_size_gb" {
  type    = number
  default = 50
}
