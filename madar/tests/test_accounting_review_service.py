import types
import unittest
from datetime import datetime

from madar.services import accounting_review_service
from madar.tests.test_erp_sync_service import _sync_order


class AccountingReviewServiceTest(unittest.TestCase):
    def test_ready_order_returns_ready_for_review_summary(self):
        fake_frappe = FakeFrappe(
            roles=["Madar Accountant"],
            orders=[
                _review_order(
                    "MADAR-ORD-1",
                    delivery_status="customer_picked_up",
                    paid_amount=100,
                    remaining_amount=0,
                    payment_status="paid",
                    erp_sales_order="SAL-ORD-1",
                    erp_sales_order_docstatus=1,
                    erp_sales_invoice="ACC-SINV-1",
                    erp_invoice_sync_status="synced",
                )
            ],
            payments=[
                _payment("PAY-1", "MADAR-ORD-1", 60, "cash", erp_sync_status="synced"),
                _payment("PAY-2", "MADAR-ORD-1", 40, "card", erp_sync_status="synced"),
            ],
            cashbox_entries=[_cashbox_entry("ENTRY-1", "PAY-1", "CASHBOX-1", "MADAR-ORD-1", 60)],
            cashboxes=[_cashbox("CASHBOX-1", status="approved")],
        )

        result = accounting_review_service.get_order_accounting_summary(
            "accountant.test@example.com", "MADAR-ORD-1", frappe_module=fake_frappe
        )

        self.assertEqual(result["ok"], True)
        self.assertEqual(result["data"]["accounting_status"], "ready_for_review")
        self.assertEqual(result["data"]["payments"]["count"], 2)
        self.assertEqual(result["data"]["payments"]["total_collected"], 100.0)
        self.assertEqual(result["data"]["payments"]["methods"], {"cash": 60.0, "card": 40.0})
        self.assertEqual(result["data"]["cashbox"]["cash_payments_total"], 60.0)
        self.assertEqual(result["data"]["cashbox"]["statuses"], ["approved"])
        self.assertTrue(result["data"]["readiness"]["payments_match_order_total"])
        self.assertTrue(result["data"]["readiness"]["payment_entries_synced_or_not_required"])
        self.assertTrue(result["data"]["readiness"]["cashboxes_reviewed_for_cash_payments"])
        self.assertNotIn("password", result["data"]["order"])

    def test_not_delivered_order_is_not_ready(self):
        fake_frappe = FakeFrappe(
            orders=[
                _review_order(
                    "MADAR-ORD-1",
                    delivery_status="ready_for_dispatch",
                    paid_amount=100,
                    remaining_amount=0,
                    payment_status="paid",
                    erp_sales_order="SAL-ORD-1",
                    erp_sales_order_docstatus=1,
                    erp_sales_invoice="ACC-SINV-1",
                    erp_invoice_sync_status="synced",
                )
            ],
            payments=[_payment("PAY-1", "MADAR-ORD-1", 100, "card", erp_sync_status="synced")],
        )

        result = accounting_review_service.get_order_accounting_summary(
            "accountant.test@example.com", "MADAR-ORD-1", frappe_module=fake_frappe
        )

        self.assertEqual(result["data"]["accounting_status"], "not_ready")
        self.assertFalse(result["data"]["readiness"]["delivered_or_picked_up"])

    def test_failed_sync_unpaid_and_unapproved_cashbox_need_attention(self):
        fake_frappe = FakeFrappe(
            orders=[
                _review_order(
                    "MADAR-ORD-1",
                    delivery_status="customer_picked_up",
                    paid_amount=40,
                    remaining_amount=60,
                    payment_status="partially_paid",
                    erp_sync_status="failed",
                    erp_sync_error="Customer missing",
                    erp_sales_order="",
                    erp_invoice_sync_status="failed",
                    erp_invoice_sync_error="Invoice account missing",
                )
            ],
            payments=[
                _payment("PAY-1", "MADAR-ORD-1", 40, "cash", erp_sync_status="failed"),
            ],
            cashbox_entries=[_cashbox_entry("ENTRY-1", "PAY-1", "CASHBOX-1", "MADAR-ORD-1", 40)],
            cashboxes=[_cashbox("CASHBOX-1", status="submitted")],
        )

        result = accounting_review_service.get_order_accounting_summary(
            "accountant.test@example.com", "MADAR-ORD-1", frappe_module=fake_frappe
        )

        self.assertEqual(result["data"]["accounting_status"], "needs_attention")
        self.assertIn("ERP_SYNC_FAILED", result["data"]["alerts"])
        self.assertIn("PAYMENTS_DO_NOT_MATCH_TOTAL", result["data"]["alerts"])
        self.assertIn("CASHBOX_NOT_APPROVED", result["data"]["alerts"])
        self.assertIn("PAYMENT_SYNC_FAILED", result["data"]["alerts"])

    def test_list_orders_for_accounting_review_excludes_reviewed_by_default(self):
        fake_frappe = FakeFrappe(
            roles=["Madar Accountant"],
            orders=[
                _review_order("MADAR-ORD-1", accounting_status="reviewed"),
                _review_order("MADAR-ORD-2", delivery_status="customer_picked_up"),
            ],
        )

        result = accounting_review_service.list_orders_for_accounting_review(
            "accountant.test@example.com", frappe_module=fake_frappe
        )

        self.assertEqual(result["ok"], True)
        self.assertEqual([item["order"]["name"] for item in result["data"]["items"]], ["MADAR-ORD-2"])

    def test_mark_reviewed_requires_ready_order_for_accountant(self):
        ready = FakeFrappe(
            roles=["Madar Accountant"],
            orders=[
                _review_order(
                    "MADAR-ORD-1",
                    delivery_status="customer_picked_up",
                    paid_amount=100,
                    remaining_amount=0,
                    payment_status="paid",
                    erp_sales_order="SAL-ORD-1",
                    erp_sales_order_docstatus=1,
                    erp_sales_invoice="ACC-SINV-1",
                    erp_invoice_sync_status="synced",
                )
            ],
            payments=[_payment("PAY-1", "MADAR-ORD-1", 100, "card", erp_sync_status="synced")],
        )
        not_ready = FakeFrappe(
            roles=["Madar Accountant"],
            orders=[_review_order("MADAR-ORD-2", delivery_status="ready_for_dispatch")],
        )

        reviewed = accounting_review_service.mark_accounting_reviewed(
            "accountant.test@example.com", "MADAR-ORD-1", frappe_module=ready
        )
        rejected = accounting_review_service.mark_accounting_reviewed(
            "accountant.test@example.com", "MADAR-ORD-2", frappe_module=not_ready
        )

        self.assertEqual(reviewed["ok"], True)
        self.assertEqual(reviewed["data"]["accounting_status"], "reviewed")
        self.assertEqual(ready.orders[0]["accounting_reviewed_by"], "accountant.test@example.com")
        self.assertEqual(rejected["ok"], False)
        self.assertEqual(rejected["error"]["code"], "ORDER_NOT_READY_FOR_ACCOUNTING_REVIEW")

    def test_system_full_access_can_override_review_readiness(self):
        fake_frappe = FakeFrappe(
            roles=["System Manager"],
            orders=[_review_order("MADAR-ORD-1", delivery_status="ready_for_dispatch")],
        )

        result = accounting_review_service.mark_accounting_reviewed(
            "Administrator", "MADAR-ORD-1", frappe_module=fake_frappe
        )

        self.assertEqual(result["ok"], True)
        self.assertEqual(fake_frappe.orders[0]["accounting_status"], "reviewed")

    def test_mark_needs_attention_requires_notes_and_permission(self):
        fake_frappe = FakeFrappe(
            roles=["Madar Accountant"],
            orders=[_review_order("MADAR-ORD-1", delivery_status="customer_picked_up")],
        )
        denied_frappe = FakeFrappe(
            roles=["Madar Employee"],
            orders=[_review_order("MADAR-ORD-1", delivery_status="customer_picked_up")],
        )

        missing_notes = accounting_review_service.mark_accounting_needs_attention(
            "accountant.test@example.com", "MADAR-ORD-1", "", frappe_module=fake_frappe
        )
        marked = accounting_review_service.mark_accounting_needs_attention(
            "accountant.test@example.com",
            "MADAR-ORD-1",
            "راجع مطابقة الدفع",
            frappe_module=fake_frappe,
        )
        denied = accounting_review_service.mark_accounting_needs_attention(
            "employee.test@example.com", "MADAR-ORD-1", "note", frappe_module=denied_frappe
        )

        self.assertEqual(missing_notes["error"]["code"], "ACCOUNTING_REVIEW_NOTES_REQUIRED")
        self.assertEqual(marked["ok"], True)
        self.assertEqual(marked["data"]["accounting_status"], "needs_attention")
        self.assertEqual(fake_frappe.orders[0]["accounting_review_notes"], "راجع مطابقة الدفع")
        self.assertEqual(denied["error"]["code"], "PERMISSION_DENIED")
        self.assertEqual(fake_frappe.created_sales_invoices, [])
        self.assertEqual(fake_frappe.submitted_payment_entries, [])


def _review_order(
    name,
    *,
    subtotal=100,
    paid_amount=0,
    remaining_amount=100,
    payment_status="unpaid",
    delivery_status="not_ready",
    production_status="ready",
    fulfillment_method="branch_pickup",
    erp_sync_status="synced",
    erp_sync_error="",
    erp_sales_order="SAL-ORD-1",
    erp_sales_order_docstatus=1,
    erp_sales_invoice="ACC-SINV-1",
    erp_invoice_sync_status="synced",
    erp_invoice_sync_error="",
    accounting_status="",
):
    order = _sync_order(
        name,
        status="approved",
        items_count=1,
        subtotal=subtotal,
        erp_sync_status=erp_sync_status,
        erp_sales_order=erp_sales_order,
        erp_sales_order_docstatus=erp_sales_order_docstatus,
        erp_sales_invoice=erp_sales_invoice,
        erp_invoice_sync_status=erp_invoice_sync_status,
        delivery_status=delivery_status,
        fulfillment_method=fulfillment_method,
    )
    order.update(
        {
            "paid_amount": paid_amount,
            "remaining_amount": remaining_amount,
            "payment_status": payment_status,
            "production_status": production_status,
            "erp_sync_error": erp_sync_error,
            "erp_invoice_sync_error": erp_invoice_sync_error,
            "accounting_status": accounting_status,
            "accounting_review_notes": "",
            "accounting_reviewed_by": "",
            "accounting_reviewed_at": None,
        }
    )
    return order


def _payment(name, order_name, amount, method, *, erp_sync_status="pending"):
    return {
        "doctype": "Madar Payment",
        "name": name,
        "madar_order": order_name,
        "amount": amount,
        "payment_method": method,
        "payment_status": "collected",
        "collected_by_user": "cashier.test@example.com",
        "collected_at": datetime(2026, 5, 20, 12, 0, 0),
        "collection_context": "branch",
        "reference_no": "",
        "notes": "",
        "is_cancelled": 0,
        "cancellation_reason": "",
        "erp_sync_status": erp_sync_status,
        "erp_sync_error": "Payment failed" if erp_sync_status == "failed" else "",
        "erp_payment_entry": "ACC-PAY-1" if erp_sync_status == "synced" else "",
        "modified": name,
    }


def _cashbox_entry(name, payment_name, cashbox_name, order_name, amount):
    return {
        "doctype": "Madar Cashbox Entry",
        "name": name,
        "cashbox": cashbox_name,
        "payment": payment_name,
        "madar_order": order_name,
        "amount": amount,
        "entry_type": "cash_payment",
        "created_by_user": "cashier.test@example.com",
        "created_at": datetime(2026, 5, 20, 12, 0, 0),
        "modified": name,
    }


def _cashbox(name, *, status="open"):
    return {
        "doctype": "Madar Cashbox",
        "name": name,
        "user": "cashier.test@example.com",
        "cashbox_date": "2026-05-20",
        "status": status,
        "expected_cash": 60,
        "submitted_cash": 60,
        "difference": 0,
        "submitted_at": datetime(2026, 5, 20, 14, 0, 0),
        "reviewed_by": "accountant.test@example.com" if status == "approved" else "",
        "reviewed_at": datetime(2026, 5, 20, 15, 0, 0) if status == "approved" else None,
        "return_reason": "",
        "closed_at": None,
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
        self._fake_frappe.audit_events.append({"doc": self.name, "text": text})


class FakeFrappe:
    def __init__(self, *, roles=None, orders=None, payments=None, cashbox_entries=None, cashboxes=None):
        self.roles = roles or ["Madar Accountant"]
        self.orders = list(orders or [])
        self.payments = list(payments or [])
        self.cashbox_entries = list(cashbox_entries or [])
        self.cashboxes = list(cashboxes or [])
        self.audit_events = []
        self.created_sales_invoices = []
        self.submitted_payment_entries = []
        self.db = types.SimpleNamespace(commit=lambda: None)
        self.utils = types.SimpleNamespace(now_datetime=lambda: datetime(2026, 5, 20, 13, 0, 0))

    def get_roles(self, user):
        return list(self.roles)

    def get_doc(self, doctype, name=None):
        if doctype == "Madar Order":
            for row in self.orders:
                if row["name"] == name:
                    return FakeDoc(self, row)
        if doctype == "Madar Payment":
            for row in self.payments:
                if row["name"] == name:
                    return FakeDoc(self, row)
        if doctype == "Madar Cashbox":
            for row in self.cashboxes:
                if row["name"] == name:
                    return FakeDoc(self, row)
        raise KeyError(name)

    def get_all(self, doctype, filters=None, fields=None, order_by=None, limit=20):
        if doctype == "Madar Order":
            rows = list(self.orders)
        elif doctype == "Madar Payment":
            rows = list(self.payments)
        elif doctype == "Madar Cashbox Entry":
            rows = list(self.cashbox_entries)
        elif doctype == "Madar Cashbox":
            rows = list(self.cashboxes)
        else:
            rows = []
        rows = _apply_filters(rows, filters or {})
        if order_by:
            rows.sort(key=lambda row: row.get("modified") or row.get("name"), reverse="desc" in order_by)
        if fields is None:
            return rows[:limit]
        return [types.SimpleNamespace(**{field: row.get(field) for field in fields}) for row in rows[:limit]]


def _apply_filters(rows, filters):
    filtered = rows
    for key, value in filters.items():
        if isinstance(value, list) and value[0] == "in":
            filtered = [row for row in filtered if row.get(key) in value[1]]
        elif isinstance(value, list) and value[0] == "!=":
            filtered = [row for row in filtered if row.get(key) != value[1]]
        else:
            filtered = [row for row in filtered if row.get(key) == value]
    return filtered


if __name__ == "__main__":
    unittest.main()
