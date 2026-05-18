import unittest

from madar.permissions import checks, registry


class PermissionRegistryTest(unittest.TestCase):
    def test_registry_returns_permissions_for_roles(self):
        self.assertEqual(
            checks.get_permissions_for_roles(["Employee"]),
            [
                "attendance.check_in",
                "attendance.check_out",
                "employee_services.view_self",
                "employee_services.request_leave",
            ],
        )

    def test_system_full_access_grants_all_permissions(self):
        permissions = checks.get_permissions_for_roles(["System Manager"])

        self.assertEqual(permissions, registry.ALL_PERMISSION_KEYS)
        self.assertIn("system.full_access", permissions)
        self.assertTrue(checks.has_permission(["System Manager"], "cashbox.submit"))

    def test_duplicate_permissions_are_removed(self):
        self.assertEqual(
            checks.get_permissions_for_roles(["Driver", "Cashier"]),
            [
                "delivery.view_assigned_batches",
                "delivery.update_batch",
                "payments.collect",
                "cashbox.view_own",
                "cashbox.submit",
            ],
        )

    def test_unknown_roles_return_no_permissions(self):
        self.assertEqual(checks.get_permissions_for_roles(["Mystery Role"]), [])
        self.assertFalse(checks.has_permission(["Mystery Role"], "orders.create"))

    def test_context_helper_does_not_expose_credentials(self):
        context = checks.build_user_context(
            user="mobile@example.com",
            full_name="Mobile User",
            roles=["Employee"],
            api_key="hidden",
            api_secret="hidden",
            password="hidden",
            sid="hidden",
        )

        self.assertEqual(
            context,
            {
                "user": "mobile@example.com",
                "full_name": "Mobile User",
                "roles": ["Employee"],
                "permissions": [
                    "attendance.check_in",
                    "attendance.check_out",
                    "employee_services.view_self",
                    "employee_services.request_leave",
                ],
                "employee": None,
                "branch": None,
            },
        )
        self.assertNotIn("api_key", context)
        self.assertNotIn("api_secret", context)
        self.assertNotIn("password", context)
        self.assertNotIn("sid", context)


if __name__ == "__main__":
    unittest.main()
