import importlib
import inspect
import sys
import types
import unittest


class OrdersApiTest(unittest.TestCase):
    def tearDown(self):
        sys.modules.pop("frappe", None)
        sys.modules.pop("madar.api.orders", None)

    def test_order_methods_are_authenticated_whitelisted_methods(self):
        whitelist_calls = []

        def whitelist(*args, **kwargs):
            whitelist_calls.append({"args": args, "kwargs": kwargs})
            return lambda fn: fn

        sys.modules["frappe"] = types.SimpleNamespace(whitelist=whitelist)

        orders = importlib.import_module("madar.api.orders")

        self.assertEqual(len(whitelist_calls), 9)
        self.assertTrue(all(call == {"args": (), "kwargs": {}} for call in whitelist_calls))
        self.assertEqual(
            set(inspect.signature(orders.create_draft).parameters),
            {
                "customer_name",
                "customer_phone",
                "notes",
                "fulfillment_method",
                "destination_branch",
            },
        )

    def test_order_methods_reject_guest(self):
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

        orders = importlib.import_module("madar.api.orders")

        with self.assertRaises(AuthenticationError):
            orders.list_orders()

    def test_order_methods_use_session_user_and_service_layer(self):
        sys.modules["frappe"] = types.SimpleNamespace(
            whitelist=lambda *args, **kwargs: lambda fn: fn,
            session=types.SimpleNamespace(user="branch.user@example.com"),
        )
        orders = importlib.import_module("madar.api.orders")
        calls = []
        orders.order_service = types.SimpleNamespace(
            create_draft=lambda user, **kwargs: calls.append(("create", user, kwargs)) or {"ok": True},
            list_orders=lambda user: calls.append(("list", user)) or {"ok": True},
            get_order=lambda user, order_name: calls.append(("get", user, order_name)) or {"ok": True},
            submit_order=lambda user, order_name: calls.append(("submit", user, order_name)) or {"ok": True},
            cancel_order=lambda user, order_name: calls.append(("cancel", user, order_name)) or {"ok": True},
            list_approval_queue=lambda user: calls.append(("queue", user)) or {"ok": True},
            approve_order=lambda user, order_name: calls.append(("approve", user, order_name)) or {"ok": True},
            return_order_for_edit=lambda user, order_name, reason: calls.append(("return", user, order_name, reason)) or {"ok": True},
            reject_order=lambda user, order_name, reason: calls.append(("reject", user, order_name, reason)) or {"ok": True},
        )

        orders.create_draft(customer_name="Customer", customer_phone="05", notes="note")
        orders.list_orders()
        orders.get_order("MADAR-ORD-1")
        orders.submit_order("MADAR-ORD-1")
        orders.cancel_order("MADAR-ORD-1")
        orders.list_approval_queue()
        orders.approve_order("MADAR-ORD-1")
        orders.return_order_for_edit("MADAR-ORD-1", "reason")
        orders.reject_order("MADAR-ORD-1", "reason")

        self.assertEqual(
            calls,
            [
                (
                    "create",
                    "branch.user@example.com",
                    {
                        "customer_name": "Customer",
                        "customer_phone": "05",
                        "notes": "note",
                        "fulfillment_method": "branch_pickup",
                        "destination_branch": None,
                    },
                ),
                ("list", "branch.user@example.com"),
                ("get", "branch.user@example.com", "MADAR-ORD-1"),
                ("submit", "branch.user@example.com", "MADAR-ORD-1"),
                ("cancel", "branch.user@example.com", "MADAR-ORD-1"),
                ("queue", "branch.user@example.com"),
                ("approve", "branch.user@example.com", "MADAR-ORD-1"),
                ("return", "branch.user@example.com", "MADAR-ORD-1", "reason"),
                ("reject", "branch.user@example.com", "MADAR-ORD-1", "reason"),
            ],
        )


if __name__ == "__main__":
    unittest.main()
