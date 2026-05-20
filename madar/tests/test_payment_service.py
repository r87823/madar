import types
import unittest
from datetime import datetime

from madar.services import payment_service


class PaymentServiceTest(unittest.TestCase):
    def test_branch_pickup_partial_and_full_payments_update_order_summary(self):
        fake_frappe = FakeFrappe(
            roles=["Madar Branch User", "Madar Cashier"],
            orders=[_order("MADAR-ORD-1", subtotal=100, delivery_status="ready_for_customer_pickup")],
        )

        partial = payment_service.collect_payment(
            "cashier.test@example.com",
            "MADAR-ORD-1",
            40,
            "cash",
            frappe_module=fake_frappe,
        )
        full = payment_service.collect_payment(
            "cashier.test@example.com",
            "MADAR-ORD-1",
            60,
            "card",
            reference_no="REF-123",
            frappe_module=fake_frappe,
        )

        self.assertEqual(partial["ok"], True)
        self.assertEqual(partial["data"]["collection_context"], "branch")
        self.assertEqual(partial["data"]["order"]["paid_amount"], 40.0)
        self.assertEqual(partial["data"]["order"]["remaining_amount"], 60.0)
        self.assertEqual(partial["data"]["order"]["payment_status"], "partially_paid")
        self.assertEqual(full["data"]["order"]["paid_amount"], 100.0)
        self.assertEqual(full["data"]["order"]["remaining_amount"], 0.0)
        self.assertEqual(full["data"]["order"]["payment_status"], "paid")
        self.assertEqual(partial["data"]["erp_sync_status"], "pending")
        self.assertEqual(full["data"]["erp_sync_status"], "pending")
        self.assertEqual(len(fake_frappe.payments), 2)
        self.assertEqual(fake_frappe.payments[1]["reference_no"], "REF-123")
        self.assertEqual(fake_frappe.created_erp_payment_entries, [])
        self.assertEqual(fake_frappe.created_sales_invoices, [])
        self.assertEqual(len(fake_frappe.cashbox_entries), 1)
        self.assertEqual(fake_frappe.cashbox_entries[0]["payment"], "PAY-1")

    def test_payment_amount_method_and_overpay_are_rejected(self):
        fake_frappe = FakeFrappe(
            roles=["Madar Branch User", "Madar Cashier"],
            orders=[_order("MADAR-ORD-1", subtotal=100, paid_amount=90, delivery_status="ready_for_customer_pickup")],
            payments=[_payment("PAY-EXISTING", "MADAR-ORD-1", amount=90, method="cash")],
        )

        invalid_amount = payment_service.collect_payment(
            "cashier.test@example.com",
            "MADAR-ORD-1",
            0,
            "cash",
            frappe_module=fake_frappe,
        )
        invalid_method = payment_service.collect_payment(
            "cashier.test@example.com",
            "MADAR-ORD-1",
            5,
            "cheque",
            frappe_module=fake_frappe,
        )
        overpay = payment_service.collect_payment(
            "cashier.test@example.com",
            "MADAR-ORD-1",
            20,
            "cash",
            frappe_module=fake_frappe,
        )

        self.assertEqual(invalid_amount["error"]["code"], "PAYMENT_AMOUNT_INVALID")
        self.assertEqual(invalid_method["error"]["code"], "PAYMENT_METHOD_INVALID")
        self.assertEqual(overpay["error"]["code"], "PAYMENT_EXCEEDS_REMAINING_AMOUNT")
        self.assertEqual(len(fake_frappe.payments), 1)

    def test_payment_cannot_be_collected_for_non_payable_order_status(self):
        fake_frappe = FakeFrappe(
            roles=["Madar Branch User", "Madar Cashier"],
            orders=[_order("MADAR-ORD-1", order_status="draft")],
        )

        result = payment_service.collect_payment(
            "cashier.test@example.com",
            "MADAR-ORD-1",
            10,
            "cash",
            frappe_module=fake_frappe,
        )

        self.assertEqual(result["error"]["code"], "ORDER_NOT_PAYABLE")

    def test_employee_without_payments_collect_is_rejected(self):
        fake_frappe = FakeFrappe(
            roles=["Madar Employee"],
            orders=[_order("MADAR-ORD-1", delivery_status="ready_for_customer_pickup")],
        )

        result = payment_service.collect_payment(
            "employee.test@example.com",
            "MADAR-ORD-1",
            10,
            "cash",
            frappe_module=fake_frappe,
        )

        self.assertEqual(result["error"]["code"], "PERMISSION_DENIED")

    def test_branch_user_cannot_collect_for_another_branch(self):
        fake_frappe = FakeFrappe(
            roles=["Madar Branch User", "Madar Cashier"],
            employee={
                "name": "EMP-HQ",
                "user_id": "cashier.test@example.com",
                "employee_name": "HQ User",
                "branch": "HQ",
                "department": "Finance",
            },
            orders=[_order("MADAR-ORD-1", destination_branch="Main Branch", delivery_status="ready_for_customer_pickup")],
        )

        result = payment_service.collect_payment(
            "cashier.test@example.com",
            "MADAR-ORD-1",
            10,
            "cash",
            frappe_module=fake_frappe,
        )

        self.assertEqual(result["error"]["code"], "OUT_OF_SCOPE")

    def test_driver_can_collect_only_for_assigned_customer_delivery_batch_order(self):
        assigned = FakeFrappe(
            roles=["Madar Driver"],
            orders=[
                _order(
                    "MADAR-ORD-1",
                    fulfillment_method="customer_delivery",
                    destination_branch="",
                    delivery_status="dispatched_to_customer",
                )
            ],
            delivery_batches=[_batch("BATCH-1", driver_user="driver.test@example.com", batch_type="customer_delivery")],
            delivery_batch_orders=[_batch_order("BATCH-ORDER-1", "BATCH-1", "MADAR-ORD-1")],
        )
        unassigned = FakeFrappe(
            roles=["Madar Driver"],
            orders=[
                _order(
                    "MADAR-ORD-2",
                    fulfillment_method="customer_delivery",
                    destination_branch="",
                    delivery_status="dispatched_to_customer",
                )
            ],
            delivery_batches=[_batch("BATCH-2", driver_user="other.driver@example.com", batch_type="customer_delivery")],
            delivery_batch_orders=[_batch_order("BATCH-ORDER-2", "BATCH-2", "MADAR-ORD-2")],
        )

        allowed = payment_service.collect_payment(
            "driver.test@example.com",
            "MADAR-ORD-1",
            25,
            "cash",
            frappe_module=assigned,
        )
        denied = payment_service.collect_payment(
            "driver.test@example.com",
            "MADAR-ORD-2",
            25,
            "cash",
            frappe_module=unassigned,
        )

        self.assertEqual(allowed["ok"], True)
        self.assertEqual(allowed["data"]["collection_context"], "delivery")
        self.assertEqual(denied["error"]["code"], "OUT_OF_SCOPE")

    def test_driver_cannot_collect_branch_pickup_payment(self):
        fake_frappe = FakeFrappe(
            roles=["Madar Driver"],
            orders=[_order("MADAR-ORD-1", delivery_status="ready_for_customer_pickup")],
        )

        result = payment_service.collect_payment(
            "driver.test@example.com",
            "MADAR-ORD-1",
            10,
            "cash",
            frappe_module=fake_frappe,
        )

        self.assertEqual(result["error"]["code"], "OUT_OF_SCOPE")

    def test_list_order_payments_returns_safe_payment_history(self):
        fake_frappe = FakeFrappe(
            roles=["Madar Admin"],
            orders=[_order("MADAR-ORD-1")],
            payments=[
                _payment("PAY-1", "MADAR-ORD-1", amount=10, method="cash"),
                _payment("PAY-2", "MADAR-ORD-1", amount=20, method="card"),
            ],
        )

        result = payment_service.list_order_payments(
            "Administrator",
            "MADAR-ORD-1",
            frappe_module=fake_frappe,
        )
        payment = payment_service.get_payment(
            "Administrator",
            "PAY-1",
            frappe_module=fake_frappe,
        )

        self.assertEqual([item["name"] for item in result["data"]["items"]], ["PAY-2", "PAY-1"])
        self.assertEqual(payment["data"]["amount"], 10.0)
        self.assertNotIn("password", payment["data"])
        self.assertNotIn("card_number", payment["data"])


def _order(
    name,
    *,
    order_status="approved",
    fulfillment_method="branch_pickup",
    destination_branch="Main Branch",
    delivery_status="ready_for_dispatch",
    subtotal=100,
    paid_amount=0,
):
    return {
        "doctype": "Madar Order",
        "name": name,
        "customer_name": f"Customer {name}",
        "customer_phone": "0500000000",
        "branch": destination_branch or "Main Branch",
        "assigned_branch": destination_branch or "Main Branch",
        "order_status": order_status,
        "production_status": "ready",
        "fulfillment_method": fulfillment_method,
        "destination_branch": destination_branch,
        "delivery_status": delivery_status,
        "subtotal": subtotal,
        "paid_amount": paid_amount,
        "remaining_amount": max(subtotal - paid_amount, 0),
        "payment_status": "unpaid" if paid_amount == 0 else "partially_paid",
        "items_count": 1,
        "modified": name,
    }


def _payment(name, order_name, *, amount, method, status="collected"):
    return {
        "doctype": "Madar Payment",
        "name": name,
        "madar_order": order_name,
        "amount": amount,
        "payment_method": method,
        "payment_status": status,
        "collected_by_user": "cashier.test@example.com",
        "collected_at": datetime(2026, 5, 19, 12, 0, 0),
        "collection_context": "branch",
        "reference_no": "",
        "notes": "",
        "is_cancelled": 0,
        "cancellation_reason": "",
        "modified": name,
        "password": "hidden",
        "card_number": "4111111111111111",
    }


def _batch(name, *, driver_user, batch_type):
    return {
        "doctype": "Madar Delivery Batch",
        "name": name,
        "batch_number": name,
        "batch_type": batch_type,
        "destination_branch": "",
        "driver_user": driver_user,
        "status": "out_for_delivery",
        "modified": name,
    }


def _batch_order(name, batch_name, order_name):
    return {
        "doctype": "Madar Delivery Batch Order",
        "name": name,
        "delivery_batch": batch_name,
        "madar_order": order_name,
        "delivery_status_snapshot": "ready_for_dispatch",
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


class FakeMeta:
    def has_field(self, field):
        return True


class FakeFrappe:
    def __init__(
        self,
        *,
        roles=None,
        employee=None,
        orders=None,
        payments=None,
        delivery_batches=None,
        delivery_batch_orders=None,
    ):
        self.roles = roles or ["Madar Admin"]
        self.employee = employee or {
            "name": "EMP-BRANCH",
            "user_id": "cashier.test@example.com",
            "employee_name": "Branch User",
            "branch": "Main Branch",
            "department": "Finance",
        }
        self.orders = list(orders or [])
        self.payments = list(payments or [])
        self.delivery_batches = list(delivery_batches or [])
        self.delivery_batch_orders = list(delivery_batch_orders or [])
        self.cashboxes = []
        self.cashbox_entries = []
        self.now = datetime(2026, 5, 19, 12, 0, 0)
        self.audit_events = []
        self.created_erp_payment_entries = []
        self.created_sales_invoices = []
        self.db = types.SimpleNamespace(commit=lambda: None)
        self.utils = types.SimpleNamespace(now_datetime=lambda: self.now)

    def get_roles(self, user):
        return list(self.roles)

    def get_meta(self, doctype):
        if doctype == "Employee":
            return FakeMeta()
        raise KeyError(doctype)

    def get_doc(self, doctype_or_values, name=None):
        if isinstance(doctype_or_values, dict):
            values = dict(doctype_or_values)
            if values["doctype"] == "Madar Payment":
                values["name"] = f"PAY-{len(self.payments) + 1}"
            elif values["doctype"] == "Madar Cashbox":
                values["name"] = f"CASHBOX-{len(self.cashboxes) + 1}"
            elif values["doctype"] == "Madar Cashbox Entry":
                values["name"] = f"CASHBOX-ENTRY-{len(self.cashbox_entries) + 1}"
            return FakeDoc(self, values)
        if doctype_or_values == "Payment Entry":
            self.created_erp_payment_entries.append(name)
            raise AssertionError("Madar payments must not create ERPNext Payment Entry")
        if doctype_or_values == "Sales Invoice":
            self.created_sales_invoices.append(name)
            raise AssertionError("Madar payments must not create Sales Invoice")
        rows = {
            "Madar Order": self.orders,
            "Madar Payment": self.payments,
            "Madar Delivery Batch": self.delivery_batches,
            "Madar Delivery Batch Order": self.delivery_batch_orders,
            "Madar Cashbox": self.cashboxes,
            "Madar Cashbox Entry": self.cashbox_entries,
        }.get(doctype_or_values, [])
        for row in rows:
            if row.get("doctype") == doctype_or_values and row.get("name") == name:
                return FakeDoc(self, row)
        raise KeyError(name)

    def get_all(self, doctype, filters=None, fields=None, order_by=None, limit=20):
        if doctype == "Employee":
            rows = [self.employee] if self.employee else []
        elif doctype == "Madar Order":
            rows = list(self.orders)
        elif doctype == "Madar Payment":
            rows = list(self.payments)
        elif doctype == "Madar Delivery Batch":
            rows = list(self.delivery_batches)
        elif doctype == "Madar Delivery Batch Order":
            rows = list(self.delivery_batch_orders)
        elif doctype == "Madar Cashbox":
            rows = list(self.cashboxes)
        elif doctype == "Madar Cashbox Entry":
            rows = list(self.cashbox_entries)
        else:
            rows = []
        rows = self._filter_rows(rows, filters)
        if order_by:
            rows.sort(key=lambda row: row.get("modified") or row.get("name"), reverse="desc" in order_by)
        return [types.SimpleNamespace(**{field: row.get(field) for field in fields}) for row in rows[:limit]]

    def insert_doc(self, values):
        if values["doctype"] == "Madar Payment":
            self.payments.append(values)
        elif values["doctype"] == "Madar Cashbox":
            self.cashboxes.append(values)
        elif values["doctype"] == "Madar Cashbox Entry":
            self.cashbox_entries.append(values)
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
