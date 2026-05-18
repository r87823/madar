import types
import unittest

from madar.services import branch_context


class FakeMeta:
    def __init__(self, fields):
        self._fields = set(fields)

    def has_field(self, fieldname):
        return fieldname in self._fields


class FakeFrappe:
    def __init__(self, meta_fields=None, branch=None, missing_doctype=False, fail=False):
        self._meta_fields = meta_fields or []
        self._branch = branch
        self._missing_doctype = missing_doctype
        self._fail = fail
        self.DoesNotExistError = type("DoesNotExistError", (Exception,), {})

    def get_meta(self, doctype):
        if self._fail:
            raise RuntimeError("lookup failed")
        if doctype != "Branch" or self._missing_doctype:
            raise self.DoesNotExistError("missing")
        return FakeMeta(self._meta_fields)

    def get_all(self, doctype, filters=None, fields=None, limit=20):
        if self._fail:
            raise RuntimeError("lookup failed")
        if doctype != "Branch" or not self._branch:
            return []
        if filters != {"name": "Riyadh"}:
            return []
        return [types.SimpleNamespace(**{field: self._branch.get(field) for field in fields})]


class BranchContextTest(unittest.TestCase):
    def test_employee_with_branch_returns_branch_context(self):
        fake_frappe = FakeFrappe(
            meta_fields=["branch", "company", "private_notes"],
            branch={
                "name": "Riyadh",
                "branch": "Riyadh Central",
                "company": "Madar",
                "private_notes": "hidden",
            },
        )

        self.assertEqual(
            branch_context.get_branch_context(
                {"branch": "Riyadh", "department": "Delivery"}, frappe_module=fake_frappe
            ),
            {
                "name": "Riyadh",
                "branch": "Riyadh Central",
                "company": "Madar",
            },
        )

    def test_employee_without_branch_returns_none(self):
        self.assertIsNone(branch_context.get_branch_context({"department": "Delivery"}))

    def test_missing_branch_doctype_returns_safe_minimal_branch(self):
        fake_frappe = FakeFrappe(missing_doctype=True)

        self.assertEqual(
            branch_context.get_branch_context({"branch": "Riyadh"}, frappe_module=fake_frappe),
            {"name": "Riyadh", "branch": "Riyadh"},
        )

    def test_branch_lookup_failure_returns_safe_minimal_branch(self):
        fake_frappe = FakeFrappe(fail=True)

        self.assertEqual(
            branch_context.get_branch_context({"branch": "Riyadh"}, frappe_module=fake_frappe),
            {"name": "Riyadh", "branch": "Riyadh"},
        )

    def test_branch_context_does_not_expose_sensitive_fields(self):
        fake_frappe = FakeFrappe(
            meta_fields=["branch", "company", "private_notes"],
            branch={
                "name": "Riyadh",
                "branch": "Riyadh Central",
                "company": "Madar",
                "private_notes": "hidden",
            },
        )

        context = branch_context.get_branch_context({"branch": "Riyadh"}, frappe_module=fake_frappe)

        self.assertNotIn("private_notes", context)


if __name__ == "__main__":
    unittest.main()
