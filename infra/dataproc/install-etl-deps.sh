#!/bin/bash
# Dataproc cluster initialization action.
# Installs Python packages not bundled in the Dataproc 2.2-debian12 image.
#
# pydantic-settings is required by etl/config.py (and dispatcher/config.py).
# The etl package itself is shipped as etl-deps.zip via python_file_uris.
set -euxo pipefail

pip install --quiet pydantic-settings==2.* pydantic==2.*
