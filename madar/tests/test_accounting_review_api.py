import importlib
import inspect
import sys
import types
import unittest


class AccountingReviewApiTest(unittest.TestCase):
    def tearDown(self):
        sys.modules.pop("frappe", None)
        sys.modules.pop("madar.api.accounting_review", None)

    def test_accounting_review_methods_are_authenticated_whitelisted_methods(self):
        whitelist_calls = []

        def whitelist(*args, **kwargs):
            whitelist_calls.append({"args": args, "kwargs": kwargs})
            return lambda fn: fn

        sys.modules["frappe"] = types.SimpleNamespace(whitelist=whitelist)

        accounting_review = importlib.import_module("madar.api.accounting_review")

        self.assertEqual(len(whitelist_calls), 4)
        self.assertTrue(all(call == {"args": (), "kwargs": {}} for call in whitelist_calls))
        self.assertEqual(set(inspect.signature(accounting_review.get_order_accounting_summary).parameters), {"order_name"})
        self.assertEqual(set(inspect.signature(accounting_review.list_orders_for_accounting_review).parameters), set())
        self.assertEqual(set(inspect.signature(accounting_review.mark_accounting_reviewed).parameters), {"order_name"})
        self.assertEqual(
            set(inspect.signature(accounting_review.mark_accounting_needs_attention).parameters),
            {"order_name", "notes"},
        )

    def test_accounting_review_methods_reject_guest(self):
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

        accounting_review = importlib.import_module("madar.api.accounting_review")

        with self.assertRaises(AuthenticationError):
            accounting_review.list_orders_for_accounting_review()

    def test_accounting_review_methods_delegate_to_service_layer(self):
        sys.modules["frappe"] = types.SimpleNamespace(
            whitelist=lambda *args, **kwargs: lambda fn: fn,
            session=types.SimpleNamespace(user="accountant.test@example.com"),
        )
        accounting_review = importlib.import_module("madar.api.accounting_review")
        calls = []
        accounting_review.accounting_review_service = types.SimpleNamespace(
            get_order_accounting_summary=lambda user, order_name: calls.append(("get", user, order_name))
            or {"ok": True},
            list_orders_for_accounting_review=lambda user: calls.append(("list", user)) or {"ok": True},
            mark_accounting_reviewed=lambda user, order_name: calls.append(("reviewed", user, order_name))
            or {"ok": True},
            mark_accounting_needs_attention=lambda user, order_name, notes: calls.append(
                ("needs", user, order_name, notes)
            )
            or {"ok": True},
        )

        accounting_review.list_orders_for_accounting_review()
        accounting_review.get_order_accounting_summary("MADAR-ORD-1")
        accounting_review.mark_accounting_reviewed("MADAR-ORD-1")
        accounting_review.mark_accounting_needs_attention("MADAR-ORD-1", "Missing cashbox")

        self.assertEqual(
            calls,
            [
                ("list", "accountant.test@example.com"),
                ("get", "accountant.test@example.com", "MADAR-ORD-1"),
                ("reviewed", "accountant.test@example.com", "MADAR-ORD-1"),
                ("needs", "accountant.test@example.com", "MADAR-ORD-1", "Missing cashbox"),
            ],
        )


if __name__ == "__main__":
    unittest.main()
