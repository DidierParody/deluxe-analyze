# Bootstrap: create bucket manually before first `terraform init`
terraform {
  backend "gcs" {
    bucket = "deluxe-analyze-tfstate"
    prefix = "terraform/state"
  }
}
