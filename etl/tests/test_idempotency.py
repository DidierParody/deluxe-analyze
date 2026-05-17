import pytest

pytestmark = pytest.mark.skip(
    reason=(
        "Integration test requiring Neo4j — run locally with Docker: "
        "pip install testcontainers[neo4j] && pytest etl/tests/test_idempotency.py"
    )
)


def test_double_ingest_same_node_count():
    """Running ETL twice must not create duplicate nodes in Neo4j."""
    # TODO: spin up testcontainers-neo4j, run normalize_csv + Neo4jWriter twice,
    # assert MATCH (n:Usuario) RETURN count(n) same both times.
    pass


def test_double_ingest_same_edge_count():
    """Running ETL twice must not create duplicate CONOCE_A edges."""
    pass
