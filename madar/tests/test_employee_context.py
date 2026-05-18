import types
import unittest

from madar.services import employee_context


class FakeMeta:
    def __init__(self, fields):
        self._fields = set(fields)

    def has_field(self, fieldname):
        return fieldname in self._fields


class FakeFrappe:
    def __init__(self, meta_fields=None, employee=None, missing_doctype=False, fail=False):
        self._meta_fields = meta_fields or []
        self._employee = employee
        self._missing_doctype = missing_doctype
        self._fail = fail
        self.DoesNotExistError = type("DoesNotExistError", (Exception,), {})

    def get_meta(self, doctype):
        if self._fail:
            raise RuntimeError("lookup failed")
        if doctype != "Employee" or self._missing_doctype:
            raise self.DoesNotExistError("missing")
        return FakeMeta(self._meta_fields)

    def get_all(self, doctype, filters=None, fields=None, limit=20):
        if self._fail:
            raise RuntimeError("lookup failed")
        if doctype != "Employee" or not self._employee:
            return []
        if filters != {"user_id": "worker@example.com"}:
            return []
        return [types.SimpleNamespace(**{field: self._employee.get(field) for field in fields})]


class EmployeeContextTest(unittest.TestCase):
    def test_user_with_linked_employee_returns_employee_context(self):
        fake_frappe = FakeFrappe(
            meta_fields=[
                "user_id",
                "employee_name",
                "company",
                "department",
                "designation",
                "branch",
                "salary",
            ],
            employee={
                "name": "EMP-0001",
                "employee_name": "Worker One",
                "company": "Madar",
                "department": "Operations",
                "designation": "Driver",
                "branch": "Riyadh",
                "salary": 999999,
            },
        )

        self.assertEqual(
            employee_context.get_employee_context("worker@example.com", frappe_module=fake_frappe),
            {
                "name": "EMP-0001",
                "employee_name": "Worker One",
                "company": "Madar",
                "department": "Operations",
                "designation": "Driver",
                "branch": "Riyadh",
            },
        )

    def test_user_without_linked_employee_returns_none(self):
        fake_frappe = FakeFrappe(meta_fields=["user_id", "employee_name"])

        self.assertIsNone(
            employee_context.get_employee_context("worker@example.com", frappe_module=fake_frappe)
        )

    def test_missing_employee_doctype_returns_none(self):
        fake_frappe = FakeFrappe(missing_doctype=True)

        self.assertIsNone(
            employee_context.get_employee_context("worker@example.com", frappe_module=fake_frappe)
        )

    def test_lookup_failure_returns_none(self):
        fake_frappe = FakeFrappe(fail=True)

        self.assertIsNone(
            employee_context.get_employee_context("worker@example.com", frappe_module=fake_frappe)
        )

    def test_employee_context_does_not_expose_sensitive_fields(self):
        fake_frappe = FakeFrappe(
            meta_fields=[
                "user_id",
                "employee_name",
                "company",
                "department",
                "designation",
                "bank_ac_no",
                "passport_number",
            ],
            employee={
                "name": "EMP-0001",
                "employee_name": "Worker One",
                "company": "Madar",
                "department": "Operations",
                "designation": "Driver",
                "bank_ac_no": "hidden",
                "passport_number": "hidden",
            },
        )

        context = employee_context.get_employee_context(
            "worker@example.com", frappe_module=fake_frappe
        )

        self.assertNotIn("bank_ac_no", context)
        self.assertNotIn("passport_number", context)


if __name__ == "__main__":
    unittest.main()
