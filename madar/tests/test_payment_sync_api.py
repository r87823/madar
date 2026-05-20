import importlib
import inspect
import sys
import types
import unittest


class PaymentSyncApiTest(unittest.TestCase):
    def tearDown(self):
        sys.modules.pop("frappe", None)
        sys.modules.pop("madar.api.payment_sync", None)

    def test_payment_sync_methods_are_authenticated_whitelisted_methods(self):
        whitelist_calls = []

        def whitelist(*args, **kwargs):
            whitelist_calls.append({"args": args, "kwargs": kwargs})
            return lambda fn: fn

        sys.modules["frappe"] = types.SimpleNamespace(whitelist=whitelist)

        payment_sync = importlib.import_module("madar.api.payment_sync")

        self.assertEqual(len(whitelist_calls), 3)
        self.assertTrue(all(call == {"args": (), "kwargs": {}} for call in whitelist_calls))
        self.assertEqual(set(inspect.signature(payment_sync.list_payment_sync_items).parameters), set())
        self.assertEqual(set(inspect.signature(payment_sync.get_payment_sync_item).parameters), {"payment_name"})
        self.assertEqual(set(inspect.signature(payment_sync.retry_payment_sync).parameters), {"payment_name"})

    def test_payment_sync_methods_reject_guest(self):
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

        payment_sync = importlib.import_module("madar.api.payment_sync")

        with self.assertRaises(AuthenticationError):
            payment_sync.list_payment_sync_items()

    def test_payment_sync_methods_delegate_to_service_layer(self):
        sys.modules["frappe"] = types.SimpleNamespace(
            whitelist=lambda *args, **kwargs: lambda fn: fn,
            session=types.SimpleNamespace(user="accountant.test@example.com"),
        )
        payment_sync = importlib.import_module("madar.api.payment_sync")
        calls = []
        payment_sync.payment_erp_sync_service = types.SimpleNamespace(
            list_payment_sync_items=lambda user: calls.append(("list", user)) or {"ok": True},
            get_payment_sync_item=lambda user, payment_name: calls.append(("get", user, payment_name))
            or {"ok": True},
            retry_payment_sync=lambda user, payment_name: calls.append(("retry", user, payment_name))
            or {"ok": True},
        )

        payment_sync.list_payment_sync_items()
        payment_sync.get_payment_sync_item("PAY-1")
        payment_sync.retry_payment_sync("PAY-1")

        self.assertEqual(
            calls,
            [
                ("list", "accountant.test@example.com"),
                ("get", "accountant.test@example.com", "PAY-1"),
                ("retry", "accountant.test@example.com", "PAY-1"),
            ],
        )


if __name__ == "__main__":
    unittest.main()
