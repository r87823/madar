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


if __name__ == "__main__":
    unittest.main()
