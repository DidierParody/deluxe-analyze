# Bootstrap: create bucket manually before first `terraform init`
terraform {
  backend "gcs" {
    bucket = "engaged-stage-463123-e0-tfstate"
    prefix = "terraform/state"
  }
}
