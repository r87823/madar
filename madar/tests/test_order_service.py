import types
import unittest
from datetime import datetime

from madar.services import order_service


class OrderServiceTest(unittest.TestCase):
    def test_create_draft_uses_user_branch_and_safe_response(self):
        fake_frappe = FakeFrappe()

        result = order_service.create_draft(
            user="branch.user@example.com",
            customer_name="عميل تجريبي",
            customer_phone="0500000000",
            notes="ملاحظة",
            frappe_module=fake_frappe,
        )

        self.assertEqual(result["ok"], True)
        self.assertEqual(result["data"]["customer_name"], "عميل تجريبي")
        self.assertEqual(result["data"]["order_status"], "draft")
        self.assertEqual(result["data"]["branch"], "Main Branch")
        self.assertEqual(result["data"]["assigned_branch"], "Main Branch")
        self.assertEqual(result["data"]["created_by_user"], "branch.user@example.com")
        self.assertNotIn("password", result["data"])
        self.assertEqual(fake_frappe.orders[0]["doctype"], "Madar Order")
        self.assertEqual(fake_frappe.audit_events[-1]["action"], "create_draft")

    def test_create_draft_requires_orders_create_permission(self):
        fake_frappe = FakeFrappe(roles=["Madar Employee"])

        result = order_service.create_draft(
            user="employee.test@example.com",
            customer_name="No Permission",
            customer_phone="0500000000",
            notes="",
            frappe_module=fake_frappe,
        )

        self.assertEqual(result["ok"], False)
        self.assertEqual(result["error"]["code"], "PERMISSION_DENIED")
        self.assertEqual(fake_frappe.orders, [])

    def test_list_orders_is_limited_to_branch_scope(self):
        fake_frappe = FakeFrappe(
            orders=[
                _order("MADAR-ORD-1", "Main Branch", "branch.user@example.com"),
                _order("MADAR-ORD-2", "HQ", "accountant.test@example.com"),
            ]
        )

        result = order_service.list_orders(
            user="branch.user@example.com",
            frappe_module=fake_frappe,
        )

        self.assertEqual(result["ok"], True)
        self.assertEqual([item["name"] for item in result["data"]["items"]], ["MADAR-ORD-1"])

    def test_full_access_user_can_list_all_orders(self):
        fake_frappe = FakeFrappe(
            roles=["Madar Admin"],
            employee={"name": "EMP-ADM", "employee_name": "Admin", "branch": None, "department": None},
            orders=[
                _order("MADAR-ORD-1", "Main Branch", "branch.user@example.com"),
                _order("MADAR-ORD-2", "HQ", "accountant.test@example.com"),
            ],
        )

        result = order_service.list_orders(
            user="admin@example.com",
            frappe_module=fake_frappe,
        )

        self.assertEqual(result["ok"], True)
        self.assertEqual([item["name"] for item in result["data"]["items"]], ["MADAR-ORD-2", "MADAR-ORD-1"])

    def test_get_order_denies_out_of_scope_order(self):
        fake_frappe = FakeFrappe(
            orders=[_order("MADAR-ORD-2", "HQ", "accountant.test@example.com")]
        )

        result = order_service.get_order(
            user="branch.user@example.com",
            order_name="MADAR-ORD-2",
            frappe_module=fake_frappe,
        )

        self.assertEqual(result["ok"], False)
        self.assertEqual(result["error"]["code"], "ORDER_NOT_FOUND")

    def test_submit_order_requires_permission_and_transitions_from_draft(self):
        now = datetime(2026, 5, 19, 12, 0, 0)
        fake_frappe = FakeFrappe(now=now, orders=[_order("MADAR-ORD-1", "Main Branch", "branch.user@example.com")])

        result = order_service.submit_order(
            user="branch.user@example.com",
            order_name="MADAR-ORD-1",
            frappe_module=fake_frappe,
        )

        self.assertEqual(result["ok"], True)
        self.assertEqual(result["data"]["order_status"], "submitted")
        self.assertEqual(result["data"]["submitted_at"], str(now))
        self.assertEqual(fake_frappe.audit_events[-1]["action"], "submit_order")

    def test_submit_cancelled_order_is_rejected(self):
        fake_frappe = FakeFrappe(
            orders=[_order("MADAR-ORD-1", "Main Branch", "branch.user@example.com", status="cancelled")]
        )

        result = order_service.submit_order(
            user="branch.user@example.com",
            order_name="MADAR-ORD-1",
            frappe_module=fake_frappe,
        )

        self.assertEqual(result["ok"], False)
        self.assertEqual(result["error"]["code"], "INVALID_ORDER_TRANSITION")

    def test_cancel_draft_order_is_allowed_but_submitted_order_is_rejected(self):
        now = datetime(2026, 5, 19, 13, 0, 0)
        fake_frappe = FakeFrappe(
            now=now,
            orders=[
                _order("MADAR-ORD-1", "Main Branch", "branch.user@example.com"),
                _order("MADAR-ORD-2", "Main Branch", "branch.user@example.com", status="submitted"),
            ],
        )

        cancelled = order_service.cancel_order(
            user="branch.user@example.com",
            order_name="MADAR-ORD-1",
            frappe_module=fake_frappe,
        )
        rejected = order_service.cancel_order(
            user="branch.user@example.com",
            order_name="MADAR-ORD-2",
            frappe_module=fake_frappe,
        )

        self.assertEqual(cancelled["ok"], True)
        self.assertEqual(cancelled["data"]["order_status"], "cancelled")
        self.assertEqual(cancelled["data"]["cancelled_at"], str(now))
        self.assertEqual(rejected["ok"], False)
        self.assertEqual(rejected["error"]["code"], "INVALID_ORDER_TRANSITION")


def _order(name, branch, created_by_user, status="draft"):
    return {
        "doctype": "Madar Order",
        "name": name,
        "customer_name": f"Customer {name}",
        "customer_phone": "0500000000",
        "branch": branch,
        "assigned_branch": branch,
        "order_status": status,
        "created_by_user": created_by_user,
        "notes": "",
        "submitted_at": None,
        "cancelled_at": None,
        "creation": name,
        "modified": name,
        "password": "hidden",
    }


class FakeMeta:
    def __init__(self, fields):
        self._fields = set(fields)

    def has_field(self, fieldname):
        return fieldname in self._fields


class FakeOrderDoc:
    def __init__(self, fake_frappe, values):
        self._fake_frappe = fake_frappe
        self._values = values
        for key, value in values.items():
            setattr(self, key, value)

    def insert(self, ignore_permissions=False):
        if not getattr(self, "name", None):
            self.name = f"MADAR-ORD-{len(self._fake_frappe.orders) + 1}"
        self._sync_values()
        self._fake_frappe.orders.append(self._values)
        return self

    def save(self, ignore_permissions=False):
        self._sync_values()
        return self

    def add_comment(self, comment_type, text):
        self._fake_frappe.audit_events.append(
            {
                "order": self.name,
                "action": text.split()[0],
                "comment_type": comment_type,
            }
        )

    def _sync_values(self):
        for key, value in vars(self).items():
            if not key.startswith("_"):
                self._values[key] = value


class FakeFrappe:
    def __init__(self, *, roles=None, employee=None, orders=None, now=None):
        self.roles = roles or ["Madar Employee", "Madar Branch User"]
        self.employee = employee or {
            "name": "EMP-BRANCH",
            "employee_name": "Branch User",
            "branch": "Main Branch",
            "department": "Branch Operations",
        }
        self.orders = list(orders or [])
        self.audit_events = []
        self.db = types.SimpleNamespace(commit=lambda: None)
        self.utils = types.SimpleNamespace(now_datetime=lambda: now or datetime(2026, 5, 19, 9, 0, 0))

    def get_roles(self, user):
        return list(self.roles)

    def get_meta(self, doctype):
        if doctype == "Employee":
            return FakeMeta(["user_id", "employee_name", "branch", "department"])
        if doctype == "Madar Order":
            return FakeMeta(["customer_name", "customer_phone", "branch", "assigned_branch"])
        raise RuntimeError(f"{doctype} unavailable")

    def get_all(self, doctype, filters=None, fields=None, order_by=None, limit=20):
        if doctype == "Employee":
            if not self.employee:
                return []
            return [types.SimpleNamespace(**{field: self.employee.get(field) for field in fields})]
        if doctype == "Madar Order":
            rows = list(self.orders)
            if filters:
                for key, value in filters.items():
                    if isinstance(value, list) and value[0] == "in":
                        rows = [row for row in rows if row.get(key) in value[1]]
                    else:
                        rows = [row for row in rows if row.get(key) == value]
            rows.sort(key=lambda row: row.get("modified") or row.get("name"), reverse=True)
            return [types.SimpleNamespace(**{field: row.get(field) for field in fields}) for row in rows[:limit]]
        return []

    def get_doc(self, doctype_or_values, name=None):
        if isinstance(doctype_or_values, dict):
            return FakeOrderDoc(self, dict(doctype_or_values))
        for row in self.orders:
            if row.get("doctype") == doctype_or_values and row.get("name") == name:
                return FakeOrderDoc(self, row)
        raise KeyError(name)


if __name__ == "__main__":
    unittest.main()
