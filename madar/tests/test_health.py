import importlib
import sys
import types
import unittest


class HealthEndpointTest(unittest.TestCase):
    def test_ping_returns_readiness_payload(self):
        fake_frappe = types.SimpleNamespace(whitelist=lambda *args, **kwargs: lambda fn: fn)
        sys.modules["frappe"] = fake_frappe

        health = importlib.reload(importlib.import_module("madar.api.health"))

        self.assertEqual(
            health.ping(),
            {
                "ok": True,
                "app": "madar",
                "service": "Madar Frappe Backend",
            },
        )

    def test_ping_allows_guest_readiness_checks(self):
        whitelist_calls = []

        def whitelist(*args, **kwargs):
            whitelist_calls.append({"args": args, "kwargs": kwargs})
            return lambda fn: fn

        fake_frappe = types.SimpleNamespace(whitelist=whitelist)
        sys.modules["frappe"] = fake_frappe

        sys.modules.pop("madar.api.health", None)
        importlib.import_module("madar.api.health")

        self.assertEqual(whitelist_calls, [{"args": (), "kwargs": {"allow_guest": True}}])


if __name__ == "__main__":
    unittest.main()
