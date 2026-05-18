import types
import unittest

from madar.permissions import checks, registry, roles
from madar.patches.v0_0 import create_madar_roles


class MadarRoleRegistryTest(unittest.TestCase):
    def test_role_constants_include_all_madar_roles(self):
        self.assertEqual(
            roles.MADAR_ROLES,
            [
                "Madar Admin",
                "Madar Employee",
                "Madar Branch User",
                "Madar Branch Supervisor",
                "Madar Production User",
                "Madar Driver",
                "Madar Cashier",
                "Madar Accountant",
            ],
        )

    def test_registry_maps_madar_roles_to_expected_permissions(self):
        self.assertEqual(checks.get_permissions_for_roles(["Madar Admin"]), registry.ALL_PERMISSION_KEYS)
        self.assertEqual(
            checks.get_permissions_for_roles(["Madar Employee"]),
            [
                "attendance.check_in",
                "attendance.check_out",
                "employee_services.view_self",
                "employee_services.request_leave",
            ],
        )
        self.assertEqual(
            checks.get_permissions_for_roles(["Madar Branch User"]),
            ["orders.create", "orders.submit_for_approval"],
        )
        self.assertEqual(checks.get_permissions_for_roles(["Madar Branch Supervisor"]), ["orders.approve"])
        self.assertEqual(
            checks.get_permissions_for_roles(["Madar Production User"]),
            ["production.view_work_orders", "production.update_work_order"],
        )
        self.assertEqual(
            checks.get_permissions_for_roles(["Madar Driver"]),
            [
                "delivery.view_assigned_batches",
                "delivery.update_batch",
                "payments.collect",
                "cashbox.view_own",
                "cashbox.submit",
            ],
        )
        self.assertEqual(
            checks.get_permissions_for_roles(["Madar Cashier"]),
            ["payments.collect", "cashbox.view_own", "cashbox.submit"],
        )
        self.assertEqual(
            checks.get_permissions_for_roles(["Madar Accountant"]),
            ["accounting.view_sync_logs"],
        )

    def test_system_full_access_still_grants_all_permissions(self):
        self.assertEqual(checks.get_permissions_for_roles(["Madar Admin"]), registry.ALL_PERMISSION_KEYS)
        self.assertEqual(checks.get_permissions_for_roles(["System Manager"]), registry.ALL_PERMISSION_KEYS)

    def test_duplicate_permissions_are_removed_for_madar_roles(self):
        self.assertEqual(
            checks.get_permissions_for_roles(["Madar Driver", "Madar Cashier"]),
            [
                "delivery.view_assigned_batches",
                "delivery.update_batch",
                "payments.collect",
                "cashbox.view_own",
                "cashbox.submit",
            ],
        )

    def test_unknown_roles_return_no_permissions(self):
        self.assertEqual(checks.get_permissions_for_roles(["Madar Unknown"]), [])

    def test_role_patch_is_idempotent(self):
        fake_frappe = _FakeFrappe(existing_roles={"Madar Admin"})

        create_madar_roles.execute(frappe_module=fake_frappe)
        create_madar_roles.execute(frappe_module=fake_frappe)

        self.assertEqual(fake_frappe.inserted_roles.count("Madar Admin"), 0)
        self.assertEqual(set(fake_frappe.inserted_roles), set(roles.MADAR_ROLES) - {"Madar Admin"})
        self.assertEqual(fake_frappe.commits, 2)


class _FakeFrappe:
    def __init__(self, existing_roles=None):
        self.existing_roles = set(existing_roles or [])
        self.inserted_roles = []
        self.commits = 0
        self.db = types.SimpleNamespace(exists=self.exists, commit=self.commit)

    def exists(self, doctype, name):
        return doctype == "Role" and name in self.existing_roles

    def get_doc(self, values):
        role_name = values["role_name"]

        class _Doc:
            def insert(_, ignore_permissions=False):
                self.existing_roles.add(role_name)
                self.inserted_roles.append(role_name)

        return _Doc()

    def commit(self):
        self.commits += 1


if __name__ == "__main__":
    unittest.main()
