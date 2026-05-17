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
apt-get install -y -q neo4j

# Install GDS Community plugin
NEO4J_HOME=/var/lib/neo4j
GDS_VERSION="2.6.5"
GDS_JAR="neo4j-graph-data-science-${GDS_VERSION}.jar"
GDS_URL="https://graphdatascience.ninja/${GDS_JAR}"

wget -q -O "${NEO4J_HOME}/plugins/${GDS_JAR}" "${GDS_URL}"
chown neo4j:neo4j "${NEO4J_HOME}/plugins/${GDS_JAR}"

# Configure Neo4j
NEO4J_CONF=/etc/neo4j/neo4j.conf

# Listen on all interfaces
sed -i 's/#server.default_listen_address=0.0.0.0/server.default_listen_address=0.0.0.0/' "$NEO4J_CONF"
sed -i 's/#server.default_advertised_address=localhost/server.default_advertised_address=0.0.0.0/' "$NEO4J_CONF"

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
