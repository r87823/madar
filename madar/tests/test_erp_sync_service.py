import types
import unittest
from datetime import datetime

from madar.services import erp_sync_service
from madar.tests.test_order_service import _order


class ErpSyncServiceTest(unittest.TestCase):
    def test_sync_review_requires_accounting_permission(self):
        fake_frappe = FakeFrappe(roles=["Madar Employee"])

        result = erp_sync_service.list_sync_orders(
            user="employee.test@example.com", frappe_module=fake_frappe
        )

        self.assertEqual(result["ok"], False)
        self.assertEqual(result["error"]["code"], "PERMISSION_DENIED")

    def test_list_sync_orders_returns_safe_fields_for_accountant(self):
        fake_frappe = FakeFrappe(
            roles=["Madar Employee", "Madar Accountant"],
            orders=[
                _sync_order("MADAR-ORD-1", status="approved", items_count=1, erp_sync_status="failed"),
                _sync_order(
                    "MADAR-ORD-2",
                    status="approved",
                    items_count=1,
                    erp_sync_status="synced",
                    erp_sales_order="SAL-ORD-1",
                ),
                _sync_order("MADAR-ORD-3", status="draft", items_count=1),
            ],
        )

        result = erp_sync_service.list_sync_orders(
            user="accountant.test@example.com", frappe_module=fake_frappe
        )

        self.assertEqual(result["ok"], True)
        self.assertEqual([item["name"] for item in result["data"]["items"]], ["MADAR-ORD-2", "MADAR-ORD-1"])
        self.assertEqual(
            set(result["data"]["items"][0]),
            {
                "name",
                "customer_name",
                "subtotal",
                "order_status",
                "delivery_status",
                "erp_sync_status",
                "erp_sync_error",
                "erp_sales_order",
                "erp_sales_order_docstatus",
                "erp_sales_invoice",
                "erp_sales_invoice_docstatus",
                "erp_invoice_sync_status",
                "erp_invoice_sync_error",
                "erp_invoice_created_at",
                "approved_at",
                "approved_by",
            },
        )
        self.assertNotIn("password", result["data"]["items"][0])

    def test_get_sync_order_returns_safe_detail(self):
        fake_frappe = FakeFrappe(
            roles=["Madar Accountant"],
            orders=[_sync_order("MADAR-ORD-1", status="approved", items_count=1)],
        )

        result = erp_sync_service.get_sync_order(
            user="accountant.test@example.com",
            order_name="MADAR-ORD-1",
            frappe_module=fake_frappe,
        )

        self.assertEqual(result["ok"], True)
        self.assertEqual(result["data"]["name"], "MADAR-ORD-1")
        self.assertEqual(set(result["data"]), set(erp_sync_service.SYNC_ORDER_FIELDS))

    def test_retry_sync_order_allows_pending_or_failed_and_rejects_synced(self):
        fake_frappe = FakeFrappe(
            roles=["Madar Accountant"],
            orders=[
                _sync_order("MADAR-ORD-1", status="approved", items_count=1, erp_sync_status="failed"),
                _sync_order(
                    "MADAR-ORD-2",
                    status="approved",
                    items_count=1,
                    erp_sync_status="synced",
                    erp_sales_order="SAL-ORD-OLD",
                ),
            ],
            items=[_item("LINE-1", "MADAR-ORD-1"), _item("LINE-2", "MADAR-ORD-2")],
        )

        retried = erp_sync_service.retry_sync_order(
            user="accountant.test@example.com",
            order_name="MADAR-ORD-1",
            frappe_module=fake_frappe,
        )
        synced = erp_sync_service.retry_sync_order(
            user="accountant.test@example.com",
            order_name="MADAR-ORD-2",
            frappe_module=fake_frappe,
        )

        self.assertEqual(retried["ok"], True)
        self.assertEqual(retried["data"]["erp_sync_status"], "synced")
        self.assertEqual(set(retried["data"]), set(erp_sync_service.SYNC_ORDER_FIELDS))
        self.assertNotIn("created_by_user", retried["data"])
        self.assertEqual(synced["ok"], False)
        self.assertEqual(synced["error"]["code"], "ORDER_ALREADY_SYNCED")

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

    def test_map_madar_order_to_sales_order_uses_safe_draft_fields(self):
        payload = {
            "customer": "Customer MADAR-ORD-1",
            "items": [{"item_code": "MILK-001", "qty": 2, "rate": 12.5}],
            "notes": "Mobile order",
            "madar_order": "MADAR-ORD-1",
        }
        fake_frappe = FakeFrappe(today="2026-05-19")

        mapped = erp_sync_service.map_madar_order_to_sales_order(
            payload, frappe_module=fake_frappe
        )

        self.assertEqual(mapped["doctype"], "Sales Order")
        self.assertEqual(mapped["customer"], "Customer MADAR-ORD-1")
        self.assertEqual(mapped["transaction_date"], "2026-05-19")
        self.assertEqual(mapped["delivery_date"], "2026-05-19")
        self.assertEqual(
            mapped["items"],
            [{"item_code": "MILK-001", "qty": 2, "rate": 12.5, "delivery_date": "2026-05-19"}],
        )
        self.assertEqual(mapped["remarks"], "Mobile order\nMadar Order: MADAR-ORD-1")

    def test_create_sales_order_inserts_draft_sales_order(self):
        fake_frappe = FakeFrappe(today="2026-05-19")
        payload = {
            "customer": "Customer MADAR-ORD-1",
            "items": [{"item_code": "MILK-001", "qty": 1, "rate": 12.5}],
            "notes": "",
            "madar_order": "MADAR-ORD-1",
        }

        result = erp_sync_service.create_sales_order(payload, frappe_module=fake_frappe)

        self.assertEqual(result["ok"], True)
        self.assertEqual(result["data"]["name"], "SAL-ORD-00001")
        self.assertEqual(len(fake_frappe.created_sales_orders), 1)
        self.assertEqual(fake_frappe.created_sales_orders[0]["doctype"], "Sales Order")

    def test_sync_order_to_erp_creates_sales_order_and_marks_synced(self):
        fake_frappe = FakeFrappe(
            orders=[_sync_order("MADAR-ORD-1", status="approved", items_count=1)],
            items=[_item("LINE-1", "MADAR-ORD-1")],
            today="2026-05-19",
        )

        result = erp_sync_service.sync_order_to_erp(
            "MADAR-ORD-1", frappe_module=fake_frappe
        )

        self.assertEqual(result["ok"], True)
        self.assertEqual(result["data"]["erp_sales_order"], "SAL-ORD-00001")
        self.assertEqual(result["data"]["erp_sync_status"], "synced")
        self.assertEqual(fake_frappe.orders[0]["erp_sales_order"], "SAL-ORD-00001")
        self.assertEqual(fake_frappe.orders[0]["erp_sync_status"], "synced")

    def test_sync_order_to_erp_tracks_safe_failure_message(self):
        fake_frappe = FakeFrappe(
            orders=[_sync_order("MADAR-ORD-1", status="approved", items_count=1)],
            items=[_item("LINE-1", "MADAR-ORD-1")],
            insert_error=RuntimeError("Traceback: Customer missing\nsecret-token"),
        )

        result = erp_sync_service.sync_order_to_erp(
            "MADAR-ORD-1", frappe_module=fake_frappe
        )

        self.assertEqual(result["ok"], False)
        self.assertEqual(result["error"]["code"], "ERP_SYNC_FAILED")
        self.assertEqual(fake_frappe.orders[0]["erp_sync_status"], "failed")
        self.assertEqual(fake_frappe.orders[0]["erp_sync_error"], "Traceback: Customer missing")

    def test_sync_order_to_erp_rejects_already_synced_without_creating_duplicate(self):
        fake_frappe = FakeFrappe(
            orders=[
                _sync_order(
                    "MADAR-ORD-1",
                    status="approved",
                    items_count=1,
                    erp_sync_status="synced",
                    erp_sales_order="SAL-ORD-OLD",
                )
            ],
            items=[_item("LINE-1", "MADAR-ORD-1")],
        )

        result = erp_sync_service.sync_order_to_erp(
            "MADAR-ORD-1", frappe_module=fake_frappe
        )

        self.assertEqual(result["ok"], False)
        self.assertEqual(result["error"]["code"], "ORDER_ALREADY_SYNCED")
        self.assertEqual(fake_frappe.created_sales_orders, [])

    def test_submit_erp_sales_order_submits_draft_and_is_idempotent(self):
        fake_frappe = FakeFrappe(
            orders=[
                _sync_order(
                    "MADAR-ORD-1",
                    status="approved",
                    items_count=1,
                    erp_sync_status="synced",
                    erp_sales_order="SAL-ORD-00001",
                    erp_sales_order_docstatus=0,
                )
            ],
            sales_orders=[{"name": "SAL-ORD-00001", "docstatus": 0}],
        )

        submitted = erp_sync_service.submit_erp_sales_order(
            "MADAR-ORD-1", frappe_module=fake_frappe
        )
        submitted_again = erp_sync_service.submit_erp_sales_order(
            "MADAR-ORD-1", frappe_module=fake_frappe
        )

        self.assertEqual(submitted["ok"], True)
        self.assertEqual(submitted["data"]["erp_sales_order_docstatus"], 1)
        self.assertEqual(submitted_again["ok"], True)
        self.assertEqual(submitted_again["data"]["erp_sales_order_docstatus"], 1)
        self.assertEqual(fake_frappe.sales_orders[0]["submit_count"], 1)
        self.assertEqual(fake_frappe.created_sales_invoices, [])

    def test_submit_erp_sales_order_requires_existing_erp_sales_order(self):
        fake_frappe = FakeFrappe(
            orders=[_sync_order("MADAR-ORD-1", status="approved", items_count=1)]
        )

        result = erp_sync_service.submit_erp_sales_order(
            "MADAR-ORD-1", frappe_module=fake_frappe
        )

        self.assertEqual(result["ok"], False)
        self.assertEqual(result["error"]["code"], "ORDER_NOT_SYNCED_TO_ERP")

    def test_validate_invoice_requires_delivery_completion_and_submitted_sales_order(self):
        draft_sales_order = FakeFrappe(
            orders=[
                _sync_order(
                    "MADAR-ORD-1",
                    status="approved",
                    items_count=1,
                    erp_sync_status="synced",
                    erp_sales_order="SAL-ORD-00001",
                    erp_sales_order_docstatus=0,
                    delivery_status="customer_picked_up",
                )
            ],
            sales_orders=[{"name": "SAL-ORD-00001", "docstatus": 0}],
            items=[_item("LINE-1", "MADAR-ORD-1")],
        )
        not_delivered = FakeFrappe(
            orders=[
                _sync_order(
                    "MADAR-ORD-2",
                    status="approved",
                    items_count=1,
                    erp_sync_status="synced",
                    erp_sales_order="SAL-ORD-00002",
                    erp_sales_order_docstatus=1,
                    fulfillment_method="customer_delivery",
                    delivery_status="dispatched_to_customer",
                )
            ],
            sales_orders=[{"name": "SAL-ORD-00002", "docstatus": 1}],
            items=[_item("LINE-2", "MADAR-ORD-2")],
        )
        already_invoiced = FakeFrappe(
            orders=[
                _sync_order(
                    "MADAR-ORD-3",
                    status="approved",
                    items_count=1,
                    erp_sync_status="synced",
                    erp_sales_order="SAL-ORD-00003",
                    erp_sales_order_docstatus=1,
                    erp_sales_invoice="ACC-SINV-1",
                    erp_invoice_sync_status="synced",
                    delivery_status="customer_picked_up",
                )
            ],
            sales_orders=[{"name": "SAL-ORD-00003", "docstatus": 1}],
            items=[_item("LINE-3", "MADAR-ORD-3")],
        )

        self.assertEqual(
            erp_sync_service.validate_order_ready_for_invoice(
                "MADAR-ORD-1", frappe_module=draft_sales_order
            )["error"]["code"],
            "ORDER_NOT_READY_FOR_INVOICE",
        )
        self.assertEqual(
            erp_sync_service.validate_order_ready_for_invoice(
                "MADAR-ORD-2", frappe_module=not_delivered
            )["error"]["code"],
            "ORDER_NOT_DELIVERED",
        )
        self.assertEqual(
            erp_sync_service.validate_order_ready_for_invoice(
                "MADAR-ORD-3", frappe_module=already_invoiced
            )["error"]["code"],
            "SALES_INVOICE_ALREADY_SYNCED",
        )

    def test_sync_sales_invoice_creates_draft_invoice_and_saves_reference(self):
        fake_frappe = FakeFrappe(
            orders=[
                _sync_order(
                    "MADAR-ORD-1",
                    status="approved",
                    items_count=1,
                    subtotal=12.5,
                    erp_sync_status="synced",
                    erp_sales_order="SAL-ORD-00001",
                    erp_sales_order_docstatus=1,
                    delivery_status="customer_picked_up",
                )
            ],
            sales_orders=[
                {
                    "name": "SAL-ORD-00001",
                    "docstatus": 1,
                    "customer": "Customer MADAR-ORD-1",
                    "company": "Madar Co",
                }
            ],
            items=[_item("LINE-1", "MADAR-ORD-1", item_code="MILK-001", qty=1, unit_price=12.5)],
            today="2026-05-20",
        )

        result = erp_sync_service.sync_sales_invoice_to_erp(
            "MADAR-ORD-1", frappe_module=fake_frappe
        )

        self.assertEqual(result["ok"], True)
        self.assertEqual(result["data"]["erp_sales_invoice"], "ACC-SINV-00001")
        self.assertEqual(result["data"]["erp_invoice_sync_status"], "synced")
        self.assertEqual(fake_frappe.created_sales_invoices[0]["doctype"], "Sales Invoice")
        self.assertEqual(fake_frappe.created_sales_invoices[0]["docstatus"], 0)
        self.assertEqual(fake_frappe.created_sales_invoices[0]["items"][0]["sales_order"], "SAL-ORD-00001")
        self.assertEqual(fake_frappe.submitted_payment_entries, [])

    def test_sync_sales_invoice_tracks_safe_failure(self):
        fake_frappe = FakeFrappe(
            orders=[
                _sync_order(
                    "MADAR-ORD-1",
                    status="approved",
                    items_count=1,
                    erp_sync_status="synced",
                    erp_sales_order="SAL-ORD-00001",
                    erp_sales_order_docstatus=1,
                    delivery_status="customer_picked_up",
                )
            ],
            sales_orders=[{"name": "SAL-ORD-00001", "docstatus": 1, "customer": "Customer MADAR-ORD-1"}],
            items=[_item("LINE-1", "MADAR-ORD-1")],
            insert_error=RuntimeError("Traceback: Missing income account\nsecret-token"),
        )

        result = erp_sync_service.sync_sales_invoice_to_erp(
            "MADAR-ORD-1", frappe_module=fake_frappe
        )

        self.assertEqual(result["ok"], False)
        self.assertEqual(result["error"]["code"], "ERP_INVOICE_SYNC_FAILED")
        self.assertEqual(fake_frappe.orders[0]["erp_invoice_sync_status"], "failed")
        self.assertEqual(fake_frappe.orders[0]["erp_invoice_sync_error"], "Traceback: Missing income account")


def _sync_order(
    name,
    *,
    status="approved",
    items_count=1,
    subtotal=12.5,
    erp_sync_status="pending",
    erp_sales_order=None,
    erp_sales_order_docstatus=None,
    erp_sales_invoice=None,
    erp_invoice_sync_status="pending",
    delivery_status="not_ready",
    fulfillment_method="branch_pickup",
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
            "erp_sales_order_docstatus": erp_sales_order_docstatus,
            "erp_sales_invoice": erp_sales_invoice,
            "erp_invoice_sync_status": erp_invoice_sync_status,
            "erp_invoice_sync_error": None,
            "erp_invoice_created_at": None,
            "delivery_status": delivery_status,
            "fulfillment_method": fulfillment_method,
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
    def __init__(
        self,
        *,
        orders=None,
        items=None,
        sales_orders=None,
        today="2026-05-19",
        insert_error=None,
        roles=None,
    ):
        self.orders = list(orders or [])
        self.items = list(items or [])
        self.roles = roles or ["Madar Accountant"]
        self.created_sales_orders = []
        self.created_sales_invoices = []
        self.submitted_payment_entries = []
        self.sales_orders = [
            dict(row, submit_count=row.get("submit_count", 0))
            for row in (sales_orders or [])
        ]
        self.today = today
        self.insert_error = insert_error
        self.audit_events = []
        self.db = types.SimpleNamespace(commit=lambda: None)
        self.utils = types.SimpleNamespace(nowdate=lambda: self.today)

    def get_roles(self, user):
        return list(self.roles)

    def get_doc(self, doctype_or_values, name=None):
        if isinstance(doctype_or_values, dict):
            if doctype_or_values.get("doctype") == "Sales Order":
                return FakeSalesOrderDoc(self, dict(doctype_or_values))
            if doctype_or_values.get("doctype") == "Sales Invoice":
                return FakeSalesInvoiceDoc(self, dict(doctype_or_values))
            raise AssertionError("ERP sync boundary must only create allowed ERP documents")
        if doctype_or_values == "Madar Order":
            for row in self.orders:
                if row["name"] == name:
                    return FakeOrderDoc(self, row)
        if doctype_or_values == "Sales Order":
            for row in self.sales_orders:
                if row["name"] == name:
                    return FakeExistingSalesOrderDoc(self, row)
        raise KeyError(name)

    def get_all(self, doctype, filters=None, fields=None, order_by=None, limit=20):
        if doctype == "Madar Order":
            rows = list(self.orders)
        elif doctype == "Madar Order Item":
            rows = list(self.items)
        else:
            return []
        if filters:
            for key, value in filters.items():
                if isinstance(value, list) and value[0] == "in":
                    rows = [row for row in rows if row.get(key) in value[1]]
                else:
                    rows = [row for row in rows if row.get(key) == value]
        if order_by:
            rows.sort(key=lambda row: row.get("modified") or row.get("name"), reverse="desc" in order_by)
        return [types.SimpleNamespace(**{field: row.get(field) for field in fields}) for row in rows[:limit]]


class FakeSalesOrderDoc:
    def __init__(self, fake_frappe, values):
        self._fake_frappe = fake_frappe
        self._values = values
        self.name = None
        for key, value in values.items():
            setattr(self, key, value)

    def insert(self, ignore_permissions=False):
        if self._fake_frappe.insert_error:
            raise self._fake_frappe.insert_error
        self.name = f"SAL-ORD-{len(self._fake_frappe.created_sales_orders) + 1:05d}"
        self._values["name"] = self.name
        self._fake_frappe.created_sales_orders.append(self._values)
        return self


class FakeExistingSalesOrderDoc:
    def __init__(self, fake_frappe, values):
        self._fake_frappe = fake_frappe
        self._values = values
        for key, value in values.items():
            setattr(self, key, value)

    def submit(self):
        if self._fake_frappe.insert_error:
            raise self._fake_frappe.insert_error
        self.docstatus = 1
        self._values["docstatus"] = 1
        self._values["submit_count"] = self._values.get("submit_count", 0) + 1
        return self


class FakeSalesInvoiceDoc:
    def __init__(self, fake_frappe, values):
        self._fake_frappe = fake_frappe
        self._values = values
        self.name = None
        for key, value in values.items():
            setattr(self, key, value)

    def insert(self, ignore_permissions=False):
        if self._fake_frappe.insert_error:
            raise self._fake_frappe.insert_error
        self.name = f"ACC-SINV-{len(self._fake_frappe.created_sales_invoices) + 1:05d}"
        self._values["name"] = self.name
        self._fake_frappe.created_sales_invoices.append(self._values)
        return self


if __name__ == "__main__":
    unittest.main()
