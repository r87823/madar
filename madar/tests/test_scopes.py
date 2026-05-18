import unittest

from madar.permissions import scopes


class ScopeHelperTest(unittest.TestCase):
    def test_scopes_include_employee_branch_and_department(self):
        self.assertEqual(
            scopes.get_context_scopes(
                employee={"branch": "Riyadh", "department": "Delivery"},
                permissions=["attendance.check_in"],
            ),
            {
                "branch_names": ["Riyadh"],
                "department_names": ["Delivery"],
            },
        )

    def test_scopes_are_empty_without_employee_values(self):
        self.assertEqual(
            scopes.get_context_scopes(employee=None, permissions=[]),
            {
                "branch_names": [],
                "department_names": [],
            },
        )

    def test_system_full_access_returns_wildcard_scopes(self):
        self.assertEqual(
            scopes.get_context_scopes(
                employee={"branch": "Riyadh", "department": "Delivery"},
                permissions=["system.full_access"],
            ),
            {
                "branch_names": ["*"],
                "department_names": ["*"],
            },
        )

    def test_duplicate_scope_values_are_removed(self):
        self.assertEqual(
            scopes.get_context_scopes(
                employee={"branch": "Riyadh", "department": "Riyadh"},
                permissions=[],
            ),
            {
                "branch_names": ["Riyadh"],
                "department_names": ["Riyadh"],
            },
        )


if __name__ == "__main__":
    unittest.main()
