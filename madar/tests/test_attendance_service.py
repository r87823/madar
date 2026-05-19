import types
import unittest
from datetime import datetime, timedelta

from madar.services import attendance_service


class AttendanceServiceTest(unittest.TestCase):
    def test_get_status_returns_unknown_without_checkins(self):
        fake_frappe = FakeFrappe()

        result = attendance_service.get_status(
            "employee.test@example.com",
            frappe_module=fake_frappe,
        )

        self.assertEqual(result["ok"], True)
        self.assertEqual(result["data"]["state"], "unknown")
        self.assertIsNone(result["data"]["last_checkin"])
        self.assertEqual(result["data"]["employee"]["name"], "EMP-0001")
        self.assertNotIn("bank_ac_no", result["data"]["employee"])

    def test_check_in_creates_employee_checkin_with_server_time_and_internal_log_type(self):
        server_time = datetime(2026, 5, 19, 8, 30, 0)
        fake_frappe = FakeFrappe(now=server_time)

        result = attendance_service.check_in(
            "employee.test@example.com",
            frappe_module=fake_frappe,
        )

        self.assertEqual(result["ok"], True)
        self.assertEqual(result["data"]["state"], "in_work")
        self.assertEqual(len(fake_frappe.created_checkins), 1)
        checkin = fake_frappe.created_checkins[0]
        self.assertEqual(checkin["employee"], "EMP-0001")
        self.assertEqual(checkin["time"], server_time)
        self.assertEqual(checkin["log_type"], "IN")

    def test_check_out_creates_employee_checkin_with_internal_out_log_type(self):
        server_time = datetime(2026, 5, 19, 17, 15, 0)
        fake_frappe = FakeFrappe(now=server_time)

        result = attendance_service.check_out(
            "employee.test@example.com",
            frappe_module=fake_frappe,
        )

        self.assertEqual(result["ok"], True)
        self.assertEqual(result["data"]["state"], "out_of_work")
        self.assertEqual(fake_frappe.created_checkins[0]["log_type"], "OUT")

    def test_check_in_requires_attendance_permission(self):
        fake_frappe = FakeFrappe(roles=["Madar Accountant"])

        result = attendance_service.check_in(
            "employee.test@example.com",
            frappe_module=fake_frappe,
        )

        self.assertEqual(result["ok"], False)
        self.assertEqual(result["error"]["code"], "PERMISSION_DENIED")
        self.assertEqual(fake_frappe.created_checkins, [])

    def test_requires_linked_employee(self):
        fake_frappe = FakeFrappe(employee=None)

        result = attendance_service.check_in(
            "employee.test@example.com",
            frappe_module=fake_frappe,
        )

        self.assertEqual(result["ok"], False)
        self.assertEqual(result["error"]["code"], "EMPLOYEE_NOT_LINKED")

    def test_missing_employee_checkin_doctype_returns_safe_error(self):
        fake_frappe = FakeFrappe(checkin_available=False)

        result = attendance_service.get_status(
            "employee.test@example.com",
            frappe_module=fake_frappe,
        )

        self.assertEqual(result["ok"], False)
        self.assertEqual(result["error"]["code"], "EMPLOYEE_CHECKIN_UNAVAILABLE")
        self.assertNotIn("Traceback", result["error"]["message"])

    def test_duplicate_same_action_within_short_window_is_rejected(self):
        server_time = datetime(2026, 5, 19, 8, 30, 30)
        fake_frappe = FakeFrappe(
            now=server_time,
            checkins=[
                {
                    "name": "CHK-1",
                    "employee": "EMP-0001",
                    "time": server_time - timedelta(seconds=30),
                    "log_type": "IN",
                }
            ],
        )

        result = attendance_service.check_in(
            "employee.test@example.com",
            frappe_module=fake_frappe,
        )

        self.assertEqual(result["ok"], False)
        self.assertEqual(result["error"]["code"], "DUPLICATE_CHECKIN")
        self.assertEqual(fake_frappe.created_checkins, [])


class FakeMeta:
    def __init__(self, fields):
        self._fields = set(fields)

    def has_field(self, fieldname):
        return fieldname in self._fields


_DEFAULT_EMPLOYEE = object()


class FakeFrappe:
    def __init__(
        self,
        *,
        roles=None,
        employee=_DEFAULT_EMPLOYEE,
        checkins=None,
        checkin_available=True,
        now=None,
    ):
        self.roles = roles or ["Madar Employee"]
        self.employee = (
            {
                "name": "EMP-0001",
                "employee_name": "Madar Dev Employee",
                "company": "test",
                "department": "General - T",
                "designation": "Madar Dev Test User",
                "branch": "Main Branch",
                "bank_ac_no": "hidden",
            }
            if employee is _DEFAULT_EMPLOYEE
            else employee
        )
        self.checkins = list(checkins or [])
        self.checkin_available = checkin_available
        self.created_checkins = []
        self.db = types.SimpleNamespace(commit=lambda: None)
        self.utils = types.SimpleNamespace(now_datetime=lambda: now or datetime(2026, 5, 19, 9, 0, 0))

    def get_roles(self, user):
        return list(self.roles)

    def get_meta(self, doctype):
        if doctype == "Employee":
            return FakeMeta(
                [
                    "user_id",
                    "employee_name",
                    "company",
                    "department",
                    "designation",
                    "branch",
                    "bank_ac_no",
                ]
            )
        if doctype == "Employee Checkin" and self.checkin_available:
            return FakeMeta(["employee", "time", "log_type"])
        raise RuntimeError(f"{doctype} unavailable")

    def get_all(self, doctype, filters=None, fields=None, limit=20, order_by=None):
        if doctype == "Employee":
            if not self.employee:
                return []
            if filters != {"user_id": "employee.test@example.com"}:
                return []
            return [types.SimpleNamespace(**{field: self.employee.get(field) for field in fields})]

        if doctype == "Employee Checkin":
            rows = [
                row
                for row in self.checkins
                if not filters or row.get("employee") == filters.get("employee")
            ]
            rows.sort(key=lambda row: row["time"], reverse=True)
            return [types.SimpleNamespace(**{field: row.get(field) for field in fields}) for row in rows[:limit]]

        return []

    def get_doc(self, values):
        class _Doc:
            def insert(_, ignore_permissions=False):
                self.created_checkins.append(values)
                self.checkins.append({"name": "NEW-CHECKIN", **values})
                return types.SimpleNamespace(name="NEW-CHECKIN", **values)

        return _Doc()


if __name__ == "__main__":
    unittest.main()
