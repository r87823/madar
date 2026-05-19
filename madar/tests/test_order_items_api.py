import importlib
import inspect
import sys
import types
import unittest


class OrderItemsApiTest(unittest.TestCase):
    def tearDown(self):
        sys.modules.pop("frappe", None)
        sys.modules.pop("madar.api.order_items", None)

    def test_order_item_methods_are_authenticated_whitelisted_methods(self):
        whitelist_calls = []

        def whitelist(*args, **kwargs):
            whitelist_calls.append({"args": args, "kwargs": kwargs})
            return lambda fn: fn

        sys.modules["frappe"] = types.SimpleNamespace(whitelist=whitelist)

        order_items = importlib.import_module("madar.api.order_items")

        self.assertEqual(len(whitelist_calls), 4)
        self.assertTrue(all(call == {"args": (), "kwargs": {}} for call in whitelist_calls))
        self.assertEqual(
            set(inspect.signature(order_items.add_item).parameters),
            {"order_name", "item_code", "qty", "notes"},
        )

    def test_order_item_methods_use_session_user_and_service_layer(self):
        sys.modules["frappe"] = types.SimpleNamespace(
            whitelist=lambda *args, **kwargs: lambda fn: fn,
            session=types.SimpleNamespace(user="branch.user@example.com"),
        )
        order_items = importlib.import_module("madar.api.order_items")
        calls = []
        order_items.order_item_service = types.SimpleNamespace(
            add_item=lambda user, **kwargs: calls.append(("add", user, kwargs)) or {"ok": True},
            update_item_qty=lambda user, **kwargs: calls.append(("qty", user, kwargs)) or {"ok": True},
            remove_item=lambda user, **kwargs: calls.append(("remove", user, kwargs)) or {"ok": True},
            list_order_items=lambda user, order_name: calls.append(("list", user, order_name)) or {"ok": True},
        )

        order_items.add_item("MADAR-ORD-1", "MILK-001", 2, notes="note")
        order_items.update_item_qty("MADAR-ORD-1", "LINE-1", 3)
        order_items.remove_item("MADAR-ORD-1", "LINE-1")
        order_items.list_order_items("MADAR-ORD-1")

        self.assertEqual(calls[0][0], "add")
        self.assertEqual(calls[0][1], "branch.user@example.com")
        self.assertEqual(calls[-1], ("list", "branch.user@example.com", "MADAR-ORD-1"))


if __name__ == "__main__":
    unittest.main()
