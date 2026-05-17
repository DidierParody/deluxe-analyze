from __future__ import annotations

import uuid
from typing import Iterable

import pandas as pd
from neo4j import Driver

from .projection import ProjectionBundle


def _frame_to_records(frame: pd.DataFrame) -> list[dict]:
    if frame.empty:
        return []
    records = frame.to_dict(orient="records")
    cleaned_records: list[dict] = []
    for row in records:
        cleaned_row: dict = {}
        for key, value in row.items():
            try:
                cleaned_row[key] = None if pd.isna(value) else value
            except TypeError:
                cleaned_row[key] = value
        cleaned_records.append(cleaned_row)
    return cleaned_records


def _chunked(rows: list[dict], size: int) -> Iterable[list[dict]]:
    for start in range(0, len(rows), size):
        yield rows[start : start + size]


class Neo4jProjector:
    SCHEMA_QUERIES = (
        "CREATE CONSTRAINT usuario_user_id_unique IF NOT EXISTS FOR (u:Usuario) REQUIRE u.user_id IS UNIQUE",
        "CREATE CONSTRAINT evento_event_id_unique IF NOT EXISTS FOR (e:Evento) REQUIRE e.event_id IS UNIQUE",
        "CREATE CONSTRAINT mesa_table_id_unique IF NOT EXISTS FOR (m:Mesa) REQUIRE m.table_id IS UNIQUE",
        "CREATE CONSTRAINT segmento_name_unique IF NOT EXISTS FOR (s:Segmento) REQUIRE s.name IS UNIQUE",
        "CREATE INDEX usuario_telegram_idx IF NOT EXISTS FOR (u:Usuario) ON (u.telegram_id)",
        "CREATE INDEX evento_event_date_idx IF NOT EXISTS FOR (e:Evento) ON (e.event_date)",
    )

    USER_UPSERT = """
    UNWIND $rows AS row
    MERGE (u:Usuario {user_id: toInteger(row.user_id)})
    SET u.telegram_id = CASE WHEN row.telegram_id IS NULL THEN NULL ELSE toInteger(row.telegram_id) END,
        u.username = row.username,
        u.social_role = row.social_role,
        u.social_group_id = row.social_group_id,
        u.secondary_group_id = row.secondary_group_id,
        u.attendance_level = row.attendance_level,
        u.vip_affinity = CASE WHEN row.vip_affinity IS NULL THEN NULL ELSE toFloat(row.vip_affinity) END,
        u.invite_power = CASE WHEN row.invite_power IS NULL THEN NULL ELSE toFloat(row.invite_power) END,
        u.table_preference = row.table_preference,
        u.rfm_seed_segment = row.rfm_seed_segment,
        u.newcomer_affinity = CASE WHEN row.newcomer_affinity IS NULL THEN NULL ELSE toFloat(row.newcomer_affinity) END,
        u.mixing_score = CASE WHEN row.mixing_score IS NULL THEN NULL ELSE toFloat(row.mixing_score) END,
        u.source_deleted = coalesce(row.source_deleted, false)
    """

    EVENT_UPSERT = """
    UNWIND $rows AS row
    MERGE (e:Evento {event_id: toInteger(row.event_id)})
    SET e.name = row.name,
        e.event_type = row.event_type,
        e.expected_demand_level = row.expected_demand_level,
        e.vip_pull = CASE WHEN row.vip_pull IS NULL THEN NULL ELSE toFloat(row.vip_pull) END,
        e.event_date = CASE WHEN row.event_date IS NULL THEN NULL ELSE date(toString(row.event_date)) END,
        e.start_time = CASE WHEN row.start_time IS NULL THEN NULL ELSE localdatetime(toString(row.start_time)) END,
        e.end_time = CASE WHEN row.end_time IS NULL THEN NULL ELSE localdatetime(toString(row.end_time)) END,
        e.event_state_id = CASE WHEN row.event_state_id IS NULL THEN NULL ELSE toInteger(row.event_state_id) END,
        e.source_deleted = coalesce(row.source_deleted, false)
    """

    TABLE_UPSERT = """
    UNWIND $rows AS row
    MERGE (m:Mesa {table_id: toInteger(row.table_id)})
    SET m.number = CASE WHEN row.number IS NULL THEN NULL ELSE toInteger(row.number) END,
        m.table_type = row.table_type,
        m.capacity = CASE WHEN row.capacity IS NULL THEN NULL ELSE toInteger(row.capacity) END,
        m.vip_suitability = CASE WHEN row.vip_suitability IS NULL THEN NULL ELSE toFloat(row.vip_suitability) END,
        m.source_deleted = coalesce(row.source_deleted, false)
    """

    SEGMENT_UPSERT = """
    UNWIND $rows AS row
    MERGE (s:Segmento {name: row.name})
    SET s.projection_run_id = $run_id
    """

    SEGMENT_SWEEP = """
    MATCH (s:Segmento)
    WHERE coalesce(s.projection_run_id, '') <> $run_id
    DETACH DELETE s
    """

    BELONGS_UPSERT = """
    UNWIND $rows AS row
    MATCH (u:Usuario {user_id: toInteger(row.user_id)})
    MATCH (s:Segmento {name: row.segment_name})
    MERGE (u)-[r:PERTENECE_A]->(s)
    SET r.projection_run_id = $run_id
    """

    BELONGS_SWEEP = """
    MATCH (:Usuario)-[r:PERTENECE_A]->(:Segmento)
    WHERE coalesce(r.projection_run_id, '') <> $run_id
    DELETE r
    """

    PURCHASE_UPSERT = """
    UNWIND $rows AS row
    MATCH (u:Usuario {user_id: toInteger(row.user_id)})
    MATCH (e:Evento {event_id: toInteger(row.event_id)})
    MERGE (u)-[r:COMPRO_TICKET_PARA {ticket_id: toInteger(row.ticket_id)}]->(e)
    SET r.type_ticket_id = CASE WHEN row.type_ticket_id IS NULL THEN NULL ELSE toInteger(row.type_ticket_id) END,
        r.ticket_tier = row.ticket_tier,
        r.order_id = CASE WHEN row.order_id IS NULL THEN NULL ELSE toInteger(row.order_id) END,
        r.approved_at = CASE WHEN row.approved_at IS NULL THEN NULL ELSE localdatetime(toString(row.approved_at)) END,
        r.price_paid = CASE WHEN row.price_paid IS NULL THEN NULL ELSE toFloat(row.price_paid) END,
        r.ticket_state_id = CASE WHEN row.ticket_state_id IS NULL THEN NULL ELSE toInteger(row.ticket_state_id) END,
        r.projection_run_id = $run_id
    """

    PURCHASE_SWEEP = """
    MATCH (:Usuario)-[r:COMPRO_TICKET_PARA]->(:Evento)
    WHERE coalesce(r.projection_run_id, '') <> $run_id
    DELETE r
    """

    ATTENDANCE_UPSERT = """
    UNWIND $rows AS row
    MATCH (u:Usuario {user_id: toInteger(row.user_id)})
    MATCH (e:Evento {event_id: toInteger(row.event_id)})
    MERGE (u)-[r:ASISTIO_A {ticket_id: toInteger(row.ticket_id)}]->(e)
    SET r.type_ticket_id = CASE WHEN row.type_ticket_id IS NULL THEN NULL ELSE toInteger(row.type_ticket_id) END,
        r.used_at = CASE WHEN row.used_at IS NULL THEN NULL ELSE localdatetime(toString(row.used_at)) END,
        r.projection_run_id = $run_id
    """

    ATTENDANCE_SWEEP = """
    MATCH (:Usuario)-[r:ASISTIO_A]->(:Evento)
    WHERE coalesce(r.projection_run_id, '') <> $run_id
    DELETE r
    """

    RESERVATION_UPSERT = """
    UNWIND $rows AS row
    MATCH (u:Usuario {user_id: toInteger(row.user_id)})
    MATCH (m:Mesa {table_id: toInteger(row.table_id)})
    MERGE (u)-[r:RESERVO {reservation_id: toInteger(row.reservation_id)}]->(m)
    SET r.event_id = CASE WHEN row.event_id IS NULL THEN NULL ELSE toInteger(row.event_id) END,
        r.table_price = CASE WHEN row.table_price IS NULL THEN NULL ELSE toFloat(row.table_price) END,
        r.reservation_state_id = CASE WHEN row.reservation_state_id IS NULL THEN NULL ELSE toInteger(row.reservation_state_id) END,
        r.reserved_at = CASE WHEN row.reserved_at IS NULL THEN NULL ELSE localdatetime(toString(row.reserved_at)) END,
        r.expires_at = CASE WHEN row.expires_at IS NULL THEN NULL ELSE localdatetime(toString(row.expires_at)) END,
        r.projection_run_id = $run_id
    """

    RESERVATION_SWEEP = """
    MATCH (:Usuario)-[r:RESERVO]->(:Mesa)
    WHERE coalesce(r.projection_run_id, '') <> $run_id
    DELETE r
    """

    SOCIAL_UPSERT = """
    UNWIND $rows AS row
    MATCH (u1:Usuario {user_id: toInteger(row.user_1_id)})
    MATCH (u2:Usuario {user_id: toInteger(row.user_2_id)})
    MERGE (u1)-[r:CONOCE_A]-(u2)
    SET r.shared_attendances = CASE WHEN row.shared_attendances IS NULL THEN 0 ELSE toFloat(row.shared_attendances) END,
        r.shared_purchases = CASE WHEN row.shared_purchases IS NULL THEN 0 ELSE toFloat(row.shared_purchases) END,
        r.shared_reservations = CASE WHEN row.shared_reservations IS NULL THEN 0 ELSE toFloat(row.shared_reservations) END,
        r.tie_strength = CASE WHEN row.tie_strength IS NULL THEN 0 ELSE toFloat(row.tie_strength) END,
        r.first_shared_event = CASE WHEN row.first_shared_event IS NULL THEN NULL ELSE datetime(toString(row.first_shared_event)) END,
        r.last_shared_event = CASE WHEN row.last_shared_event IS NULL THEN NULL ELSE datetime(toString(row.last_shared_event)) END,
        r.projection_run_id = $run_id
    """

    SOCIAL_SWEEP = """
    MATCH (:Usuario)-[r:CONOCE_A]-(:Usuario)
    WHERE coalesce(r.projection_run_id, '') <> $run_id
    DELETE r
    """

    def __init__(self, driver: Driver, *, database: str | None = None, batch_size: int = 500) -> None:
        self.driver = driver
        self.database = database
        self.batch_size = batch_size

    @property
    def _session_kwargs(self) -> dict[str, str]:
        return {"database": self.database} if self.database else {}

    def ensure_schema(self) -> None:
        with self.driver.session(**self._session_kwargs) as session:
            for query in self.SCHEMA_QUERIES:
                session.run(query).consume()

    def apply_projection(self, bundle: ProjectionBundle, *, run_id: str | None = None) -> str:
        projection_run_id = run_id or str(uuid.uuid4())

        self._batched_write(self.USER_UPSERT, bundle.user_node_current)
        self._batched_write(self.EVENT_UPSERT, bundle.event_node_current)
        self._batched_write(self.TABLE_UPSERT, bundle.table_node_current)

        self._sync_full_snapshot(self.PURCHASE_UPSERT, self.PURCHASE_SWEEP, bundle.ticket_purchase_edge_current, projection_run_id)
        self._sync_full_snapshot(self.ATTENDANCE_UPSERT, self.ATTENDANCE_SWEEP, bundle.attendance_edge_current, projection_run_id)
        self._sync_full_snapshot(self.RESERVATION_UPSERT, self.RESERVATION_SWEEP, bundle.reservation_edge_current, projection_run_id)
        self._sync_full_snapshot(self.SOCIAL_UPSERT, self.SOCIAL_SWEEP, bundle.social_tie_edge_current, projection_run_id)

        if bundle.segment_node_current is not None and bundle.belongs_edge_current is not None:
            self._sync_full_snapshot(self.SEGMENT_UPSERT, self.SEGMENT_SWEEP, bundle.segment_node_current, projection_run_id)
            self._sync_full_snapshot(self.BELONGS_UPSERT, self.BELONGS_SWEEP, bundle.belongs_edge_current, projection_run_id)

        return projection_run_id

    def _batched_write(self, query: str, frame: pd.DataFrame, run_id: str | None = None) -> None:
        rows = _frame_to_records(frame)
        if not rows:
            return
        with self.driver.session(**self._session_kwargs) as session:
            for chunk in _chunked(rows, self.batch_size):
                params = {"rows": chunk}
                if run_id is not None:
                    params["run_id"] = run_id
                session.run(query, params).consume()

    def _sync_full_snapshot(self, upsert_query: str, sweep_query: str, frame: pd.DataFrame, run_id: str) -> None:
        self._batched_write(upsert_query, frame, run_id=run_id)
        with self.driver.session(**self._session_kwargs) as session:
            session.run(sweep_query, {"run_id": run_id}).consume()
