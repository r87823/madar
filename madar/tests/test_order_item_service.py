import types
import unittest
from datetime import datetime

from madar.services import order_item_service


class OrderItemServiceTest(unittest.TestCase):
    def test_add_item_creates_line_and_recalculates_order_totals(self):
        fake_frappe = FakeFrappe()

        result = order_item_service.add_item(
            user="branch.user@example.com",
            order_name="MADAR-ORD-1",
            item_code="MILK-001",
            qty=2,
            frappe_module=fake_frappe,
        )

        self.assertEqual(result["ok"], True)
        self.assertEqual(result["data"]["order"]["subtotal"], 25.0)
        self.assertEqual(result["data"]["order"]["items_count"], 1)
        self.assertEqual(result["data"]["item"]["line_total"], 25.0)
        self.assertEqual(fake_frappe.order_items[0]["unit_price"], 12.5)
        self.assertEqual(fake_frappe.audit_events[-1]["action"], "add_item")

    def test_update_qty_and_remove_item_recalculate_totals(self):
        fake_frappe = FakeFrappe(
            order_items=[
                _item("LINE-1", "MADAR-ORD-1", "MILK-001", "Milk", 2, 12.5),
                _item("LINE-2", "MADAR-ORD-1", "RICE-001", "Rice", 1, 5),
            ]
        )

        updated = order_item_service.update_item_qty(
            user="branch.user@example.com",
            order_name="MADAR-ORD-1",
            item_name="LINE-1",
            qty=3,
            frappe_module=fake_frappe,
        )
        removed = order_item_service.remove_item(
            user="branch.user@example.com",
            order_name="MADAR-ORD-1",
            item_name="LINE-2",
            frappe_module=fake_frappe,
        )

        self.assertEqual(updated["data"]["order"]["subtotal"], 42.5)
        self.assertEqual(removed["data"]["order"]["subtotal"], 37.5)
        self.assertEqual(removed["data"]["order"]["items_count"], 1)

    def test_submitted_order_rejects_item_mutations(self):
        fake_frappe = FakeFrappe(order_status="submitted")

        result = order_item_service.add_item(
            user="branch.user@example.com",
            order_name="MADAR-ORD-1",
            item_code="MILK-001",
            qty=1,
            frappe_module=fake_frappe,
        )

        self.assertEqual(result["ok"], False)
        self.assertEqual(result["error"]["code"], "ORDER_NOT_EDITABLE")
        self.assertEqual(fake_frappe.order_items, [])

    def test_invalid_quantity_is_rejected(self):
        fake_frappe = FakeFrappe()

        result = order_item_service.add_item(
            user="branch.user@example.com",
            order_name="MADAR-ORD-1",
            item_code="MILK-001",
            qty=0,
            frappe_module=fake_frappe,
        )

        self.assertEqual(result["ok"], False)
        self.assertEqual(result["error"]["code"], "INVALID_QUANTITY")

    def test_out_of_scope_order_is_rejected(self):
        fake_frappe = FakeFrappe(order_branch="HQ")

        result = order_item_service.list_order_items(
            user="branch.user@example.com",
            order_name="MADAR-ORD-1",
            frappe_module=fake_frappe,
        )

        self.assertEqual(result["ok"], False)
        self.assertEqual(result["error"]["code"], "ORDER_NOT_FOUND")


def _order(name="MADAR-ORD-1", branch="Main Branch", status="draft", created_by_user="branch.user@example.com"):
    return {
        "doctype": "Madar Order",
        "name": name,
        "customer_name": "Customer",
        "customer_phone": "050",
        "branch": branch,
        "assigned_branch": branch,
        "order_status": status,
        "created_by_user": created_by_user,
        "notes": "",
        "subtotal": 0,
        "items_count": 0,
        "modified": name,
    }


def _item(name, order_name, item_code, item_name, qty, unit_price):
    return {
        "doctype": "Madar Order Item",
        "name": name,
        "order_name": order_name,
        "item_code": item_code,
        "item_name": item_name,
        "qty": qty,
        "unit_price": unit_price,
        "line_total": qty * unit_price,
        "notes": "",
    }


class FakeOrderDoc:
    def __init__(self, fake_frappe, values):
        self._fake_frappe = fake_frappe
        self._values = values
        for key, value in values.items():
            setattr(self, key, value)

    def save(self, ignore_permissions=False):
        self._sync_values()
        return self

    def add_comment(self, comment_type, text):
        self._fake_frappe.audit_events.append(
            {"order": self.name, "action": text.split()[0], "comment_type": comment_type}
        )

    def _sync_values(self):
        for key, value in vars(self).items():
            if not key.startswith("_"):
                self._values[key] = value


class FakeItemDoc(FakeOrderDoc):
    def insert(self, ignore_permissions=False):
        if not getattr(self, "name", None):
            self.name = f"LINE-{len(self._fake_frappe.order_items) + 1}"
        self._sync_values()
        self._fake_frappe.order_items.append(self._values)
        return self

    def delete(self, ignore_permissions=False):
        self._fake_frappe.order_items = [
            row for row in self._fake_frappe.order_items if row.get("name") != self.name
        ]


class FakeFrappe:
    def __init__(self, *, order_status="draft", order_branch="Main Branch", order_items=None):
        self.roles = ["Madar Employee", "Madar Branch User"]
        self.employee = {
            "name": "EMP-BRANCH",
            "employee_name": "Branch User",
            "branch": "Main Branch",
            "department": "Branch Operations",
        }
        created_by_user = "accountant.test@example.com" if order_branch != "Main Branch" else "branch.user@example.com"
        self.orders = [_order(branch=order_branch, status=order_status, created_by_user=created_by_user)]
        self.order_items = list(order_items or [])
        self.items = {
            "MILK-001": {"item_code": "MILK-001", "item_name": "Milk", "stock_uom": "Nos", "disabled": 0},
            "RICE-001": {"item_code": "RICE-001", "item_name": "Rice", "stock_uom": "Kg", "disabled": 0},
        }
        self.prices = {"MILK-001": 12.5, "RICE-001": 5}
        self.audit_events = []
        self.db = types.SimpleNamespace(commit=lambda: None)
        self.utils = types.SimpleNamespace(now_datetime=lambda: datetime(2026, 5, 19, 9, 0, 0))

    def get_roles(self, user):
        return list(self.roles)

    def get_all(self, doctype, filters=None, fields=None, order_by=None, limit=20):
        if doctype == "Employee":
            return [types.SimpleNamespace(**{field: self.employee.get(field) for field in fields})]
        if doctype == "Madar Order Item":
            rows = list(self.order_items)
            if filters:
                for key, value in filters.items():
                    rows = [row for row in rows if row.get(key) == value]
            return [types.SimpleNamespace(**{field: row.get(field) for field in fields}) for row in rows[:limit]]
        if doctype == "Item Price":
            item_code = filters.get("item_code")
            if item_code in self.prices:
                return [types.SimpleNamespace(price_list_rate=self.prices[item_code])]
            return []
        return []

    def get_doc(self, doctype_or_values, name=None):
        if isinstance(doctype_or_values, dict):
            return FakeItemDoc(self, dict(doctype_or_values))
        if doctype_or_values == "Madar Order":
            for row in self.orders:
                if row["name"] == name:
                    return FakeOrderDoc(self, row)
        if doctype_or_values == "Madar Order Item":
            for row in self.order_items:
                if row["name"] == name:
                    return FakeItemDoc(self, row)
        if doctype_or_values == "Item":
            if name in self.items:
                return types.SimpleNamespace(**self.items[name])
        raise KeyError(name)


if __name__ == "__main__":
    unittest.main()
