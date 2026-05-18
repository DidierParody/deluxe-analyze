#!/bin/bash
# Dataproc cluster initialization action.
# Installs Python packages not bundled in the Dataproc 2.2-debian12 image.
#
# pyspark is pre-installed on Dataproc.
# google-cloud-* SDKs are also pre-installed but we pin versions to avoid
# conflicts.  The etl package source is shipped as etl-deps.zip via
# python_file_uris, but its third-party dependencies must be available
# system-wide so the YARN driver can import them.
set -euxo pipefail

pip install --quiet \
  "neo4j>=5.0,<6.0" \
  "boto3>=1.34" \
  "pyarrow>=15.0" \
  "pydantic-settings>=2.0,<3.0" \
  "pydantic>=2.0,<3.0" \
  "google-cloud-storage>=2.0" \
  "google-cloud-secret-manager>=2.0"
