import importlib
import inspect
import sys
import types
import unittest


class ReportsApiTest(unittest.TestCase):
    def tearDown(self):
        sys.modules.pop("frappe", None)
        sys.modules.pop("madar.api.reports", None)

    def test_report_methods_are_authenticated_whitelisted_methods(self):
        whitelist_calls = []

        def whitelist(*args, **kwargs):
            whitelist_calls.append({"args": args, "kwargs": kwargs})
            return lambda fn: fn

        sys.modules["frappe"] = types.SimpleNamespace(whitelist=whitelist)
        reports = importlib.import_module("madar.api.reports")

        methods = [
            reports.get_orders_report,
            reports.get_payments_report,
            reports.get_production_report,
            reports.get_delivery_report,
            reports.get_cashbox_report,
            reports.get_erp_sync_errors_report,
        ]
        self.assertEqual(len(whitelist_calls), len(methods))
        for method in methods:
            self.assertIn("filters", inspect.signature(method).parameters)

    def test_guest_is_rejected(self):
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
        reports = importlib.import_module("madar.api.reports")

        with self.assertRaises(AuthenticationError):
            reports.get_orders_report()

    def test_orders_report_delegates_to_service_with_current_user(self):
        sys.modules["frappe"] = types.SimpleNamespace(
            whitelist=lambda *args, **kwargs: lambda fn: fn,
            session=types.SimpleNamespace(user="branch.user@example.com"),
        )
        reports = importlib.import_module("madar.api.reports")
        calls = []
        reports.reports_service = types.SimpleNamespace(
            get_orders_report=lambda user, filters=None: calls.append((user, filters))
            or {"ok": True, "data": {"items": [], "total": 0}, "error": None}
        )

        result = reports.get_orders_report(filters={"order_status": "draft"})

        self.assertTrue(result["ok"])
        self.assertEqual(calls, [("branch.user@example.com", {"order_status": "draft"})])


if __name__ == "__main__":
    unittest.main()
