import importlib
import inspect
import sys
import types
import unittest


class FollowupDashboardApiTest(unittest.TestCase):
    def tearDown(self):
        sys.modules.pop("frappe", None)
        sys.modules.pop("madar.api.followup_dashboard", None)

    def test_get_summary_is_authenticated_whitelisted_method(self):
        whitelist_calls = []

        def whitelist(*args, **kwargs):
            whitelist_calls.append({"args": args, "kwargs": kwargs})
            return lambda fn: fn

        sys.modules["frappe"] = types.SimpleNamespace(whitelist=whitelist)
        followup_dashboard = importlib.import_module("madar.api.followup_dashboard")

        self.assertEqual(len(whitelist_calls), 1)
        self.assertEqual(set(inspect.signature(followup_dashboard.get_summary).parameters), set())

    def test_get_summary_rejects_guest(self):
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
        followup_dashboard = importlib.import_module("madar.api.followup_dashboard")

        with self.assertRaises(AuthenticationError):
            followup_dashboard.get_summary()

    def test_get_summary_delegates_to_service(self):
        sys.modules["frappe"] = types.SimpleNamespace(
            whitelist=lambda *args, **kwargs: lambda fn: fn,
            session=types.SimpleNamespace(user="branch.user@example.com"),
        )
        followup_dashboard = importlib.import_module("madar.api.followup_dashboard")
        calls = []
        followup_dashboard.followup_dashboard_service = types.SimpleNamespace(
            get_summary=lambda user: calls.append(user) or {"ok": True, "data": {"cards": [], "alerts": []}, "error": None}
        )

        result = followup_dashboard.get_summary()

        self.assertEqual(result["ok"], True)
        self.assertEqual(calls, ["branch.user@example.com"])


if __name__ == "__main__":
    unittest.main()
