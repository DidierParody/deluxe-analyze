# Dataproc Serverless Batch configuration used by the dispatcher Cloud Run Job.
# This is documentation-as-code — actual batch submission happens in dispatcher/dispatcher/submit.py.

locals {
  dataproc_batch_config = {
    main_python_file = "gs://${var.project_id}-etl-artifacts/jobs/main.py"
    subnet           = google_compute_subnetwork.data.self_link
    service_account  = google_service_account.dataproc_etl.email
    spark_properties = {
      "spark.jars.packages" = "org.neo4j:neo4j-connector-apache-spark_2.13:5.3.1_for_spark_3"
    }
  }
}

output "dataproc_subnet" {
  value = google_compute_subnetwork.data.self_link
}

output "dataproc_sa_email" {
  value = google_service_account.dataproc_etl.email
}

output "etl_artifacts_bucket" {
  value = google_storage_bucket.etl_artifacts.name
}
