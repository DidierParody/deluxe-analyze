# Dataproc cluster lifecycle — managed by the dispatcher, NOT by Terraform.
#
# Why not Terraform-managed:
#   The google_dataproc_cluster resource does not support `terraform import`,
#   and the cluster is intentionally ephemeral: it has idle_delete_ttl=1h and
#   auto-deletes itself during quiet periods.  The dispatcher's
#   ensure_cluster_exists() recreates it transparently before each job
#   submission, so Terraform owning its lifecycle would cause conflicts.
#
# Cluster spec (enforced by ensure_cluster_exists in dispatcher/submit.py):
#   name            = "deluxe-etl-cluster"
#   master          = n1-standard-2, pd-standard 100 GB, 1 instance
#   workers         = 0 (single-node Spark local mode)
#   image           = 2.2-debian12  (Spark 3.5)
#   subnet          = subnet-data   (10.20.10.0/24, private)
#   service_account = dataproc-etl-sa
#   internal_ip_only = true         (Cloud NAT for egress)
#   idle_delete_ttl  = 3600s        (auto-delete after 1 h idle)
#   init_action      = gs://${project}-etl-artifacts/init/install-etl-deps.sh
