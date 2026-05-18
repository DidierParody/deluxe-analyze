#!/bin/bash
set -euo pipefail

# Install Java 17
apt-get update -q
apt-get install -y -q openjdk-17-jre-headless wget gnupg

# Add Neo4j 5.x repo
wget -O - https://debian.neo4j.com/neotechnology.gpg.key | gpg --dearmor -o /etc/apt/keyrings/neo4j.gpg
echo 'deb [signed-by=/etc/apt/keyrings/neo4j.gpg] https://debian.neo4j.com stable 5' \
  > /etc/apt/sources.list.d/neo4j.list
apt-get update -q

# Install the latest Neo4j 5.x stable from the repo and hold it to prevent
# silent upgrades between reboots that could break plugin compatibility.
apt-get install -y -q neo4j
apt-mark hold neo4j

# NOTE: The GDS (Graph Data Science) Community plugin is NOT installed here.
# GDS version must be pinned to the exact Neo4j minor version; installing the
# wrong jar prevents Neo4j from starting entirely.  GDS is not required for the
# ETL pipeline (CONOCE_A_CYPHER uses plain Cypher).  Add GDS manually after
# confirming the installed Neo4j version, following the compatibility matrix at:
# https://neo4j.com/docs/graph-data-science/current/installation/neo4j-server/

# Stop Neo4j if systemd already started it before the script could configure it
# (happens on reboot via startup-script-url execution order).
systemctl stop neo4j || true

# Configure Neo4j
NEO4J_CONF=/etc/neo4j/neo4j.conf

# Listen on all interfaces (0.0.0.0 valid for listen, not for advertised)
# Use regex to overwrite any existing value (idempotent across reboots)
sed -i 's/^#\?server\.default_listen_address=.*/server.default_listen_address=0.0.0.0/' "$NEO4J_CONF"

# Advertised address: fetch external IP from GCE metadata
EXTERNAL_IP=$(curl -sf "http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/externalIp" \
  -H "Metadata-Flavor: Google" || hostname -I | awk '{print $1}')
sed -i "s/^#\?server\.default_advertised_address=.*/server.default_advertised_address=${EXTERNAL_IP}/" "$NEO4J_CONF"

# Allow GDS plugin
echo "dbms.security.procedures.unrestricted=gds.*" >> "$NEO4J_CONF"
echo "dbms.security.procedures.allowlist=gds.*" >> "$NEO4J_CONF"

# Read initial password from Secret Manager via metadata
SECRET_ID=$(curl -sf "http://metadata.google.internal/computeMetadata/v1/instance/attributes/neo4j-password-secret" \
  -H "Metadata-Flavor: Google")
NEO4J_PASSWORD=$(gcloud secrets versions access latest --secret="$SECRET_ID" 2>/dev/null || echo "changeme123")

# Enable and start Neo4j
systemctl enable neo4j
systemctl start neo4j

# Wait for Neo4j to be ready
sleep 30

# Set initial password
cypher-shell -u neo4j -p neo4j "ALTER CURRENT USER SET PASSWORD FROM 'neo4j' TO '${NEO4J_PASSWORD}'" || true

echo "Neo4j startup complete"
