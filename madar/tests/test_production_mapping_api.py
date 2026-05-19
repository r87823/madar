import importlib
import inspect
import sys
import types
import unittest


class ProductionMappingApiTest(unittest.TestCase):
    def tearDown(self):
        sys.modules.pop("frappe", None)
        sys.modules.pop("madar.api.production_mapping", None)

    def test_production_mapping_methods_are_authenticated_whitelisted_methods(self):
        whitelist_calls = []

        def whitelist(*args, **kwargs):
            whitelist_calls.append({"args": args, "kwargs": kwargs})
            return lambda fn: fn

        sys.modules["frappe"] = types.SimpleNamespace(whitelist=whitelist)

        api = importlib.import_module("madar.api.production_mapping")

        self.assertEqual(len(whitelist_calls), 7)
        self.assertTrue(all(call == {"args": (), "kwargs": {}} for call in whitelist_calls))
        self.assertEqual(set(inspect.signature(api.list_production_centers).parameters), set())
        self.assertEqual(
            set(inspect.signature(api.create_or_update_item_department_mapping).parameters),
            {"item_code", "production_center", "production_department", "is_active"},
        )

    def test_production_mapping_methods_reject_guest(self):
        class AuthenticationError(Exception):
            pass

        def throw(message, exc):
            raise exc(message)

        sys.modules["frappe"] = types.SimpleNamespace(
            whitelist=lambda *args, **kwargs: lambda fn: fn,
            session=types.SimpleNamespace(user="Guest"),
            AuthenticationError=AuthenticationError,
            throw=throw,
        )

        api = importlib.import_module("madar.api.production_mapping")

        with self.assertRaises(AuthenticationError):
            api.list_production_centers()

    def test_production_mapping_methods_delegate_to_service_layer(self):
        sys.modules["frappe"] = types.SimpleNamespace(
            whitelist=lambda *args, **kwargs: lambda fn: fn,
            session=types.SimpleNamespace(user="Administrator"),
        )
        api = importlib.import_module("madar.api.production_mapping")
        calls = []
        api.production_mapping_service = types.SimpleNamespace(
            list_production_centers=lambda user: calls.append(("centers", user)) or {"ok": True},
            list_production_departments=lambda user, production_center=None: calls.append(
                ("departments", user, production_center)
            )
            or {"ok": True},
            list_item_department_mappings=lambda user: calls.append(("mappings", user)) or {"ok": True},
            create_or_update_production_center=lambda user, center_name, center_code, is_active=1: calls.append(
                ("center", user, center_name, center_code, is_active)
            )
            or {"ok": True},
            create_or_update_production_department=lambda user, department_name, department_code, production_center, is_active=1: calls.append(
                ("department", user, department_name, department_code, production_center, is_active)
            )
            or {"ok": True},
            create_or_update_item_department_mapping=lambda user, item_code, production_center, production_department, is_active=1: calls.append(
                ("mapping", user, item_code, production_center, production_department, is_active)
            )
            or {"ok": True},
            validate_order_department_mappings=lambda user, order_name: calls.append(("validate", user, order_name))
            or {"ok": True},
        )

        api.list_production_centers()
        api.list_production_departments(production_center="MAIN")
        api.list_item_department_mappings()
        api.create_or_update_production_center("Main", "MAIN")
        api.create_or_update_production_department("Milk", "MILK", "MAIN")
        api.create_or_update_item_department_mapping("MILK-001", "MAIN", "MILK")
        api.validate_order_department_mappings("MADAR-ORD-1")

        self.assertEqual(
            calls,
            [
                ("centers", "Administrator"),
                ("departments", "Administrator", "MAIN"),
                ("mappings", "Administrator"),
                ("center", "Administrator", "Main", "MAIN", 1),
                ("department", "Administrator", "Milk", "MILK", "MAIN", 1),
                ("mapping", "Administrator", "MILK-001", "MAIN", "MILK", 1),
                ("validate", "Administrator", "MADAR-ORD-1"),
            ],
        )


if __name__ == "__main__":
    unittest.main()
