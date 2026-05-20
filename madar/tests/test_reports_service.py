import types
import unittest
from datetime import datetime

from madar.services import reports_service


class ReportsServiceTest(unittest.TestCase):
    def test_branch_user_sees_scoped_orders_with_pagination_and_filters(self):
        fake_frappe = FakeFrappe(
            roles=["Madar Employee", "Madar Branch User"],
            employee={"branch": "Main Branch", "department": "Branch Operations"},
            orders=[
                _order("ORD-1", "Main Branch", order_status="draft"),
                _order("ORD-2", "HQ", order_status="draft"),
                _order("ORD-3", "Main Branch", order_status="submitted"),
            ],
        )

        result = reports_service.get_orders_report(
            "branch.user@example.com",
            {"order_status": "draft", "page": 1, "page_size": 1},
            frappe_module=fake_frappe,
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["total"], 1)
        self.assertEqual(result["data"]["page_size"], 1)
        self.assertEqual([row["name"] for row in result["data"]["items"]], ["ORD-1"])
        self.assertNotIn("customer_phone", str(result["data"]))

    def test_supervisor_sees_pending_orders_inside_branch_scope(self):
        fake_frappe = FakeFrappe(
            roles=["Madar Employee", "Madar Branch Supervisor"],
            employee={"branch": "Main Branch", "department": "Branch Operations"},
            orders=[
                _order("ORD-1", "Main Branch", order_status="submitted"),
                _order("ORD-2", "HQ", order_status="submitted"),
            ],
        )

        result = reports_service.get_orders_report(
            "branch.supervisor@example.com",
            {"order_status": "submitted"},
            frappe_module=fake_frappe,
        )

        self.assertTrue(result["ok"])
        self.assertEqual([row["name"] for row in result["data"]["items"]], ["ORD-1"])

    def test_driver_sees_only_assigned_delivery_batches(self):
        fake_frappe = FakeFrappe(
            roles=["Madar Employee", "Madar Driver"],
            employee={"branch": "Main Branch", "department": "Delivery"},
            batches=[
                _batch("BATCH-1", "driver.test@example.com", "assigned"),
                _batch("BATCH-2", "other@example.com", "assigned"),
            ],
        )

        result = reports_service.get_delivery_report(
            "driver.test@example.com",
            {},
            frappe_module=fake_frappe,
        )

        self.assertTrue(result["ok"])
        self.assertEqual([row["name"] for row in result["data"]["items"]], ["BATCH-1"])

    def test_accountant_sees_payment_cashbox_and_erp_reports(self):
        fake_frappe = FakeFrappe(
            roles=["Madar Accountant"],
            payments=[
                _payment("PAY-1", "ORD-1", "cash", "collected", "cashier.test@example.com", erp_sync_status="failed"),
                _payment("PAY-2", "ORD-2", "card", "collected", "driver.test@example.com", erp_sync_status="synced"),
            ],
            cashboxes=[
                _cashbox("CASH-1", "cashier.test@example.com", "submitted"),
                _cashbox("CASH-2", "driver.test@example.com", "approved"),
            ],
        )

        payments = reports_service.get_payments_report(
            "accountant.test@example.com",
            {"payment_method": "cash"},
            frappe_module=fake_frappe,
        )
        cashboxes = reports_service.get_cashbox_report(
            "accountant.test@example.com",
            {"status": "submitted"},
            frappe_module=fake_frappe,
        )
        erp_errors = reports_service.get_erp_sync_errors_report(
            "accountant.test@example.com",
            {},
            frappe_module=fake_frappe,
        )

        self.assertEqual([row["name"] for row in payments["data"]["items"]], ["PAY-1"])
        self.assertEqual(payments["data"]["summary"]["total_amount"], 50)
        self.assertEqual([row["name"] for row in cashboxes["data"]["items"]], ["CASH-1"])
        self.assertEqual(erp_errors["data"]["items"][0]["entity_type"], "Madar Payment")
        self.assertNotIn("Traceback", str(erp_errors["data"]))

    def test_production_user_sees_department_scoped_work_orders(self):
        fake_frappe = FakeFrappe(
            roles=["Madar Employee", "Madar Production User"],
            employee={"branch": "Main Branch", "department": "Kitchen"},
            work_orders=[
                _work_order("WO-1", "Kitchen", "in_production"),
                _work_order("WO-2", "Packaging", "in_production"),
            ],
        )

        result = reports_service.get_production_report(
            "production.test@example.com",
            {"status": "in_production"},
            frappe_module=fake_frappe,
        )

        self.assertTrue(result["ok"])
        self.assertEqual([row["name"] for row in result["data"]["items"]], ["WO-1"])

    def test_employee_without_permission_is_denied(self):
        fake_frappe = FakeFrappe(
            roles=["Madar Employee"],
            employee={"branch": "Main Branch", "department": "General"},
        )

        result = reports_service.get_cashbox_report(
            "employee.test@example.com",
            {},
            frappe_module=fake_frappe,
        )

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "PERMISSION_DENIED")

    def test_max_page_size_is_enforced(self):
        fake_frappe = FakeFrappe(
            roles=["Administrator"],
            orders=[_order(f"ORD-{index}", "Main Branch") for index in range(80)],
        )

        result = reports_service.get_orders_report(
            "Administrator",
            {"page_size": 500},
            frappe_module=fake_frappe,
        )

        self.assertEqual(result["data"]["page_size"], reports_service.MAX_PAGE_SIZE)
        self.assertEqual(len(result["data"]["items"]), reports_service.MAX_PAGE_SIZE)


def _order(
    name,
    branch,
    *,
    order_status="draft",
    production_status="not_started",
    delivery_status="not_ready",
    payment_status="unpaid",
    erp_sync_status="pending",
    erp_invoice_sync_status="pending",
):
    return {
        "doctype": "Madar Order",
        "name": name,
        "customer_name": "Customer",
        "assigned_branch": branch,
        "branch": branch,
        "destination_branch": branch,
        "order_status": order_status,
        "production_status": production_status,
        "delivery_status": delivery_status,
        "payment_status": payment_status,
        "subtotal": 100,
        "paid_amount": 20,
        "remaining_amount": 80,
        "erp_sync_status": erp_sync_status,
        "erp_sync_error": "Traceback secret\nSafe order error",
        "erp_sales_order": "SO-1",
        "erp_invoice_sync_status": erp_invoice_sync_status,
        "erp_invoice_sync_error": "Traceback secret\nSafe invoice error",
        "erp_sales_invoice": "SI-1",
        "creation": datetime(2026, 5, 20, 9, 0, 0),
        "modified": datetime(2026, 5, 20, 10, 0, 0),
    }


def _payment(name, order, method, status, user, erp_sync_status="pending"):
    return {
        "doctype": "Madar Payment",
        "name": name,
        "madar_order": order,
        "amount": 50,
        "payment_method": method,
        "payment_status": status,
        "collection_context": "branch",
        "collected_by_user": user,
        "collected_at": datetime(2026, 5, 20, 11, 0, 0),
        "erp_sync_status": erp_sync_status,
        "erp_sync_error": "Traceback secret\nSafe payment error",
        "erp_payment_entry": "PE-1",
        "modified": datetime(2026, 5, 20, 12, 0, 0),
    }


def _work_order(name, department, status):
    return {
        "doctype": "Madar Work Order",
        "name": name,
        "madar_order": "ORD-1",
        "production_center": "Center",
        "production_department": department,
        "status": status,
        "accepted_at": None,
        "started_at": None,
        "ready_at": None,
        "delayed_at": None,
        "delay_reason": None,
        "creation": datetime(2026, 5, 20, 8, 0, 0),
        "modified": datetime(2026, 5, 20, 9, 0, 0),
    }


def _batch(name, driver_user, status):
    return {
        "doctype": "Madar Delivery Batch",
        "name": name,
        "batch_type": "customer_delivery",
        "driver_user": driver_user,
        "destination_branch": "Main Branch",
        "status": status,
        "picked_up_at": None,
        "out_for_delivery_at": None,
        "delivered_at": None,
        "returned_at": None,
        "creation": datetime(2026, 5, 20, 7, 0, 0),
        "modified": datetime(2026, 5, 20, 8, 0, 0),
    }


def _cashbox(name, user, status):
    return {
        "doctype": "Madar Cashbox",
        "name": name,
        "user": user,
        "cashbox_date": datetime(2026, 5, 20).date(),
        "status": status,
        "expected_cash": 100,
        "submitted_cash": 90,
        "difference": -10,
        "submitted_at": datetime(2026, 5, 20, 20, 0, 0),
        "reviewed_by": None,
        "reviewed_at": None,
        "modified": datetime(2026, 5, 20, 21, 0, 0),
    }


class FakeFrappe:
    def __init__(
        self,
        *,
        roles=None,
        employee=None,
        orders=None,
        work_orders=None,
        batches=None,
        payments=None,
        cashboxes=None,
    ):
        self.roles = roles or []
        self.employee = employee
        self.orders = list(orders or [])
        self.work_orders = list(work_orders or [])
        self.batches = list(batches or [])
        self.payments = list(payments or [])
        self.cashboxes = list(cashboxes or [])
        self.utils = types.SimpleNamespace(now_datetime=lambda: datetime(2026, 5, 20, 12, 0, 0))

    def get_roles(self, user):
        if user == "Administrator":
            return ["Administrator"]
        return list(self.roles)

    def get_meta(self, doctype):
        return types.SimpleNamespace(has_field=lambda field: field in {"user_id", "branch", "department"})

    def get_all(self, doctype, filters=None, fields=None, order_by=None, limit=20, start=0):
        if doctype == "Employee":
            rows = [self.employee] if self.employee else []
            filters = None
        else:
            rows = {
                "Madar Order": self.orders,
                "Madar Work Order": self.work_orders,
                "Madar Delivery Batch": self.batches,
                "Madar Payment": self.payments,
                "Madar Cashbox": self.cashboxes,
            }.get(doctype, [])
        rows = _filter_rows(list(rows), filters)
        rows = rows[start : start + limit]
        return [types.SimpleNamespace(**{field: row.get(field) for field in (fields or row.keys())}) for row in rows]


def _filter_rows(rows, filters):
    for key, value in (filters or {}).items():
        if isinstance(value, list) and value[0] == "in":
            rows = [row for row in rows if row.get(key) in value[1]]
        elif isinstance(value, list) and value[0] == "between":
            start, end = value[1]
            rows = [row for row in rows if row.get(key) is not None and start <= row.get(key) <= end]
        else:
            rows = [row for row in rows if row.get(key) == value]
    return rows


if __name__ == "__main__":
    unittest.main()
