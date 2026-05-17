from __future__ import annotations

import json
import unittest

import pandas as pd

from deluxe_neo4j_cdc.cdc import reduce_cdc_to_current
from deluxe_neo4j_cdc.projection import build_projection_bundle


class CDCProjectionTests(unittest.TestCase):
    def test_reduce_cdc_to_current_keeps_latest_delete_state(self) -> None:
        changelog = pd.DataFrame(
            [
                {
                    "op": "INSERT",
                    "source_ts": "2026-05-05T00:00:00",
                    "pk": {"id": 1},
                    "after": {"id": 1, "username": "A"},
                    "before": None,
                },
                {
                    "op": "DELETE",
                    "source_ts": "2026-05-05T01:00:00",
                    "pk": {"id": 1},
                    "after": None,
                    "before": {"id": 1, "username": "A"},
                },
            ]
        )

        current = reduce_cdc_to_current(changelog, table_name="core.users")

        self.assertEqual(len(current), 1)
        self.assertEqual(current.loc[0, "id"], 1)
        self.assertTrue(current.loc[0, "source_deleted"])

    def test_projection_builds_purchase_attendance_reservation_and_social_edges(self) -> None:
        frames = {
            "core.users": pd.DataFrame(
                [
                    {"id": 1, "username": "Ana", "telegram_id": 101, "source_deleted": False},
                    {"id": 2, "username": "Luis", "telegram_id": 102, "source_deleted": False},
                ]
            ),
            "core.events": pd.DataFrame(
                [{"id": 10, "name": "Deluxe Night", "event_date": "2026-05-10", "event_state_id": 2, "source_deleted": False}]
            ),
            "core.dico_tables": pd.DataFrame(
                [{"id": 20, "number": 1, "table_type_name": "vip", "capacity": 6, "source_deleted": False}]
            ),
            "core.type_tickets": pd.DataFrame(
                [{"id": 30, "event_id": 10, "ticket_tier": "vip", "price": 100000, "source_deleted": False}]
            ),
            "core.table_prices": pd.DataFrame(
                [{"table_id": 20, "event_id": 10, "price": 300000, "source_deleted": False}]
            ),
            "transactions.orders": pd.DataFrame(
                [
                    {"id": 100, "user_id": 1, "status": "approved", "updated_at": "2026-05-05T10:00:00", "source_deleted": False},
                    {"id": 101, "user_id": 2, "status": "approved", "updated_at": "2026-05-05T10:05:00", "source_deleted": False},
                ]
            ),
            "transactions.order_details": pd.DataFrame(
                [
                    {"id": 200, "order_id": 100, "ticket_id": 300, "unit_price": 100000, "discount": 0, "source_deleted": False},
                    {"id": 201, "order_id": 101, "ticket_id": 301, "unit_price": 100000, "discount": 0, "source_deleted": False},
                ]
            ),
            "transactions.tickets": pd.DataFrame(
                [
                    {"id": 300, "user_id": 1, "type_ticket_id": 30, "ticket_state_id": 2, "created_at": "2026-05-05T09:00:00", "updated_at": "2026-05-10T23:10:00", "source_deleted": False},
                    {"id": 301, "user_id": 2, "type_ticket_id": 30, "ticket_state_id": 2, "created_at": "2026-05-05T09:01:00", "updated_at": "2026-05-10T23:12:00", "source_deleted": False},
                    {"id": 302, "user_id": 1, "type_ticket_id": 30, "ticket_state_id": 3, "created_at": "2026-05-05T09:02:00", "updated_at": "2026-05-10T23:12:00", "source_deleted": False},
                ]
            ),
            "transactions.reservations": pd.DataFrame(
                [
                    {"id": 400, "reservation_state_id": 2, "user_id": 1, "table_id": 20, "event_id": 10, "reserved_at": "2026-05-05T11:00:00", "expires_at": "2026-05-10T23:00:00", "source_deleted": False},
                    {"id": 401, "reservation_state_id": 2, "user_id": 2, "table_id": 20, "event_id": 10, "reserved_at": "2026-05-05T11:05:00", "expires_at": "2026-05-10T23:00:00", "source_deleted": False},
                    {"id": 402, "reservation_state_id": 3, "user_id": 2, "table_id": 20, "event_id": 10, "reserved_at": "2026-05-05T11:05:00", "expires_at": "2026-05-10T23:00:00", "source_deleted": False},
                ]
            ),
            "transactions.payments": pd.DataFrame(
                [
                    {"id": 500, "order_id": 100, "status": "verified", "created_at": "2026-05-05T10:01:00", "source_deleted": False},
                    {"id": 501, "order_id": 101, "status": "verified", "created_at": "2026-05-05T10:06:00", "source_deleted": False},
                ]
            ),
            "catalog.ticket_states": pd.DataFrame(
                [
                    {"id": 2, "name": "used"},
                    {"id": 3, "name": "cancelled"},
                ]
            ),
            "catalog.reservation_states": pd.DataFrame(
                [
                    {"id": 2, "name": "confirmed"},
                    {"id": 3, "name": "cancelled"},
                ]
            ),
        }

        bundle = build_projection_bundle(frames)

        self.assertEqual(sorted(bundle.ticket_purchase_edge_current["ticket_id"].tolist()), [300, 301])
        self.assertEqual(sorted(bundle.attendance_edge_current["ticket_id"].tolist()), [300, 301])
        self.assertEqual(sorted(bundle.reservation_edge_current["reservation_id"].tolist()), [400, 401])
        self.assertEqual(len(bundle.social_tie_edge_current), 1)
        tie = bundle.social_tie_edge_current.iloc[0]
        self.assertEqual(tie["shared_attendances"], 1)
        self.assertEqual(tie["shared_purchases"], 1)
        self.assertEqual(tie["shared_reservations"], 1)
        self.assertEqual(tie["tie_strength"], 2.0)

    def test_optional_analytic_columns_do_not_break_projection(self) -> None:
        frames = {
            "core.users": pd.DataFrame([{"id": 1, "username": "Ana", "source_deleted": False}]),
            "core.events": pd.DataFrame([{"id": 10, "name": "Event", "event_state_id": 2, "source_deleted": False}]),
            "core.dico_tables": pd.DataFrame([{"id": 20, "number": 1, "capacity": 6, "source_deleted": False}]),
        }

        bundle = build_projection_bundle(frames)

        self.assertIn("vip_affinity", bundle.user_node_current.columns)
        self.assertIn("expected_demand_level", bundle.event_node_current.columns)
        self.assertIn("vip_suitability", bundle.table_node_current.columns)
        self.assertTrue(bundle.ticket_purchase_edge_current.empty)

    def test_projection_records_replace_missing_numeric_latent_fields_with_none(self) -> None:
        frames = {
            "core.users": pd.DataFrame([{"id": 1, "username": "Ana", "telegram_id": 101, "source_deleted": False}]),
        }

        bundle = build_projection_bundle(frames)
        user_record = bundle.as_records()["user_node_current"][0]

        self.assertIsNone(user_record["vip_affinity"])
        self.assertIsNone(user_record["invite_power"])
        self.assertIsNone(user_record["newcomer_affinity"])
        self.assertIsNone(user_record["mixing_score"])
        json.dumps(user_record, allow_nan=False)


if __name__ == "__main__":
    unittest.main()
