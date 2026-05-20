import types
import unittest
from datetime import datetime

from madar.services import payment_erp_sync_service


class PaymentErpSyncServiceTest(unittest.TestCase):
    def test_prepare_payment_entry_payload_requires_synced_order(self):
        fake_frappe = FakeFrappe(
            payments=[_payment("PAY-1", "MADAR-ORD-1", amount=40, method="cash")],
            orders=[_order("MADAR-ORD-1", erp_sales_order="")],
        )

        result = payment_erp_sync_service.prepare_payment_entry_payload(
            "PAY-1",
            frappe_module=fake_frappe,
        )

        self.assertEqual(result["error"]["code"], "ORDER_NOT_SYNCED_TO_ERP")
        self.assertEqual(fake_frappe.payment_entries, [])
        self.assertEqual(fake_frappe.sales_invoices, [])

    def test_sync_collected_payment_creates_draft_payment_entry_and_marks_success(self):
        fake_frappe = FakeFrappe(
            payments=[_payment("PAY-1", "MADAR-ORD-1", amount=40, method="cash", reference_no="REF-1")],
            orders=[_order("MADAR-ORD-1", erp_sales_order="SAL-ORD-1")],
        )

        result = payment_erp_sync_service.sync_payment_to_erp("PAY-1", frappe_module=fake_frappe)

        self.assertEqual(result["ok"], True)
        self.assertEqual(result["data"]["erp_sync_status"], "synced")
        self.assertEqual(result["data"]["erp_payment_entry"], "ACC-PAY-1")
        self.assertEqual(fake_frappe.payments[0]["erp_sync_status"], "synced")
        self.assertEqual(fake_frappe.payment_entries[0]["docstatus"], 0)
        self.assertEqual(fake_frappe.payment_entries[0]["doctype"], "Payment Entry")
        self.assertEqual(fake_frappe.payment_entries[0]["party_type"], "Customer")
        self.assertEqual(fake_frappe.payment_entries[0]["party"], "Customer MADAR-ORD-1")
        self.assertEqual(fake_frappe.payment_entries[0]["paid_amount"], 40.0)
        self.assertEqual(fake_frappe.payment_entries[0]["received_amount"], 40.0)
        self.assertEqual(fake_frappe.payment_entries[0]["mode_of_payment"], "Cash")
        self.assertEqual(fake_frappe.payment_entries[0]["reference_no"], "REF-1")
        self.assertEqual(fake_frappe.sales_invoices, [])

    def test_invalid_and_already_synced_payments_are_rejected(self):
        fake_frappe = FakeFrappe(
            payments=[
                _payment("PAY-CANCELLED", "MADAR-ORD-1", amount=40, method="cash", is_cancelled=1),
                _payment("PAY-ZERO", "MADAR-ORD-1", amount=0, method="cash"),
                _payment("PAY-SYNCED", "MADAR-ORD-1", amount=10, method="card", erp_sync_status="synced"),
            ],
            orders=[_order("MADAR-ORD-1", erp_sales_order="SAL-ORD-1")],
        )

        cancelled = payment_erp_sync_service.validate_payment_ready_for_sync(
            "PAY-CANCELLED",
            frappe_module=fake_frappe,
        )
        zero = payment_erp_sync_service.validate_payment_ready_for_sync(
            "PAY-ZERO",
            frappe_module=fake_frappe,
        )
        synced = payment_erp_sync_service.validate_payment_ready_for_sync(
            "PAY-SYNCED",
            frappe_module=fake_frappe,
        )

        self.assertEqual(cancelled["error"]["code"], "PAYMENT_NOT_COLLECTED")
        self.assertEqual(zero["error"]["code"], "PAYMENT_AMOUNT_INVALID")
        self.assertEqual(synced["error"]["code"], "PAYMENT_ALREADY_SYNCED")

    def test_failure_marks_safe_error_without_exposing_raw_exception(self):
        fake_frappe = FakeFrappe(
            fail_payment_entry=True,
            payments=[_payment("PAY-1", "MADAR-ORD-1", amount=40, method="online")],
            orders=[_order("MADAR-ORD-1", erp_sales_order="SAL-ORD-1")],
        )

        result = payment_erp_sync_service.sync_payment_to_erp("PAY-1", frappe_module=fake_frappe)

        self.assertEqual(result["error"]["code"], "ERP_PAYMENT_SYNC_FAILED")
        self.assertEqual(fake_frappe.payments[0]["erp_sync_status"], "failed")
        self.assertIn("Simulated ERP failure", fake_frappe.payments[0]["erp_sync_error"])
        self.assertNotIn("Traceback", fake_frappe.payments[0]["erp_sync_error"])
        self.assertEqual(fake_frappe.sales_invoices, [])

    def test_list_get_and_retry_require_accounting_permission(self):
        denied = FakeFrappe(
            roles=["Madar Employee"],
            payments=[_payment("PAY-1", "MADAR-ORD-1", amount=40, method="cash")],
            orders=[_order("MADAR-ORD-1", erp_sales_order="SAL-ORD-1")],
        )
        allowed = FakeFrappe(
            roles=["Madar Accountant"],
            payments=[_payment("PAY-1", "MADAR-ORD-1", amount=40, method="cash")],
            orders=[_order("MADAR-ORD-1", erp_sales_order="SAL-ORD-1")],
        )

        denied_result = payment_erp_sync_service.list_payment_sync_items(
            "employee.test@example.com",
            frappe_module=denied,
        )
        listed = payment_erp_sync_service.list_payment_sync_items(
            "accountant.test@example.com",
            frappe_module=allowed,
        )
        fetched = payment_erp_sync_service.get_payment_sync_item(
            "accountant.test@example.com",
            "PAY-1",
            frappe_module=allowed,
        )
        retried = payment_erp_sync_service.retry_payment_sync(
            "accountant.test@example.com",
            "PAY-1",
            frappe_module=allowed,
        )
        retry_synced = payment_erp_sync_service.retry_payment_sync(
            "accountant.test@example.com",
            "PAY-1",
            frappe_module=allowed,
        )

        self.assertEqual(denied_result["error"]["code"], "PERMISSION_DENIED")
        self.assertEqual(listed["data"]["items"][0]["name"], "PAY-1")
        self.assertEqual(fetched["data"]["name"], "PAY-1")
        self.assertEqual(retried["data"]["erp_sync_status"], "synced")
        self.assertEqual(retry_synced["error"]["code"], "PAYMENT_ALREADY_SYNCED")


def _order(name, *, erp_sales_order):
    return {
        "doctype": "Madar Order",
        "name": name,
        "customer_name": f"Customer {name}",
        "erp_sales_order": erp_sales_order,
        "modified": name,
    }


def _payment(
    name,
    order_name,
    *,
    amount,
    method,
    status="collected",
    is_cancelled=0,
    erp_sync_status="pending",
    reference_no="",
):
    return {
        "doctype": "Madar Payment",
        "name": name,
        "madar_order": order_name,
        "amount": amount,
        "payment_method": method,
        "payment_status": status,
        "collected_by_user": "cashier.test@example.com",
        "collected_at": datetime(2026, 5, 20, 12, 0, 0),
        "collection_context": "branch",
        "reference_no": reference_no,
        "notes": "Payment notes",
        "is_cancelled": is_cancelled,
        "cancellation_reason": "",
        "erp_sync_status": erp_sync_status,
        "erp_sync_error": "",
        "erp_payment_entry": "ACC-PAY-OLD" if erp_sync_status == "synced" else "",
        "modified": name,
    }


class FakeDoc:
    def __init__(self, fake_frappe, values):
        self._fake_frappe = fake_frappe
        self._values = values
        for key, value in values.items():
            setattr(self, key, value)

    def insert(self, ignore_permissions=False):
        self._fake_frappe.insert_doc(self._values)
        return self

    def save(self, ignore_permissions=False):
        for key, value in vars(self).items():
            if not key.startswith("_"):
                self._values[key] = value
        return self

    def add_comment(self, comment_type, text):
        self._fake_frappe.audit_events.append({"comment_type": comment_type, "text": text})


class FakeFrappe:
    def __init__(self, *, roles=None, payments=None, orders=None, fail_payment_entry=False):
        self.roles = roles or ["Madar Accountant"]
        self.payments = list(payments or [])
        self.orders = list(orders or [])
        self.payment_entries = []
        self.sales_invoices = []
        self.fail_payment_entry = fail_payment_entry
        self.audit_events = []
        self.db = types.SimpleNamespace(commit=lambda: None)
        self.utils = types.SimpleNamespace(nowdate=lambda: "2026-05-20")

    def get_roles(self, user):
        return list(self.roles)

    def get_doc(self, doctype_or_values, name=None):
        if isinstance(doctype_or_values, dict):
            values = dict(doctype_or_values)
            if values["doctype"] == "Payment Entry":
                if self.fail_payment_entry:
                    raise RuntimeError("Simulated ERP failure\nTraceback: secret stack")
                values["name"] = f"ACC-PAY-{len(self.payment_entries) + 1}"
            elif values["doctype"] == "Sales Invoice":
                self.sales_invoices.append(values)
                raise AssertionError("Payment sync must not create Sales Invoice")
            return FakeDoc(self, values)
        rows = {
            "Madar Payment": self.payments,
            "Madar Order": self.orders,
            "Payment Entry": self.payment_entries,
            "Sales Invoice": self.sales_invoices,
        }.get(doctype_or_values, [])
        for row in rows:
            if row.get("doctype") == doctype_or_values and row.get("name") == name:
                return FakeDoc(self, row)
        raise KeyError(name)

    def get_all(self, doctype, filters=None, fields=None, order_by=None, limit=20):
        rows = {
            "Madar Payment": self.payments,
            "Madar Order": self.orders,
            "Payment Entry": self.payment_entries,
            "Sales Invoice": self.sales_invoices,
        }.get(doctype, [])
        rows = self._filter_rows(rows, filters)
        if order_by:
            rows.sort(key=lambda row: row.get("modified") or row.get("name"), reverse="desc" in order_by)
        return [types.SimpleNamespace(**{field: row.get(field) for field in fields}) for row in rows[:limit]]

    def insert_doc(self, values):
        if values["doctype"] == "Payment Entry":
            self.payment_entries.append(values)
        elif values["doctype"] == "Sales Invoice":
            self.sales_invoices.append(values)
        else:
            raise AssertionError(values["doctype"])

    def _filter_rows(self, rows, filters):
        filtered = list(rows)
        for key, value in (filters or {}).items():
            if isinstance(value, list) and value[0] == "in":
                filtered = [row for row in filtered if row.get(key) in value[1]]
            else:
                filtered = [row for row in filtered if row.get(key) == value]
        return filtered


if __name__ == "__main__":
    unittest.main()
