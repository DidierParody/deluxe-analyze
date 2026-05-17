from .cdc import CDC_REQUIRED_TABLES, LOOKUP_TABLES, reduce_cdc_to_current, reduce_streams_to_current
from .projection import ProjectionBundle, build_projection_bundle

try:
    from .neo4j_sync import Neo4jProjector
except ModuleNotFoundError:  # pragma: no cover - optional dependency in Spark runtime
    Neo4jProjector = None

__all__ = [
    "CDC_REQUIRED_TABLES",
    "LOOKUP_TABLES",
    "Neo4jProjector",
    "ProjectionBundle",
    "build_projection_bundle",
    "reduce_cdc_to_current",
    "reduce_streams_to_current",
]
