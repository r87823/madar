import types
import unittest
from datetime import datetime

from madar.services import accounting_finalization_service
from madar.tests.test_accounting_review_service import (
    FakeDoc as ReviewFakeDoc,
    FakeFrappe as ReviewFakeFrappe,
    _cashbox,
    _cashbox_entry,
    _payment,
    _review_order,
)


class AccountingFinalizationServiceTest(unittest.TestCase):
    def test_read_permission_can_view_status_but_cannot_submit(self):
        fake_frappe = FakeFrappe(
            roles=["Accounts User"],
            orders=[_final_order("MADAR-ORD-1")],
            payments=[_final_payment("PAY-1", "MADAR-ORD-1", 100, "card")],
            sales_invoices=[_erp_doc("ACC-SINV-1", docstatus=0)],
            payment_entries=[_erp_doc("ACC-PAY-1", docstatus=0)],
        )

        status = accounting_finalization_service.get_finalization_status(
            "accounts.user@example.com", "MADAR-ORD-1", frappe_module=fake_frappe
        )
        denied = accounting_finalization_service.submit_sales_invoice(
            "accounts.user@example.com", "MADAR-ORD-1", frappe_module=fake_frappe
        )

        self.assertEqual(status["ok"], True)
        self.assertEqual(denied["error"]["code"], "ACCOUNTING_FINALIZE_PERMISSION_DENIED")

    def test_invoice_submit_requires_finalize_permission_and_ready_order(self):
        denied_frappe = FakeFrappe(roles=["Madar Branch Supervisor"], orders=[_final_order("MADAR-ORD-1")])
        not_ready_frappe = FakeFrappe(
            roles=["Madar Accountant"],
            orders=[_final_order("MADAR-ORD-1", delivery_status="ready_for_dispatch")],
        )

        denied = accounting_finalization_service.submit_sales_invoice(
            "supervisor.test@example.com", "MADAR-ORD-1", frappe_module=denied_frappe
        )
        not_ready = accounting_finalization_service.submit_sales_invoice(
            "accountant.test@example.com", "MADAR-ORD-1", frappe_module=not_ready_frappe
        )

        self.assertEqual(denied["error"]["code"], "ACCOUNTING_FINALIZE_PERMISSION_DENIED")
        self.assertEqual(not_ready["error"]["code"], "ORDER_NOT_READY_FOR_FINAL_SUBMIT")

    def test_invoice_submit_updates_docstatus_and_is_idempotent(self):
        fake_frappe = FakeFrappe(
            roles=["Madar Accountant"],
            orders=[_final_order("MADAR-ORD-1")],
            sales_invoices=[_erp_doc("ACC-SINV-1", docstatus=0)],
        )

        submitted = accounting_finalization_service.submit_sales_invoice(
            "accountant.test@example.com", "MADAR-ORD-1", frappe_module=fake_frappe
        )
        repeated = accounting_finalization_service.submit_sales_invoice(
            "accountant.test@example.com", "MADAR-ORD-1", frappe_module=fake_frappe
        )

        self.assertEqual(submitted["ok"], True)
        self.assertEqual(fake_frappe.orders[0]["erp_sales_invoice_docstatus"], 1)
        self.assertEqual(fake_frappe.sales_invoices[0]["docstatus"], 1)
        self.assertEqual(repeated["ok"], True)
        self.assertEqual(repeated["data"]["erp_sales_invoice_docstatus"], 1)
        self.assertEqual(fake_frappe.created_delivery_notes, [])
        self.assertEqual(fake_frappe.created_stock_entries, [])

    def test_invoice_submit_failure_stores_safe_error(self):
        fake_frappe = FakeFrappe(
            roles=["Madar Accountant"],
            orders=[_final_order("MADAR-ORD-1")],
            sales_invoices=[_erp_doc("ACC-SINV-1", docstatus=0, submit_error="secret token\ntraceback")],
        )

        result = accounting_finalization_service.submit_sales_invoice(
            "accountant.test@example.com", "MADAR-ORD-1", frappe_module=fake_frappe
        )

        self.assertEqual(result["error"]["code"], "SALES_INVOICE_SUBMIT_FAILED")
        self.assertEqual(fake_frappe.orders[0]["accounting_finalization_error"], "secret token")
        self.assertNotIn("traceback", fake_frappe.orders[0]["accounting_finalization_error"])

    def test_payment_entry_submit_updates_all_synced_payment_entries(self):
        fake_frappe = FakeFrappe(
            roles=["Madar Accountant"],
            orders=[_final_order("MADAR-ORD-1")],
            payments=[
                _final_payment("PAY-1", "MADAR-ORD-1", 60, "card", erp_payment_entry="ACC-PAY-1"),
                _final_payment("PAY-2", "MADAR-ORD-1", 40, "transfer", erp_payment_entry="ACC-PAY-2"),
            ],
            payment_entries=[_erp_doc("ACC-PAY-1", docstatus=0), _erp_doc("ACC-PAY-2", docstatus=1)],
        )

        result = accounting_finalization_service.submit_payment_entries_for_order(
            "accountant.test@example.com", "MADAR-ORD-1", frappe_module=fake_frappe
        )

        self.assertEqual(result["ok"], True)
        self.assertEqual([payment["erp_payment_entry_docstatus"] for payment in fake_frappe.payments], [1, 1])
        self.assertTrue(fake_frappe.payments[0]["erp_payment_submitted_at"])

    def test_finalization_blocks_unpaid_order_and_unapproved_cashbox(self):
        unpaid = FakeFrappe(
            roles=["Madar Accountant"],
            orders=[_final_order("MADAR-ORD-1", paid_amount=50, remaining_amount=50, payment_status="partially_paid")],
            payments=[_final_payment("PAY-1", "MADAR-ORD-1", 50, "card")],
        )
        cashbox_pending = FakeFrappe(
            roles=["Madar Accountant"],
            orders=[_final_order("MADAR-ORD-2", erp_sales_invoice_docstatus=1)],
            payments=[
                _final_payment(
                    "PAY-2",
                    "MADAR-ORD-2",
                    100,
                    "cash",
                    erp_payment_entry_docstatus=1,
                )
            ],
            cashbox_entries=[_cashbox_entry("ENTRY-1", "PAY-2", "CASHBOX-1", "MADAR-ORD-2", 100)],
            cashboxes=[_cashbox("CASHBOX-1", status="submitted")],
        )

        unpaid_result = accounting_finalization_service.finalize_order_accounting(
            "accountant.test@example.com", "MADAR-ORD-1", frappe_module=unpaid
        )
        cashbox_result = accounting_finalization_service.finalize_order_accounting(
            "accountant.test@example.com", "MADAR-ORD-2", frappe_module=cashbox_pending
        )

        self.assertEqual(unpaid_result["error"]["code"], "ORDER_NOT_PAID")
        self.assertEqual(cashbox_result["error"]["code"], "CASHBOX_NOT_APPROVED")

    def test_finalization_succeeds_when_invoice_payments_and_cashbox_are_ready(self):
        fake_frappe = FakeFrappe(
            roles=["Madar Accountant"],
            orders=[_final_order("MADAR-ORD-1", erp_sales_invoice_docstatus=1)],
            payments=[
                _final_payment(
                    "PAY-1",
                    "MADAR-ORD-1",
                    100,
                    "cash",
                    erp_payment_entry="ACC-PAY-1",
                    erp_payment_entry_docstatus=1,
                )
            ],
            cashbox_entries=[_cashbox_entry("ENTRY-1", "PAY-1", "CASHBOX-1", "MADAR-ORD-1", 100)],
            cashboxes=[_cashbox("CASHBOX-1", status="approved")],
        )

        result = accounting_finalization_service.finalize_order_accounting(
            "accountant.test@example.com", "MADAR-ORD-1", frappe_module=fake_frappe
        )

        self.assertEqual(result["ok"], True)
        self.assertEqual(fake_frappe.orders[0]["accounting_status"], "reviewed")
        self.assertEqual(fake_frappe.orders[0]["accounting_finalized_by"], "accountant.test@example.com")
        self.assertTrue(fake_frappe.orders[0]["accounting_finalized_at"])


def _final_order(name, **overrides):
    order = _review_order(
        name,
        paid_amount=100,
        remaining_amount=0,
        payment_status="paid",
        delivery_status="customer_picked_up",
        accounting_status="ready_for_review",
    )
    order.update(
        {
            "erp_sales_invoice_docstatus": 0,
            "accounting_finalized_at": None,
            "accounting_finalized_by": "",
            "accounting_finalization_error": "",
        }
    )
    order.update(overrides)
    return order


def _final_payment(
    name,
    order_name,
    amount,
    method,
    *,
    erp_payment_entry="ACC-PAY-1",
    erp_payment_entry_docstatus=0,
):
    payment = _payment(name, order_name, amount, method, erp_sync_status="synced")
    payment.update(
        {
            "erp_payment_entry": erp_payment_entry,
            "erp_payment_entry_docstatus": erp_payment_entry_docstatus,
            "erp_payment_submitted_at": None,
            "erp_payment_submit_error": "",
        }
    )
    return payment


def _erp_doc(name, *, docstatus=0, submit_error=None):
    return {"name": name, "docstatus": docstatus, "submit_error": submit_error}


class ERPDoc(ReviewFakeDoc):
    def submit(self):
        if self._values.get("submit_error"):
            raise Exception(self._values["submit_error"])
        self.docstatus = 1
        self._values["docstatus"] = 1
        return self


class FakeFrappe(ReviewFakeFrappe):
    def __init__(self, *, sales_orders=None, sales_invoices=None, payment_entries=None, **kwargs):
        super().__init__(**kwargs)
        self.sales_orders = list(sales_orders or [_erp_doc("SAL-ORD-1", docstatus=1)])
        self.sales_invoices = list(sales_invoices or [_erp_doc("ACC-SINV-1", docstatus=0)])
        self.payment_entries = list(payment_entries or [_erp_doc("ACC-PAY-1", docstatus=0)])
        self.created_delivery_notes = []
        self.created_stock_entries = []
        self.utils = types.SimpleNamespace(
            now_datetime=lambda: datetime(2026, 5, 20, 16, 0, 0),
            nowdate=lambda: "2026-05-20",
        )

    def get_doc(self, doctype, name=None):
        if doctype == "Sales Order":
            for row in self.sales_orders:
                if row["name"] == name:
                    return ERPDoc(self, row)
        if doctype == "Sales Invoice":
            for row in self.sales_invoices:
                if row["name"] == name:
                    return ERPDoc(self, row)
        if doctype == "Payment Entry":
            for row in self.payment_entries:
                if row["name"] == name:
                    return ERPDoc(self, row)
        if doctype == "Delivery Note":
            self.created_delivery_notes.append(name)
        if doctype == "Stock Entry":
            self.created_stock_entries.append(name)
        return super().get_doc(doctype, name)


if __name__ == "__main__":
    unittest.main()
