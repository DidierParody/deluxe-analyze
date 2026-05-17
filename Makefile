.PHONY: tf-plan tf-apply etl-test etl-lint dispatcher-lint dispatcher-test upload-etl help

help:
	@echo "Available targets:"
	@echo "  tf-plan         Run terraform plan (requires GCP auth)"
	@echo "  tf-apply        Run terraform apply"
	@echo "  etl-test        Run ETL unit tests"
	@echo "  etl-lint        Run ruff on ETL package"
	@echo "  dispatcher-test Run dispatcher tests"
	@echo "  dispatcher-lint Run ruff on dispatcher"
	@echo "  upload-etl      Upload ETL job to GCS (requires GCS_BUCKET env var)"

tf-plan:
	cd infra && terraform plan -var-file=terraform.tfvars

tf-apply:
	cd infra && terraform apply -var-file=terraform.tfvars

etl-lint:
	ruff check etl/

etl-test:
	cd etl && pip install -e ".[dev]" -q && pytest tests/ -v

dispatcher-lint:
	ruff check dispatcher/

dispatcher-test:
	cd dispatcher && pip install -e ".[dev]" -q && pytest tests/ -v

upload-etl:
	@test -n "$(GCS_BUCKET)" || (echo "Set GCS_BUCKET env var" && exit 1)
	gsutil cp etl/jobs/main.py gs://$(GCS_BUCKET)/jobs/main.py
