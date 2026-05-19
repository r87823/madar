import types
import unittest
from datetime import datetime

from madar.services import erp_sync_service
from madar.tests.test_order_service import _order


class ErpSyncServiceTest(unittest.TestCase):
    def test_validate_requires_approved_order_with_items_and_not_synced(self):
        not_approved = FakeFrappe(
            orders=[_sync_order("MADAR-ORD-1", status="submitted", items_count=1)]
        )
        empty = FakeFrappe(
            orders=[_sync_order("MADAR-ORD-2", status="approved", items_count=0)]
        )
        synced = FakeFrappe(
            orders=[
                _sync_order(
                    "MADAR-ORD-3",
                    status="approved",
                    items_count=1,
                    erp_sync_status="synced",
                    erp_sales_order="SAL-ORD-1",
                )
            ],
            items=[_item("LINE-1", "MADAR-ORD-3")],
        )

        self.assertEqual(
            erp_sync_service.validate_order_ready_for_sync(
                "MADAR-ORD-1", frappe_module=not_approved
            )["error"]["code"],
            "ORDER_NOT_APPROVED",
        )
        self.assertEqual(
            erp_sync_service.validate_order_ready_for_sync(
                "MADAR-ORD-2", frappe_module=empty
            )["error"]["code"],
            "ORDER_HAS_NO_ITEMS",
        )
        self.assertEqual(
            erp_sync_service.validate_order_ready_for_sync(
                "MADAR-ORD-3", frappe_module=synced
            )["error"]["code"],
            "ORDER_ALREADY_SYNCED",
        )

    def test_prepare_sales_order_payload_returns_safe_payload_without_creating_sales_order(self):
        fake_frappe = FakeFrappe(
            orders=[_sync_order("MADAR-ORD-1", status="approved", items_count=2, subtotal=25)],
            items=[
                _item("LINE-1", "MADAR-ORD-1", item_code="MILK-001", qty=2, unit_price=10),
                _item("LINE-2", "MADAR-ORD-1", item_code="RICE-001", qty=1, unit_price=5),
            ],
        )

        result = erp_sync_service.prepare_sales_order_payload(
            "MADAR-ORD-1", frappe_module=fake_frappe
        )

        self.assertEqual(result["ok"], True)
        self.assertEqual(result["data"]["madar_order"], "MADAR-ORD-1")
        self.assertEqual(result["data"]["customer"], "Customer MADAR-ORD-1")
        self.assertEqual(result["data"]["branch"], "Main Branch")
        self.assertEqual(
            result["data"]["items"],
            [
                {"item_code": "MILK-001", "qty": 2.0, "rate": 10.0},
                {"item_code": "RICE-001", "qty": 1.0, "rate": 5.0},
            ],
        )
        self.assertEqual(fake_frappe.created_sales_orders, [])

    def test_mark_sync_failed_and_success_update_metadata_only(self):
        fake_frappe = FakeFrappe(
            orders=[_sync_order("MADAR-ORD-1", status="approved", items_count=1)],
            items=[_item("LINE-1", "MADAR-ORD-1")],
        )

        failed = erp_sync_service.mark_sync_failed(
            "MADAR-ORD-1", "Customer missing", frappe_module=fake_frappe
        )
        success = erp_sync_service.mark_sync_success(
            "MADAR-ORD-1", "SAL-ORD-2026-00001", frappe_module=fake_frappe
        )

        self.assertEqual(failed["data"]["erp_sync_status"], "failed")
        self.assertEqual(failed["data"]["erp_sync_error"], "Customer missing")
        self.assertEqual(success["data"]["erp_sync_status"], "synced")
        self.assertEqual(success["data"]["erp_sales_order"], "SAL-ORD-2026-00001")
        self.assertEqual(fake_frappe.created_sales_orders, [])


def _sync_order(
    name,
    *,
    status="approved",
    items_count=1,
    subtotal=12.5,
    erp_sync_status="pending",
    erp_sales_order=None,
):
    order = _order(
        name,
        "Main Branch",
        "branch.user@example.com",
        status=status,
        items_count=items_count,
        subtotal=subtotal,
    )
    order.update(
        {
            "approved_at": datetime(2026, 5, 19, 10, 0, 0),
            "approved_by": "branch.supervisor@example.com",
            "erp_sync_status": erp_sync_status,
            "erp_sync_error": None,
            "erp_sales_order": erp_sales_order,
        }
    )
    return order


def _item(name, order_name, item_code="MILK-001", qty=1, unit_price=12.5):
    return {
        "doctype": "Madar Order Item",
        "name": name,
        "order_name": order_name,
        "item_code": item_code,
        "item_name": item_code,
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
        for key, value in vars(self).items():
            if not key.startswith("_"):
                self._values[key] = value
        return self

    def add_comment(self, comment_type, text):
        self._fake_frappe.audit_events.append(
            {"order": self.name, "action": text.split()[0], "comment_type": comment_type}
        )


class FakeFrappe:
    def __init__(self, *, orders=None, items=None):
        self.orders = list(orders or [])
        self.items = list(items or [])
        self.created_sales_orders = []
        self.audit_events = []
        self.db = types.SimpleNamespace(commit=lambda: None)

    def get_doc(self, doctype_or_values, name=None):
        if isinstance(doctype_or_values, dict):
            if doctype_or_values.get("doctype") == "Sales Order":
                self.created_sales_orders.append(doctype_or_values)
            raise AssertionError("ERP sync boundary must not create documents")
        if doctype_or_values == "Madar Order":
            for row in self.orders:
                if row["name"] == name:
                    return FakeOrderDoc(self, row)
        raise KeyError(name)

    def get_all(self, doctype, filters=None, fields=None, order_by=None, limit=20):
        if doctype != "Madar Order Item":
            return []
        rows = list(self.items)
        if filters:
            for key, value in filters.items():
                rows = [row for row in rows if row.get(key) == value]
        return [types.SimpleNamespace(**{field: row.get(field) for field in fields}) for row in rows[:limit]]


if __name__ == "__main__":
    unittest.main()
