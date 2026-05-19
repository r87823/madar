import importlib
import inspect
import sys
import types
import unittest


class CatalogApiTest(unittest.TestCase):
    def tearDown(self):
        sys.modules.pop("frappe", None)
        sys.modules.pop("madar.api.catalog", None)

    def test_catalog_method_is_authenticated_whitelisted_method(self):
        whitelist_calls = []

        def whitelist(*args, **kwargs):
            whitelist_calls.append({"args": args, "kwargs": kwargs})
            return lambda fn: fn

        sys.modules["frappe"] = types.SimpleNamespace(whitelist=whitelist)

        catalog = importlib.import_module("madar.api.catalog")

        self.assertEqual(len(whitelist_calls), 1)
        self.assertEqual(whitelist_calls[0], {"args": (), "kwargs": {}})
        self.assertEqual(set(inspect.signature(catalog.list_products).parameters), {"search"})

    def test_catalog_method_uses_session_user(self):
        sys.modules["frappe"] = types.SimpleNamespace(
            whitelist=lambda *args, **kwargs: lambda fn: fn,
            session=types.SimpleNamespace(user="branch.user@example.com"),
        )
        catalog = importlib.import_module("madar.api.catalog")
        calls = []
        catalog.catalog_service = types.SimpleNamespace(
            list_products=lambda user, search="": calls.append((user, search)) or {"ok": True}
        )

        catalog.list_products(search="milk")

        self.assertEqual(calls, [("branch.user@example.com", "milk")])


if __name__ == "__main__":
    unittest.main()
