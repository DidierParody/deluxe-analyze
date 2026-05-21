"""Neo4j driver singleton + GDS projection lifecycle helper."""
from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Any

from neo4j import Driver, GraphDatabase

from .config import Settings

logger = logging.getLogger(__name__)

_driver: Driver | None = None
_settings = Settings()


def get_driver() -> Driver:
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            _settings.NEO4J_URI,
            auth=(_settings.NEO4J_USERNAME, _settings.NEO4J_PASSWORD),
        )
        _driver.verify_connectivity()
        logger.info("Neo4j driver initialised: %s", _settings.NEO4J_URI)
    return _driver


def close_driver() -> None:
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None


@contextmanager
def session():
    drv = get_driver()
    with drv.session(database=_settings.NEO4J_DATABASE) as s:
        yield s


def run_query(query: str, parameters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Execute a read query and return list of record dicts."""
    with session() as s:
        result = s.run(query, parameters or {})
        return [dict(record) for record in result]


def run_write(query: str, parameters: dict[str, Any] | None = None) -> None:
    """Execute a write/management query and consume."""
    with session() as s:
        s.run(query, parameters or {}).consume()


def ensure_projection() -> None:
    """Create the GDS projection `socialGraph` if it does not exist."""
    graph_name = _settings.GDS_GRAPH_NAME
    exists = run_query(
        "CALL gds.graph.exists($name) YIELD exists RETURN exists",
        {"name": graph_name},
    )
    if exists and exists[0].get("exists"):
        return
    logger.info("Creating GDS projection %s", graph_name)
    run_write(
        """
        CALL gds.graph.project(
          $name, 'Usuario',
          {CONOCE_A: {orientation: 'UNDIRECTED', properties: ['tie_strength']}}
        )
        """,
        {"name": graph_name},
    )


def user_exists(user_id: str) -> bool:
    rows = run_query(
        "MATCH (u:Usuario {id: $id}) RETURN count(u) AS c",
        {"id": user_id},
    )
    return bool(rows and rows[0]["c"] > 0)


def get_username(user_id: str) -> str | None:
    rows = run_query(
        "MATCH (u:Usuario {id: $id}) RETURN u.username AS username LIMIT 1",
        {"id": user_id},
    )
    if rows:
        return rows[0].get("username")
    return None
