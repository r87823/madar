import importlib
import inspect
import sys
import types
import unittest


class WorkOrdersApiTest(unittest.TestCase):
    def tearDown(self):
        sys.modules.pop("frappe", None)
        sys.modules.pop("madar.api.work_orders", None)

    def test_work_order_methods_are_authenticated_whitelisted_methods(self):
        whitelist_calls = []

        def whitelist(*args, **kwargs):
            whitelist_calls.append({"args": args, "kwargs": kwargs})
            return lambda fn: fn

        sys.modules["frappe"] = types.SimpleNamespace(whitelist=whitelist)

        api = importlib.import_module("madar.api.work_orders")

        self.assertEqual(len(whitelist_calls), 7)
        self.assertTrue(all(call == {"args": (), "kwargs": {}} for call in whitelist_calls))
        self.assertEqual(set(inspect.signature(api.create_work_orders_from_order).parameters), {"order_name"})
        self.assertEqual(set(inspect.signature(api.list_work_orders).parameters), set())
        self.assertEqual(set(inspect.signature(api.get_work_order).parameters), {"work_order_name"})
        self.assertEqual(
            set(inspect.signature(api.mark_work_order_delayed).parameters),
            {"work_order_name", "reason"},
        )

    def test_work_order_methods_reject_guest(self):
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

        api = importlib.import_module("madar.api.work_orders")

        with self.assertRaises(AuthenticationError):
            api.list_work_orders()

    def test_work_order_methods_delegate_to_service_layer(self):
        sys.modules["frappe"] = types.SimpleNamespace(
            whitelist=lambda *args, **kwargs: lambda fn: fn,
            session=types.SimpleNamespace(user="production.user@example.com"),
        )
        api = importlib.import_module("madar.api.work_orders")
        calls = []
        api.work_order_service = types.SimpleNamespace(
            create_work_orders_from_order=lambda user, order_name: calls.append(("create", user, order_name))
            or {"ok": True},
            list_work_orders=lambda user: calls.append(("list", user)) or {"ok": True},
            get_work_order=lambda user, work_order_name: calls.append(("get", user, work_order_name))
            or {"ok": True},
            accept_work_order=lambda user, work_order_name: calls.append(("accept", user, work_order_name))
            or {"ok": True},
            start_work_order=lambda user, work_order_name: calls.append(("start", user, work_order_name))
            or {"ok": True},
            mark_work_order_ready=lambda user, work_order_name: calls.append(("ready", user, work_order_name))
            or {"ok": True},
            mark_work_order_delayed=lambda user, work_order_name, reason: calls.append(
                ("delay", user, work_order_name, reason)
            )
            or {"ok": True},
        )

        api.create_work_orders_from_order("MADAR-ORD-1")
        api.list_work_orders()
        api.get_work_order("WO-1")
        api.accept_work_order("WO-1")
        api.start_work_order("WO-1")
        api.mark_work_order_ready("WO-1")
        api.mark_work_order_delayed("WO-1", "Machine issue")

        self.assertEqual(
            calls,
            [
                ("create", "production.user@example.com", "MADAR-ORD-1"),
                ("list", "production.user@example.com"),
                ("get", "production.user@example.com", "WO-1"),
                ("accept", "production.user@example.com", "WO-1"),
                ("start", "production.user@example.com", "WO-1"),
                ("ready", "production.user@example.com", "WO-1"),
                ("delay", "production.user@example.com", "WO-1", "Machine issue"),
            ],
        )


if __name__ == "__main__":
    unittest.main()
