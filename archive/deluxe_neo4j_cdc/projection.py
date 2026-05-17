from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Any, Mapping

import pandas as pd

from .cdc import resolve_table_name


@dataclass
class ProjectionBundle:
    user_node_current: pd.DataFrame
    event_node_current: pd.DataFrame
    table_node_current: pd.DataFrame
    ticket_purchase_edge_current: pd.DataFrame
    attendance_edge_current: pd.DataFrame
    reservation_edge_current: pd.DataFrame
    social_tie_edge_current: pd.DataFrame
    segment_node_current: pd.DataFrame | None = None
    belongs_edge_current: pd.DataFrame | None = None

    def as_records(self) -> dict[str, list[dict[str, Any]]]:
        payloads: dict[str, list[dict[str, Any]]] = {}
        for name, frame in self.__dict__.items():
            if frame is None:
                payloads[name] = []
            else:
                payloads[name] = _frame_to_records(frame)
        return payloads


def _frame_to_records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    if frame.empty:
        return []
    records = frame.to_dict(orient="records")
    cleaned_records: list[dict[str, Any]] = []
    for row in records:
        cleaned_row: dict[str, Any] = {}
        for key, value in row.items():
            try:
                cleaned_row[key] = None if pd.isna(value) else value
            except TypeError:
                cleaned_row[key] = value
        cleaned_records.append(cleaned_row)
    return cleaned_records


def _copy_frame(frames: Mapping[str, pd.DataFrame], *names: str) -> pd.DataFrame:
    for name in names:
        resolved = resolve_table_name(name)
        if resolved in frames:
            return frames[resolved].copy()
    return pd.DataFrame()


def _ensure_columns(frame: pd.DataFrame, defaults: Mapping[str, Any]) -> pd.DataFrame:
    working = frame.copy()
    for column, default in defaults.items():
        if column not in working.columns:
            working[column] = default
    return working


def _rename_first(frame: pd.DataFrame, candidates: Mapping[str, tuple[str, ...]]) -> pd.DataFrame:
    working = frame.copy()
    for target, aliases in candidates.items():
        if target in working.columns:
            continue
        for alias in aliases:
            if alias in working.columns:
                working = working.rename(columns={alias: target})
                break
    return working


def _to_datetime_if_present(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    working = frame.copy()
    for column in columns:
        if column in working.columns:
            working[column] = pd.to_datetime(working[column], errors="coerce")
    return working


def _state_lookup(frame: pd.DataFrame, name_column: str = "name") -> dict[Any, str]:
    if frame.empty or "id" not in frame.columns or name_column not in frame.columns:
        return {}
    lookup = frame[["id", name_column]].dropna().drop_duplicates("id")
    return dict(zip(lookup["id"], lookup[name_column].astype(str).str.lower()))


def _coerce_numeric(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    working = frame.copy()
    for column in columns:
        if column in working.columns:
            working[column] = pd.to_numeric(working[column], errors="coerce")
    return working


def _unique_active(frame: pd.DataFrame, subset: list[str]) -> pd.DataFrame:
    if frame.empty:
        return frame
    working = frame.copy()
    if "source_deleted" in working.columns:
        working = working[~working["source_deleted"].fillna(False)]
    return working.drop_duplicates(subset=subset)


def build_projection_bundle(current_frames: Mapping[str, pd.DataFrame]) -> ProjectionBundle:
    users = _prepare_users(_copy_frame(current_frames, "core.users", "users"))
    events = _prepare_events(_copy_frame(current_frames, "core.events", "events"))
    tables = _prepare_tables(_copy_frame(current_frames, "core.dico_tables", "dico_tables", "tables"))
    type_tickets = _prepare_type_tickets(_copy_frame(current_frames, "core.type_tickets", "type_tickets"))
    table_prices = _prepare_table_prices(_copy_frame(current_frames, "core.table_prices", "table_prices"))
    orders = _prepare_orders(_copy_frame(current_frames, "transactions.orders", "orders"))
    order_details = _prepare_order_details(_copy_frame(current_frames, "transactions.order_details", "order_details"))
    tickets = _prepare_tickets(_copy_frame(current_frames, "transactions.tickets", "tickets"))
    reservations = _prepare_reservations(_copy_frame(current_frames, "transactions.reservations", "reservations"))
    payments = _prepare_payments(_copy_frame(current_frames, "transactions.payments", "payments"))

    ticket_states = _copy_frame(current_frames, "catalog.ticket_states", "ticket_states")
    reservation_states = _copy_frame(current_frames, "catalog.reservation_states", "reservation_states")

    purchase_edges = _build_ticket_purchase_edges(
        tickets=tickets,
        type_tickets=type_tickets,
        order_details=order_details,
        orders=orders,
        payments=payments,
        ticket_states=ticket_states,
    )
    attendance_edges = _build_attendance_edges(
        tickets=tickets,
        type_tickets=type_tickets,
        ticket_states=ticket_states,
    )
    reservation_edges = _build_reservation_edges(
        reservations=reservations,
        tables=tables,
        table_prices=table_prices,
        reservation_states=reservation_states,
    )
    segment_nodes, belongs_edges = _build_optional_segments(users)
    social_edges = _build_social_ties(
        purchases=purchase_edges,
        attendances=attendance_edges,
        reservations=reservation_edges,
        events=events,
    )

    return ProjectionBundle(
        user_node_current=users,
        event_node_current=events,
        table_node_current=tables,
        ticket_purchase_edge_current=purchase_edges,
        attendance_edge_current=attendance_edges,
        reservation_edge_current=reservation_edges,
        social_tie_edge_current=social_edges,
        segment_node_current=segment_nodes,
        belongs_edge_current=belongs_edges,
    )


def _prepare_users(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=["user_id", "source_deleted"])
    working = _rename_first(frame, {"user_id": ("id",)})
    working = _ensure_columns(
        working,
        {
            "telegram_id": None,
            "username": None,
            "social_role": None,
            "social_group_id": None,
            "secondary_group_id": None,
            "attendance_level": None,
            "vip_affinity": None,
            "invite_power": None,
            "table_preference": None,
            "rfm_seed_segment": None,
            "newcomer_affinity": None,
            "mixing_score": None,
            "source_deleted": False,
        },
    )
    return _coerce_numeric(working, ["user_id", "telegram_id", "vip_affinity", "invite_power", "newcomer_affinity", "mixing_score"])


def _prepare_events(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=["event_id", "source_deleted"])
    working = _rename_first(frame, {"event_id": ("id",), "event_state_id": ("event_state",)})
    working = _ensure_columns(
        working,
        {
            "name": None,
            "event_type": None,
            "expected_demand_level": None,
            "vip_pull": None,
            "event_date": None,
            "start_time": None,
            "end_time": None,
            "event_state_id": None,
            "source_deleted": False,
        },
    )
    working = _to_datetime_if_present(working, ["event_date", "start_time", "end_time"])
    working = _coerce_numeric(working, ["event_id", "event_state_id", "vip_pull"])
    return working


def _prepare_tables(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=["table_id", "source_deleted"])
    working = _rename_first(frame, {"table_id": ("id",), "table_type": ("table_type_name",)})
    working = _ensure_columns(
        working,
        {
            "number": None,
            "table_type": None,
            "capacity": None,
            "vip_suitability": None,
            "source_deleted": False,
        },
    )
    return _coerce_numeric(working, ["table_id", "number", "capacity", "vip_suitability"])


def _prepare_type_tickets(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=["type_ticket_id"])
    working = _rename_first(frame, {"type_ticket_id": ("id",)})
    working = _ensure_columns(
        working,
        {
            "event_id": None,
            "ticket_tier": None,
            "name": None,
            "price": None,
            "source_deleted": False,
        },
    )
    working = _coerce_numeric(working, ["type_ticket_id", "event_id", "price"])
    if "ticket_tier" not in working.columns or working["ticket_tier"].isna().all():
        working["ticket_tier"] = working["name"].astype(str).str.lower()
    else:
        working["ticket_tier"] = working["ticket_tier"].astype(str).str.lower()
    return working


def _prepare_table_prices(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=["table_id", "event_id", "price"])
    working = _ensure_columns(frame, {"source_deleted": False})
    return _coerce_numeric(working, ["table_id", "event_id", "price"])


def _prepare_orders(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=["order_id"])
    working = _rename_first(frame, {"order_id": ("id",)})
    working = _ensure_columns(
        working,
        {
            "user_id": None,
            "status": None,
            "updated_at": None,
            "source_deleted": False,
        },
    )
    working = _to_datetime_if_present(working, ["updated_at", "created_at", "ordered_at"])
    working = _coerce_numeric(working, ["order_id", "user_id", "total"])
    return working


def _prepare_order_details(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=["order_detail_id"])
    working = _rename_first(frame, {"order_detail_id": ("id",)})
    working = _ensure_columns(
        working,
        {
            "order_id": None,
            "ticket_id": None,
            "reservation_id": None,
            "type_ticket_id": None,
            "table_id": None,
            "quantity": 1,
            "unit_price": None,
            "discount": 0,
            "source_deleted": False,
        },
    )
    return _coerce_numeric(
        working,
        ["order_detail_id", "order_id", "ticket_id", "reservation_id", "type_ticket_id", "table_id", "quantity", "unit_price", "discount"],
    )


def _prepare_tickets(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=["ticket_id"])
    working = _rename_first(frame, {"ticket_id": ("id",)})
    working = _ensure_columns(
        working,
        {
            "user_id": None,
            "type_ticket_id": None,
            "ticket_state_id": None,
            "created_at": None,
            "updated_at": None,
            "source_deleted": False,
        },
    )
    working = _to_datetime_if_present(working, ["created_at", "updated_at"])
    return _coerce_numeric(working, ["ticket_id", "user_id", "type_ticket_id", "ticket_state_id"])


def _prepare_reservations(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=["reservation_id"])
    working = _rename_first(frame, {"reservation_id": ("id",)})
    working = _ensure_columns(
        working,
        {
            "reservation_state_id": None,
            "user_id": None,
            "table_id": None,
            "event_id": None,
            "reserved_at": None,
            "expires_at": None,
            "source_deleted": False,
        },
    )
    working = _to_datetime_if_present(working, ["reserved_at", "expires_at", "updated_at", "created_at"])
    return _coerce_numeric(working, ["reservation_id", "reservation_state_id", "user_id", "table_id", "event_id"])


def _prepare_payments(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=["payment_id"])
    working = _rename_first(frame, {"payment_id": ("id",)})
    working = _ensure_columns(
        working,
        {
            "order_id": None,
            "status": None,
            "created_at": None,
            "source_deleted": False,
        },
    )
    working = _to_datetime_if_present(working, ["created_at"])
    return _coerce_numeric(working, ["payment_id", "order_id", "payment_method_id", "amount"])


def _build_ticket_purchase_edges(
    *,
    tickets: pd.DataFrame,
    type_tickets: pd.DataFrame,
    order_details: pd.DataFrame,
    orders: pd.DataFrame,
    payments: pd.DataFrame,
    ticket_states: pd.DataFrame,
) -> pd.DataFrame:
    if tickets.empty or type_tickets.empty or order_details.empty or orders.empty:
        return pd.DataFrame(columns=["ticket_id"])

    ticket_state_lookup = _state_lookup(ticket_states)
    active_tickets = _unique_active(tickets, ["ticket_id"]).copy()
    active_details = _unique_active(order_details, ["order_detail_id"]).copy()
    active_orders = _unique_active(orders, ["order_id"]).copy()
    active_type_tickets = _unique_active(type_tickets, ["type_ticket_id"]).copy()
    active_payments = _unique_active(payments, ["payment_id"]).copy()

    verified_payments = active_payments[active_payments["status"].astype(str).str.lower() == "verified"].copy()
    if not verified_payments.empty:
        verified_payments = verified_payments.sort_values("created_at").drop_duplicates("order_id", keep="last")

    merged = (
        active_tickets
        .merge(active_type_tickets[["type_ticket_id", "event_id", "ticket_tier", "price"]], on="type_ticket_id", how="inner")
        .merge(active_details[["order_id", "ticket_id", "unit_price", "discount"]], on="ticket_id", how="inner")
        .merge(
            active_orders[["order_id", "status", "updated_at"]].rename(columns={"updated_at": "approved_at"}),
            on="order_id",
            how="inner",
        )
        .merge(verified_payments[["order_id"]], on="order_id", how="inner")
    )

    merged["ticket_state_name"] = merged["ticket_state_id"].map(ticket_state_lookup).fillna(
        merged["ticket_state_id"].astype(str).str.lower()
    )
    merged = merged[
        (merged["status"].astype(str).str.lower() == "approved")
        & (merged["ticket_state_name"] != "cancelled")
    ].copy()

    if merged.empty:
        return pd.DataFrame(columns=["ticket_id"])

    merged["price_paid"] = merged["unit_price"].fillna(merged["price"]) - merged["discount"].fillna(0)
    result = merged[
        ["user_id", "event_id", "ticket_id", "type_ticket_id", "ticket_tier", "order_id", "approved_at", "price_paid", "ticket_state_id"]
    ].drop_duplicates("ticket_id")
    return result.reset_index(drop=True)


def _build_attendance_edges(
    *,
    tickets: pd.DataFrame,
    type_tickets: pd.DataFrame,
    ticket_states: pd.DataFrame,
) -> pd.DataFrame:
    if tickets.empty or type_tickets.empty:
        return pd.DataFrame(columns=["ticket_id"])

    ticket_state_lookup = _state_lookup(ticket_states)
    active_tickets = _unique_active(tickets, ["ticket_id"]).copy()
    active_type_tickets = _unique_active(type_tickets, ["type_ticket_id"]).copy()

    merged = active_tickets.merge(
        active_type_tickets[["type_ticket_id", "event_id"]],
        on="type_ticket_id",
        how="inner",
    )
    merged["ticket_state_name"] = merged["ticket_state_id"].map(ticket_state_lookup).fillna(
        merged["ticket_state_id"].astype(str).str.lower()
    )
    merged = merged[merged["ticket_state_name"] == "used"].copy()
    if merged.empty:
        return pd.DataFrame(columns=["ticket_id"])

    merged["used_at"] = merged["updated_at"].fillna(merged["created_at"])
    return merged[["user_id", "event_id", "ticket_id", "type_ticket_id", "used_at"]].drop_duplicates("ticket_id").reset_index(drop=True)


def _build_reservation_edges(
    *,
    reservations: pd.DataFrame,
    tables: pd.DataFrame,
    table_prices: pd.DataFrame,
    reservation_states: pd.DataFrame,
) -> pd.DataFrame:
    if reservations.empty or tables.empty:
        return pd.DataFrame(columns=["reservation_id"])

    reservation_state_lookup = _state_lookup(reservation_states)
    active_reservations = _unique_active(reservations, ["reservation_id"]).copy()
    active_tables = _unique_active(tables, ["table_id"]).copy()
    active_prices = _unique_active(table_prices, ["table_id", "event_id"]).copy()

    merged = active_reservations.merge(active_tables[["table_id"]], on="table_id", how="inner")
    if not active_prices.empty:
        merged = merged.merge(
            active_prices[["table_id", "event_id", "price"]],
            on=["table_id", "event_id"],
            how="left",
        )

    merged["reservation_state_name"] = merged["reservation_state_id"].map(reservation_state_lookup).fillna(
        merged["reservation_state_id"].astype(str).str.lower()
    )
    merged = merged[merged["reservation_state_name"].isin({"pending", "confirmed", "completed"})].copy()
    if merged.empty:
        return pd.DataFrame(columns=["reservation_id"])

    merged = merged.rename(columns={"price": "table_price"})
    return merged[
        ["user_id", "table_id", "reservation_id", "event_id", "table_price", "reservation_state_id", "reserved_at", "expires_at"]
    ].drop_duplicates("reservation_id").reset_index(drop=True)


def _build_optional_segments(users: pd.DataFrame) -> tuple[pd.DataFrame | None, pd.DataFrame | None]:
    if users.empty or "rfm_seed_segment" not in users.columns:
        return None, None

    active_users = users[~users["source_deleted"].fillna(False)].copy()
    active_users = active_users[active_users["rfm_seed_segment"].notna()].copy()
    if active_users.empty:
        return None, None

    segment_nodes = pd.DataFrame({"name": sorted(active_users["rfm_seed_segment"].dropna().astype(str).unique())})
    belongs_edges = active_users[["user_id", "rfm_seed_segment"]].rename(columns={"rfm_seed_segment": "segment_name"}).reset_index(drop=True)
    return segment_nodes, belongs_edges


def _pair_counter(edges: pd.DataFrame, event_dates: dict[Any, Any], event_col: str) -> pd.DataFrame:
    if edges.empty or event_col not in edges.columns:
        return pd.DataFrame(columns=["user_1_id", "user_2_id", "shared_count", "first_shared_event", "last_shared_event"])

    deduped = edges[["user_id", event_col]].dropna().drop_duplicates()
    pairs: list[dict[str, Any]] = []
    for event_id, group in deduped.groupby(event_col):
        users = sorted(set(group["user_id"]))
        event_date = event_dates.get(event_id)
        for user_1, user_2 in combinations(users, 2):
            pairs.append(
                {
                    "user_1_id": user_1,
                    "user_2_id": user_2,
                    "event_id": event_id,
                    "event_date": event_date,
                }
            )

    if not pairs:
        return pd.DataFrame(columns=["user_1_id", "user_2_id", "shared_count", "first_shared_event", "last_shared_event"])

    pair_frame = pd.DataFrame(pairs)
    summary = (
        pair_frame.groupby(["user_1_id", "user_2_id"], dropna=False)
        .agg(
            shared_count=("event_id", "nunique"),
            first_shared_event=("event_date", "min"),
            last_shared_event=("event_date", "max"),
        )
        .reset_index()
    )
    return summary


def _build_social_ties(
    *,
    purchases: pd.DataFrame,
    attendances: pd.DataFrame,
    reservations: pd.DataFrame,
    events: pd.DataFrame,
) -> pd.DataFrame:
    event_dates: dict[Any, Any] = {}
    if not events.empty and "event_id" in events.columns and "event_date" in events.columns:
        event_dates = dict(zip(events["event_id"], pd.to_datetime(events["event_date"], errors="coerce")))

    purchase_pairs = _pair_counter(purchases, event_dates, "event_id").rename(columns={"shared_count": "shared_purchases"})
    attendance_pairs = _pair_counter(attendances, event_dates, "event_id").rename(columns={"shared_count": "shared_attendances"})
    reservation_pairs = _pair_counter(reservations, event_dates, "event_id").rename(columns={"shared_count": "shared_reservations"})

    frames = [frame for frame in (purchase_pairs, attendance_pairs, reservation_pairs) if not frame.empty]
    if not frames:
        return pd.DataFrame(columns=["user_1_id", "user_2_id"])

    social = frames[0]
    for frame in frames[1:]:
        social = social.merge(frame, on=["user_1_id", "user_2_id"], how="outer")

    social = _ensure_columns(
        social,
        {
            "shared_purchases": 0,
            "shared_attendances": 0,
            "shared_reservations": 0,
            "first_shared_event_x": pd.NaT,
            "last_shared_event_x": pd.NaT,
            "first_shared_event_y": pd.NaT,
            "last_shared_event_y": pd.NaT,
        },
    )

    first_cols = [col for col in social.columns if col.startswith("first_shared_event")]
    last_cols = [col for col in social.columns if col.startswith("last_shared_event")]
    social["first_shared_event"] = social[first_cols].min(axis=1)
    social["last_shared_event"] = social[last_cols].max(axis=1)
    social["shared_purchases"] = pd.to_numeric(social["shared_purchases"], errors="coerce").fillna(0)
    social["shared_attendances"] = pd.to_numeric(social["shared_attendances"], errors="coerce").fillna(0)
    social["shared_reservations"] = pd.to_numeric(social["shared_reservations"], errors="coerce").fillna(0)
    social["tie_strength"] = (
        social["shared_attendances"] * 1.0
        + social["shared_reservations"] * 0.75
        + social["shared_purchases"] * 0.25
    ).round(3)

    keep = social["tie_strength"] > 0
    social = social.loc[keep, ["user_1_id", "user_2_id", "shared_attendances", "shared_purchases", "shared_reservations", "tie_strength", "first_shared_event", "last_shared_event"]]
    return social.reset_index(drop=True)
