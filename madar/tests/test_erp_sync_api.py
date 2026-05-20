import importlib
import inspect
import sys
import types
import unittest


class ErpSyncApiTest(unittest.TestCase):
    def tearDown(self):
        sys.modules.pop("frappe", None)
        sys.modules.pop("madar.api.erp_sync", None)

    def test_erp_sync_methods_are_authenticated_whitelisted_methods(self):
        whitelist_calls = []

        def whitelist(*args, **kwargs):
            whitelist_calls.append({"args": args, "kwargs": kwargs})
            return lambda fn: fn

        sys.modules["frappe"] = types.SimpleNamespace(whitelist=whitelist)

        erp_sync = importlib.import_module("madar.api.erp_sync")

        self.assertEqual(len(whitelist_calls), 7)
        self.assertTrue(all(call == {"args": (), "kwargs": {}} for call in whitelist_calls))
        self.assertEqual(set(inspect.signature(erp_sync.list_sync_orders).parameters), set())
        self.assertEqual(set(inspect.signature(erp_sync.get_sync_order).parameters), {"order_name"})
        self.assertEqual(set(inspect.signature(erp_sync.retry_sync_order).parameters), {"order_name"})
        self.assertEqual(set(inspect.signature(erp_sync.submit_erp_sales_order).parameters), {"order_name"})
        self.assertEqual(set(inspect.signature(erp_sync.list_invoice_sync_orders).parameters), set())
        self.assertEqual(set(inspect.signature(erp_sync.get_invoice_sync_order).parameters), {"order_name"})
        self.assertEqual(set(inspect.signature(erp_sync.retry_invoice_sync).parameters), {"order_name"})

    def test_erp_sync_methods_reject_guest(self):
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

        erp_sync = importlib.import_module("madar.api.erp_sync")

        with self.assertRaises(AuthenticationError):
            erp_sync.list_sync_orders()

    def test_erp_sync_methods_delegate_to_service_layer(self):
        sys.modules["frappe"] = types.SimpleNamespace(
            whitelist=lambda *args, **kwargs: lambda fn: fn,
            session=types.SimpleNamespace(user="accountant.test@example.com"),
        )
        erp_sync = importlib.import_module("madar.api.erp_sync")
        calls = []
        erp_sync.erp_sync_service = types.SimpleNamespace(
            list_sync_orders=lambda user: calls.append(("list", user)) or {"ok": True},
            get_sync_order=lambda user, order_name: calls.append(("get", user, order_name)) or {"ok": True},
            retry_sync_order=lambda user, order_name: calls.append(("retry", user, order_name)) or {"ok": True},
            submit_erp_sales_order_for_user=lambda user, order_name: calls.append(("submit_so", user, order_name))
            or {"ok": True},
            list_invoice_sync_orders=lambda user: calls.append(("list_invoice", user)) or {"ok": True},
            get_invoice_sync_order=lambda user, order_name: calls.append(("get_invoice", user, order_name))
            or {"ok": True},
            retry_invoice_sync=lambda user, order_name: calls.append(("retry_invoice", user, order_name))
            or {"ok": True},
        )

        erp_sync.list_sync_orders()
        erp_sync.get_sync_order("MADAR-ORD-1")
        erp_sync.retry_sync_order("MADAR-ORD-1")
        erp_sync.submit_erp_sales_order("MADAR-ORD-1")
        erp_sync.list_invoice_sync_orders()
        erp_sync.get_invoice_sync_order("MADAR-ORD-1")
        erp_sync.retry_invoice_sync("MADAR-ORD-1")

        self.assertEqual(
            calls,
            [
                ("list", "accountant.test@example.com"),
                ("get", "accountant.test@example.com", "MADAR-ORD-1"),
                ("retry", "accountant.test@example.com", "MADAR-ORD-1"),
                ("submit_so", "accountant.test@example.com", "MADAR-ORD-1"),
                ("list_invoice", "accountant.test@example.com"),
                ("get_invoice", "accountant.test@example.com", "MADAR-ORD-1"),
                ("retry_invoice", "accountant.test@example.com", "MADAR-ORD-1"),
            ],
        )


if __name__ == "__main__":
    unittest.main()
