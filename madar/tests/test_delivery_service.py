import types
import unittest
from datetime import datetime

from madar.services import delivery_service


class DeliveryServiceTest(unittest.TestCase):
    def test_production_ready_sets_ready_for_dispatch_once(self):
        fake_frappe = FakeFrappe(
            roles=["Madar Admin"],
            orders=[
                _order(
                    "MADAR-ORD-1",
                    production_status="ready",
                    delivery_status="not_ready",
                )
            ],
        )

        first = delivery_service.sync_delivery_readiness(
            "MADAR-ORD-1",
            frappe_module=fake_frappe,
        )
        fake_frappe.now = datetime(2026, 5, 19, 13, 0, 0)
        second = delivery_service.sync_delivery_readiness(
            "MADAR-ORD-1",
            frappe_module=fake_frappe,
        )

        self.assertEqual(first["data"]["delivery_status"], "ready_for_dispatch")
        self.assertEqual(second["data"]["ready_for_dispatch_at"], "2026-05-19 12:00:00")
        self.assertEqual(fake_frappe.orders[0]["ready_for_dispatch_at"], datetime(2026, 5, 19, 12, 0, 0))

    def test_non_ready_production_sets_not_ready(self):
        fake_frappe = FakeFrappe(
            roles=["Madar Admin"],
            orders=[
                _order(
                    "MADAR-ORD-1",
                    production_status="in_progress",
                    delivery_status="ready_for_dispatch",
                    ready_for_dispatch_at=datetime(2026, 5, 19, 12, 0, 0),
                )
            ],
        )

        result = delivery_service.sync_delivery_readiness(
            "MADAR-ORD-1",
            frappe_module=fake_frappe,
        )

        self.assertEqual(result["data"]["delivery_status"], "not_ready")
        self.assertIsNone(result["data"]["ready_for_dispatch_at"])

    def test_branch_pickup_requires_destination_branch(self):
        fake_frappe = FakeFrappe(
            roles=["Madar Driver"],
            orders=[
                _order(
                    "MADAR-ORD-1",
                    production_status="ready",
                    delivery_status="ready_for_dispatch",
                    destination_branch="",
                )
            ],
        )

        result = delivery_service.mark_dispatched_to_branch(
            "driver.test@example.com",
            "MADAR-ORD-1",
            frappe_module=fake_frappe,
        )

        self.assertEqual(result["ok"], False)
        self.assertEqual(result["error"]["code"], "DESTINATION_BRANCH_REQUIRED")

    def test_branch_pickup_transition_sequence(self):
        fake_frappe = FakeFrappe(
            roles=["Madar Admin"],
            orders=[
                _order(
                    "MADAR-ORD-1",
                    production_status="ready",
                    delivery_status="ready_for_dispatch",
                )
            ],
        )

        dispatched = delivery_service.mark_dispatched_to_branch(
            "Administrator",
            "MADAR-ORD-1",
            frappe_module=fake_frappe,
        )
        received = delivery_service.mark_received_at_branch(
            "Administrator",
            "MADAR-ORD-1",
            frappe_module=fake_frappe,
        )
        pickup_ready = delivery_service.mark_ready_for_customer_pickup(
            "Administrator",
            "MADAR-ORD-1",
            frappe_module=fake_frappe,
        )
        picked_up = delivery_service.mark_customer_picked_up(
            "Administrator",
            "MADAR-ORD-1",
            frappe_module=fake_frappe,
        )

        self.assertEqual(dispatched["data"]["delivery_status"], "dispatched_to_branch")
        self.assertEqual(received["data"]["delivery_status"], "received_at_branch")
        self.assertEqual(pickup_ready["data"]["delivery_status"], "ready_for_customer_pickup")
        self.assertEqual(picked_up["data"]["delivery_status"], "customer_picked_up")
        self.assertEqual(fake_frappe.created_erp_delivery_notes, [])

    def test_customer_delivery_transition_sequence_and_failed_delivery(self):
        delivered_frappe = FakeFrappe(
            roles=["Madar Driver"],
            orders=[
                _order(
                    "MADAR-ORD-1",
                    fulfillment_method="customer_delivery",
                    destination_branch="",
                    production_status="ready",
                    delivery_status="ready_for_dispatch",
                )
            ],
        )
        failed_frappe = FakeFrappe(
            roles=["Madar Driver"],
            orders=[
                _order(
                    "MADAR-ORD-2",
                    fulfillment_method="customer_delivery",
                    destination_branch="",
                    production_status="ready",
                    delivery_status="ready_for_dispatch",
                )
            ],
        )

        dispatched = delivery_service.mark_dispatched_to_customer(
            "driver.test@example.com",
            "MADAR-ORD-1",
            frappe_module=delivered_frappe,
        )
        delivered = delivery_service.mark_delivered_to_customer(
            "driver.test@example.com",
            "MADAR-ORD-1",
            frappe_module=delivered_frappe,
        )
        failed_without_reason = delivery_service.mark_failed_delivery(
            "driver.test@example.com",
            "MADAR-ORD-2",
            "",
            frappe_module=failed_frappe,
        )
        delivery_service.mark_dispatched_to_customer(
            "driver.test@example.com",
            "MADAR-ORD-2",
            frappe_module=failed_frappe,
        )
        failed = delivery_service.mark_failed_delivery(
            "driver.test@example.com",
            "MADAR-ORD-2",
            "Customer unavailable",
            frappe_module=failed_frappe,
        )

        self.assertEqual(dispatched["data"]["delivery_status"], "dispatched_to_customer")
        self.assertEqual(delivered["data"]["delivery_status"], "delivered_to_customer")
        self.assertEqual(failed_without_reason["error"]["code"], "REASON_REQUIRED")
        self.assertEqual(failed["data"]["delivery_status"], "failed_delivery")
        self.assertEqual(failed["data"]["failed_delivery_reason"], "Customer unavailable")

    def test_invalid_transition_is_rejected(self):
        fake_frappe = FakeFrappe(
            roles=["Madar Driver"],
            orders=[
                _order(
                    "MADAR-ORD-1",
                    fulfillment_method="customer_delivery",
                    destination_branch="",
                    delivery_status="not_ready",
                )
            ],
        )

        result = delivery_service.mark_dispatched_to_customer(
            "driver.test@example.com",
            "MADAR-ORD-1",
            frappe_module=fake_frappe,
        )

        self.assertEqual(result["ok"], False)
        self.assertEqual(result["error"]["code"], "ORDER_NOT_READY_FOR_DISPATCH")

    def test_branch_scope_enforced_for_branch_handoff(self):
        fake_frappe = FakeFrappe(
            roles=["Madar Branch User"],
            employee={
                "name": "EMP-HQ",
                "employee_name": "HQ User",
                "branch": "HQ",
                "department": "Branch Operations",
            },
            orders=[
                _order(
                    "MADAR-ORD-1",
                    destination_branch="Main Branch",
                    delivery_status="dispatched_to_branch",
                )
            ],
        )

        result = delivery_service.mark_received_at_branch(
            "branch.user@example.com",
            "MADAR-ORD-1",
            frappe_module=fake_frappe,
        )

        self.assertEqual(result["ok"], False)
        self.assertEqual(result["error"]["code"], "OUT_OF_SCOPE")

    def test_delivery_user_can_dispatch_and_branch_user_cannot_dispatch(self):
        delivery_frappe = FakeFrappe(
            roles=["Madar Driver"],
            orders=[_order("MADAR-ORD-1", delivery_status="ready_for_dispatch")],
        )
        branch_frappe = FakeFrappe(
            roles=["Madar Branch User"],
            orders=[_order("MADAR-ORD-2", delivery_status="ready_for_dispatch")],
        )

        allowed = delivery_service.mark_dispatched_to_branch(
            "driver.test@example.com",
            "MADAR-ORD-1",
            frappe_module=delivery_frappe,
        )
        denied = delivery_service.mark_dispatched_to_branch(
            "branch.user@example.com",
            "MADAR-ORD-2",
            frappe_module=branch_frappe,
        )

        self.assertEqual(allowed["ok"], True)
        self.assertEqual(denied["error"]["code"], "PERMISSION_DENIED")

    def test_dispatch_queue_lists_ready_and_active_delivery_orders(self):
        fake_frappe = FakeFrappe(
            roles=["Madar Driver"],
            orders=[
                _order("MADAR-ORD-1", delivery_status="ready_for_dispatch"),
                _order("MADAR-ORD-2", delivery_status="customer_picked_up"),
                _order("MADAR-ORD-3", fulfillment_method="customer_delivery", delivery_status="dispatched_to_customer"),
            ],
        )

        result = delivery_service.list_dispatch_queue(
            "driver.test@example.com",
            frappe_module=fake_frappe,
        )

        self.assertEqual(result["ok"], True)
        self.assertEqual([item["name"] for item in result["data"]["items"]], ["MADAR-ORD-3", "MADAR-ORD-1"])


def _order(
    name,
    *,
    fulfillment_method="branch_pickup",
    destination_branch="Main Branch",
    production_status="ready",
    delivery_status="not_ready",
    ready_for_dispatch_at=None,
):
    return {
        "doctype": "Madar Order",
        "name": name,
        "customer_name": f"Customer {name}",
        "customer_phone": "0500000000",
        "branch": destination_branch or "Main Branch",
        "assigned_branch": destination_branch or "Main Branch",
        "order_status": "approved",
        "production_status": production_status,
        "fulfillment_method": fulfillment_method,
        "destination_branch": destination_branch,
        "delivery_status": delivery_status,
        "ready_for_dispatch_at": ready_for_dispatch_at,
        "dispatched_at": None,
        "received_at_branch_at": None,
        "ready_for_customer_pickup_at": None,
        "customer_picked_up_at": None,
        "delivered_at": None,
        "failed_delivery_at": None,
        "failed_delivery_reason": None,
        "subtotal": 10,
        "items_count": 1,
        "modified": name,
    }


class FakeDoc:
    def __init__(self, fake_frappe, values):
        self._fake_frappe = fake_frappe
        self._values = values
        for key, value in values.items():
            setattr(self, key, value)

    def save(self, ignore_permissions=False):
        for key, value in vars(self).items():
            if not key.startswith("_"):
                self._values[key] = value
        return self

    def add_comment(self, comment_type, text):
        self._fake_frappe.audit_events.append({"comment_type": comment_type, "text": text})


class FakeMeta:
    def has_field(self, field):
        return True


class FakeFrappe:
    def __init__(self, *, roles=None, employee=None, orders=None):
        self.roles = roles or ["Madar Admin"]
        self.employee = employee or {
            "name": "EMP-BRANCH",
            "employee_name": "Branch User",
            "branch": "Main Branch",
            "department": "Branch Operations",
        }
        self.orders = list(orders or [])
        self.now = datetime(2026, 5, 19, 12, 0, 0)
        self.audit_events = []
        self.created_erp_delivery_notes = []
        self.db = types.SimpleNamespace(commit=lambda: None)
        self.utils = types.SimpleNamespace(now_datetime=lambda: self.now)

    def get_roles(self, user):
        return list(self.roles)

    def get_meta(self, doctype):
        if doctype == "Employee":
            return FakeMeta()
        raise KeyError(doctype)

    def get_doc(self, doctype, name):
        if doctype == "Delivery Note":
            self.created_erp_delivery_notes.append(name)
            raise AssertionError("Madar delivery must not create ERPNext Delivery Note")
        for row in self.orders:
            if row.get("doctype") == doctype and row.get("name") == name:
                return FakeDoc(self, row)
        raise KeyError(name)

    def get_all(self, doctype, filters=None, fields=None, order_by=None, limit=20):
        if doctype == "Employee":
            rows = [self.employee] if self.employee else []
        elif doctype == "Madar Order":
            rows = list(self.orders)
        else:
            rows = []
        rows = self._filter_rows(rows, filters)
        if order_by:
            rows.sort(key=lambda row: row.get("modified") or row.get("name"), reverse="desc" in order_by)
        return [types.SimpleNamespace(**{field: row.get(field) for field in fields}) for row in rows[:limit]]

    def _filter_rows(self, rows, filters):
        filtered = list(rows)
        for key, value in (filters or {}).items():
            if isinstance(value, list) and value[0] == "in":
                filtered = [row for row in filtered if row.get(key) in value[1]]
            elif isinstance(value, list) and value[0] == "not in":
                filtered = [row for row in filtered if row.get(key) not in value[1]]
            else:
                filtered = [row for row in filtered if row.get(key) == value]
        return filtered


if __name__ == "__main__":
    unittest.main()
