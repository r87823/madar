import types
import unittest
from datetime import datetime

from madar.services import followup_dashboard_service


class FollowupDashboardServiceTest(unittest.TestCase):
    def test_system_full_access_receives_all_core_cards(self):
        fake_frappe = FakeFrappe(
            roles=["Madar Admin"],
            employee=None,
            orders=[
                _order("ORD-1", "Main Branch", status="submitted"),
                _order("ORD-2", "HQ", delivery_status="ready_for_dispatch"),
                _order("ORD-3", "HQ", erp_sync_status="failed", accounting_status="ready_for_review"),
                _order("ORD-4", "HQ", erp_invoice_sync_status="failed"),
            ],
            work_orders=[
                _work_order("WO-1", "Production", "in_production"),
                _work_order("WO-2", "Delivery", "delayed"),
            ],
            batches=[
                _batch("BATCH-1", driver_user="driver.test@example.com", status="assigned"),
                _batch("BATCH-2", driver_user="other@example.com", status="out_for_delivery"),
            ],
            payments=[
                _payment("PAY-1", "Main Branch", "cashier.test@example.com", erp_sync_status="failed"),
            ],
            cashboxes=[_cashbox("CASHBOX-1", "cashier.test@example.com", "submitted")],
            notifications=[_notification("NOTIF-1", "Administrator", is_read=0)],
        )

        result = followup_dashboard_service.get_summary(
            "Administrator",
            frappe_module=fake_frappe,
        )

        self.assertEqual(result["ok"], True)
        cards = _cards(result)
        self.assertEqual(cards["orders_today"]["value"], 4)
        self.assertEqual(cards["orders_pending_approval"]["value"], 1)
        self.assertEqual(cards["production_in_progress"]["value"], 1)
        self.assertEqual(cards["production_delayed"]["priority"], "high")
        self.assertEqual(cards["ready_for_dispatch"]["value"], 1)
        self.assertEqual(cards["active_delivery_batches"]["value"], 2)
        self.assertEqual(cards["payments_today"]["value"], 1)
        self.assertEqual(cards["cashboxes_waiting_review"]["value"], 1)
        self.assertEqual(cards["erp_sync_failed"]["value"], 3)
        self.assertEqual(cards["accounting_ready_for_review"]["value"], 1)
        self.assertEqual(cards["unread_notifications"]["value"], 1)
        self.assertNotIn("customer_phone", str(result["data"]))

    def test_branch_user_receives_branch_scoped_order_cards_only(self):
        fake_frappe = FakeFrappe(
            roles=["Madar Employee", "Madar Branch User"],
            employee={"branch": "Main Branch", "department": "Branch Operations"},
            orders=[
                _order("ORD-1", "Main Branch"),
                _order("ORD-2", "HQ"),
            ],
            notifications=[_notification("NOTIF-1", "branch.user@example.com", is_read=0)],
        )

        result = followup_dashboard_service.get_summary(
            "branch.user@example.com",
            frappe_module=fake_frappe,
        )

        cards = _cards(result)
        self.assertEqual(set(cards), {"orders_today", "unread_notifications", "attendance_state"})
        self.assertEqual(cards["orders_today"]["value"], 1)

    def test_branch_supervisor_sees_pending_approval_scoped_to_branch(self):
        fake_frappe = FakeFrappe(
            roles=["Madar Employee", "Madar Branch Supervisor"],
            employee={"branch": "Main Branch", "department": "Branch Operations"},
            orders=[
                _order("ORD-1", "Main Branch", status="submitted"),
                _order("ORD-2", "HQ", status="submitted"),
                _order("ORD-3", "Main Branch", status="draft"),
            ],
        )

        result = followup_dashboard_service.get_summary(
            "branch.supervisor@example.com",
            frappe_module=fake_frappe,
        )

        cards = _cards(result)
        self.assertEqual(cards["orders_pending_approval"]["value"], 1)
        self.assertEqual(cards["orders_today"]["value"], 2)

    def test_driver_sees_only_assigned_active_batches(self):
        fake_frappe = FakeFrappe(
            roles=["Madar Employee", "Madar Driver"],
            employee={"branch": "Main Branch", "department": "Delivery"},
            batches=[
                _batch("BATCH-1", driver_user="driver.test@example.com", status="assigned"),
                _batch("BATCH-2", driver_user="driver.test@example.com", status="completed"),
                _batch("BATCH-3", driver_user="other@example.com", status="assigned"),
            ],
        )

        result = followup_dashboard_service.get_summary(
            "driver.test@example.com",
            frappe_module=fake_frappe,
        )

        cards = _cards(result)
        self.assertEqual(cards["active_delivery_batches"]["value"], 1)
        self.assertNotIn("orders_today", cards)

    def test_accountant_sees_accounting_cards_and_high_failed_sync_alert(self):
        fake_frappe = FakeFrappe(
            roles=["Madar Accountant"],
            orders=[
                _order("ORD-1", "Main Branch", erp_sync_status="failed"),
                _order("ORD-2", "Main Branch", accounting_status="ready_for_review"),
            ],
            payments=[_payment("PAY-1", "Main Branch", "cashier.test@example.com", erp_sync_status="failed")],
            cashboxes=[_cashbox("CASHBOX-1", "cashier.test@example.com", "submitted")],
        )

        result = followup_dashboard_service.get_summary(
            "accountant.test@example.com",
            frappe_module=fake_frappe,
        )

        cards = _cards(result)
        alerts = _alerts(result)
        self.assertEqual(cards["erp_sync_failed"]["value"], 2)
        self.assertEqual(cards["cashboxes_waiting_review"]["value"], 1)
        self.assertEqual(cards["accounting_ready_for_review"]["value"], 1)
        self.assertEqual(alerts["erp_sync_failed"]["priority"], "high")
        self.assertEqual(alerts["cashboxes_waiting_review"]["priority"], "high")

    def test_employee_without_broad_permissions_gets_basic_cards_only(self):
        fake_frappe = FakeFrappe(
            roles=["Madar Employee"],
            employee={"branch": "Main Branch", "department": "General"},
            orders=[_order("ORD-1", "Main Branch")],
            notifications=[_notification("NOTIF-1", "employee.test@example.com", is_read=0)],
        )

        result = followup_dashboard_service.get_summary(
            "employee.test@example.com",
            frappe_module=fake_frappe,
        )

        cards = _cards(result)
        self.assertEqual(set(cards), {"unread_notifications", "attendance_state"})
        self.assertEqual(cards["unread_notifications"]["value"], 1)


def _cards(result):
    return {card["key"]: card for card in result["data"]["cards"]}


def _alerts(result):
    return {alert["key"]: alert for alert in result["data"]["alerts"]}


def _order(
    name,
    branch,
    *,
    status="draft",
    delivery_status="not_ready",
    erp_sync_status="pending",
    erp_invoice_sync_status="pending",
    accounting_status="not_ready",
):
    return {
        "doctype": "Madar Order",
        "name": name,
        "assigned_branch": branch,
        "branch": branch,
        "order_status": status,
        "delivery_status": delivery_status,
        "erp_sync_status": erp_sync_status,
        "erp_invoice_sync_status": erp_invoice_sync_status,
        "accounting_status": accounting_status,
        "creation": datetime(2026, 5, 20, 9, 0, 0),
        "modified": name,
    }


def _work_order(name, department, status):
    return {
        "doctype": "Madar Work Order",
        "name": name,
        "production_department": department,
        "status": status,
        "modified": name,
    }


def _batch(name, *, driver_user, status):
    return {
        "doctype": "Madar Delivery Batch",
        "name": name,
        "driver_user": driver_user,
        "status": status,
        "modified": name,
    }


def _payment(name, branch, user, erp_sync_status="pending"):
    return {
        "doctype": "Madar Payment",
        "name": name,
        "madar_order": "ORD-1",
        "collected_by_user": user,
        "branch": branch,
        "amount": 50,
        "erp_sync_status": erp_sync_status,
        "creation": datetime(2026, 5, 20, 10, 0, 0),
        "modified": name,
    }


def _cashbox(name, user, status):
    return {
        "doctype": "Madar Cashbox",
        "name": name,
        "user": user,
        "status": status,
        "modified": name,
    }


def _notification(name, user, is_read=0):
    return {
        "doctype": "Madar Notification",
        "name": name,
        "recipient_user": user,
        "is_read": is_read,
        "modified": name,
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
        notifications=None,
    ):
        self.roles = roles or []
        self.employee = employee
        self.orders = list(orders or [])
        self.work_orders = list(work_orders or [])
        self.batches = list(batches or [])
        self.payments = list(payments or [])
        self.cashboxes = list(cashboxes or [])
        self.notifications = list(notifications or [])
        self.utils = types.SimpleNamespace(now_datetime=lambda: datetime(2026, 5, 20, 12, 0, 0))

    def get_roles(self, user):
        if user == "Administrator":
            return ["Administrator"]
        return list(self.roles)

    def get_meta(self, doctype):
        return types.SimpleNamespace(has_field=lambda field: field in {"user_id", "branch", "department"})

    def get_all(self, doctype, filters=None, fields=None, order_by=None, limit=20):
        if doctype == "Employee":
            rows = [self.employee] if self.employee else []
            return [types.SimpleNamespace(**{field: row.get(field) for field in (fields or row.keys())}) for row in rows[:limit]]
        rows = {
            "Madar Order": self.orders,
            "Madar Work Order": self.work_orders,
            "Madar Delivery Batch": self.batches,
            "Madar Payment": self.payments,
            "Madar Cashbox": self.cashboxes,
            "Madar Notification": self.notifications,
        }.get(doctype, [])
        rows = _filter_rows(list(rows), filters)
        return [types.SimpleNamespace(**{field: row.get(field) for field in (fields or row.keys())}) for row in rows[:limit]]


def _filter_rows(rows, filters):
    for key, value in (filters or {}).items():
        if isinstance(value, list) and value[0] == "in":
            rows = [row for row in rows if row.get(key) in value[1]]
        elif isinstance(value, list) and value[0] == "!=":
            rows = [row for row in rows if row.get(key) != value[1]]
        elif isinstance(value, list) and value[0] == "between":
            start, end = value[1]
            rows = [row for row in rows if start <= row.get(key) <= end]
        else:
            rows = [row for row in rows if row.get(key) == value]
    return rows


if __name__ == "__main__":
    unittest.main()
