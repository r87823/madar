import importlib
import inspect
import sys
import types
import unittest


class AccountingFinalizationApiTest(unittest.TestCase):
    def tearDown(self):
        sys.modules.pop("frappe", None)
        sys.modules.pop("madar.api.accounting_finalization", None)

    def test_finalization_methods_are_authenticated_whitelisted_methods(self):
        whitelist_calls = []

        def whitelist(*args, **kwargs):
            whitelist_calls.append({"args": args, "kwargs": kwargs})
            return lambda fn: fn

        sys.modules["frappe"] = types.SimpleNamespace(whitelist=whitelist)

        accounting_finalization = importlib.import_module("madar.api.accounting_finalization")

        self.assertEqual(len(whitelist_calls), 4)
        self.assertTrue(all(call == {"args": (), "kwargs": {}} for call in whitelist_calls))
        self.assertEqual(set(inspect.signature(accounting_finalization.get_finalization_status).parameters), {"order_name"})
        self.assertEqual(set(inspect.signature(accounting_finalization.submit_sales_invoice).parameters), {"order_name"})
        self.assertEqual(set(inspect.signature(accounting_finalization.submit_payment_entries).parameters), {"order_name"})
        self.assertEqual(set(inspect.signature(accounting_finalization.finalize_order_accounting).parameters), {"order_name"})

    def test_finalization_methods_reject_guest(self):
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

        accounting_finalization = importlib.import_module("madar.api.accounting_finalization")

        with self.assertRaises(AuthenticationError):
            accounting_finalization.get_finalization_status("MADAR-ORD-1")

    def test_finalization_methods_delegate_to_service_layer(self):
        sys.modules["frappe"] = types.SimpleNamespace(
            whitelist=lambda *args, **kwargs: lambda fn: fn,
            session=types.SimpleNamespace(user="accountant.test@example.com"),
        )
        accounting_finalization = importlib.import_module("madar.api.accounting_finalization")
        calls = []
        accounting_finalization.accounting_finalization_service = types.SimpleNamespace(
            get_finalization_status=lambda user, order_name: calls.append(("status", user, order_name))
            or {"ok": True},
            submit_sales_invoice=lambda user, order_name: calls.append(("invoice", user, order_name))
            or {"ok": True},
            submit_payment_entries_for_order=lambda user, order_name: calls.append(("payments", user, order_name))
            or {"ok": True},
            finalize_order_accounting=lambda user, order_name: calls.append(("finalize", user, order_name))
            or {"ok": True},
        )

        accounting_finalization.get_finalization_status("MADAR-ORD-1")
        accounting_finalization.submit_sales_invoice("MADAR-ORD-1")
        accounting_finalization.submit_payment_entries("MADAR-ORD-1")
        accounting_finalization.finalize_order_accounting("MADAR-ORD-1")

        self.assertEqual(
            calls,
            [
                ("status", "accountant.test@example.com", "MADAR-ORD-1"),
                ("invoice", "accountant.test@example.com", "MADAR-ORD-1"),
                ("payments", "accountant.test@example.com", "MADAR-ORD-1"),
                ("finalize", "accountant.test@example.com", "MADAR-ORD-1"),
            ],
        )


if __name__ == "__main__":
    unittest.main()
