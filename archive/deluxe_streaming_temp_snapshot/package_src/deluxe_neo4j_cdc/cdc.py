from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

import pandas as pd

CDC_REQUIRED_TABLES = (
    "core.users",
    "core.events",
    "core.dico_tables",
    "core.type_tickets",
    "core.table_prices",
    "transactions.orders",
    "transactions.order_details",
    "transactions.tickets",
    "transactions.reservations",
    "transactions.payments",
)

LOOKUP_TABLES = (
    "catalog.ticket_states",
    "catalog.reservation_states",
    "catalog.event_states",
    "catalog.table_types",
    "catalog.payment_methods",
)


@dataclass(frozen=True)
class TableSpec:
    name: str
    primary_key: tuple[str, ...]


TABLE_SPECS: dict[str, TableSpec] = {
    "core.users": TableSpec("core.users", ("id",)),
    "core.events": TableSpec("core.events", ("id",)),
    "core.dico_tables": TableSpec("core.dico_tables", ("id",)),
    "core.type_tickets": TableSpec("core.type_tickets", ("id",)),
    "core.table_prices": TableSpec("core.table_prices", ("table_id", "event_id")),
    "transactions.orders": TableSpec("transactions.orders", ("id",)),
    "transactions.order_details": TableSpec("transactions.order_details", ("id",)),
    "transactions.tickets": TableSpec("transactions.tickets", ("id",)),
    "transactions.reservations": TableSpec("transactions.reservations", ("id",)),
    "transactions.payments": TableSpec("transactions.payments", ("id",)),
    "catalog.ticket_states": TableSpec("catalog.ticket_states", ("id",)),
    "catalog.reservation_states": TableSpec("catalog.reservation_states", ("id",)),
    "catalog.event_states": TableSpec("catalog.event_states", ("id",)),
    "catalog.table_types": TableSpec("catalog.table_types", ("id",)),
    "catalog.payment_methods": TableSpec("catalog.payment_methods", ("id",)),
}

TABLE_ALIASES = {
    "users": "core.users",
    "events": "core.events",
    "dico_tables": "core.dico_tables",
    "tables": "core.dico_tables",
    "type_tickets": "core.type_tickets",
    "table_prices": "core.table_prices",
    "orders": "transactions.orders",
    "order_details": "transactions.order_details",
    "tickets": "transactions.tickets",
    "reservations": "transactions.reservations",
    "payments": "transactions.payments",
    "ticket_states": "catalog.ticket_states",
    "reservation_states": "catalog.reservation_states",
    "event_states": "catalog.event_states",
    "table_types": "catalog.table_types",
    "payment_methods": "catalog.payment_methods",
}


def resolve_table_name(name: str) -> str:
    return TABLE_ALIASES.get(name, name)


def _json_or_mapping(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if pd.isna(value):
        return {}
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return {}
        loaded = json.loads(stripped)
        if isinstance(loaded, dict):
            return loaded
    raise TypeError(f"Unsupported CDC payload type: {type(value)!r}")


def _normalize_op(op: Any) -> str:
    if op is None:
        return ""
    normalized = str(op).strip().upper()
    mapping = {
        "C": "INSERT",
        "I": "INSERT",
        "INSERT": "INSERT",
        "R": "INSERT",
        "U": "UPDATE",
        "UPDATE": "UPDATE",
        "D": "DELETE",
        "DELETE": "DELETE",
    }
    return mapping.get(normalized, normalized)


def _pk_tuple(row: Mapping[str, Any], primary_key: Iterable[str]) -> tuple[Any, ...]:
    return tuple(row.get(col) for col in primary_key)


def reduce_cdc_to_current(
    changelog: pd.DataFrame,
    *,
    table_name: str | None = None,
    primary_key: Iterable[str] | None = None,
) -> pd.DataFrame:
    if changelog.empty:
        return pd.DataFrame()

    resolved_table = resolve_table_name(table_name) if table_name else None
    if primary_key is None:
        if not resolved_table or resolved_table not in TABLE_SPECS:
            raise ValueError("A primary key or known table_name is required for CDC reduction.")
        primary_key = TABLE_SPECS[resolved_table].primary_key

    working = changelog.copy()
    working["op"] = working["op"].map(_normalize_op)
    working["source_ts"] = pd.to_datetime(working["source_ts"], errors="coerce")
    working["pk"] = working.get("pk", None).map(_json_or_mapping if "pk" in working else lambda _: {})
    working["after"] = working.get("after", None).map(_json_or_mapping if "after" in working else lambda _: {})
    working["before"] = working.get("before", None).map(_json_or_mapping if "before" in working else lambda _: {})

    records: list[dict[str, Any]] = []
    for row in working.to_dict(orient="records"):
        op = row["op"]
        image = dict(row["after"] or {})
        if op == "DELETE":
            image = dict(row["before"] or {})

        pk_values = dict(row["pk"] or {})
        if not pk_values:
            pk_values = {col: image.get(col) for col in primary_key}

        image.update(pk_values)
        image["source_deleted"] = op == "DELETE"
        image["_op"] = op
        image["_source_ts"] = row["source_ts"]
        records.append(image)

    current = pd.DataFrame(records)
    current["_pk_tuple"] = current.apply(lambda rec: _pk_tuple(rec, primary_key), axis=1)
    current = current.sort_values(["_source_ts"]).drop_duplicates("_pk_tuple", keep="last")
    current = current.drop(columns=["_pk_tuple"]).reset_index(drop=True)
    return current


def reduce_streams_to_current(streams: Mapping[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    current_frames: dict[str, pd.DataFrame] = {}
    for raw_name, frame in streams.items():
        resolved_name = resolve_table_name(raw_name)
        current_frames[resolved_name] = reduce_cdc_to_current(frame, table_name=resolved_name)
    return current_frames
