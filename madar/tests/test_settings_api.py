import importlib
import inspect
import sys
import types
import unittest


class SettingsApiTest(unittest.TestCase):
    def tearDown(self):
        sys.modules.pop("frappe", None)
        sys.modules.pop("madar.api.settings", None)

    def test_settings_methods_are_authenticated_whitelisted_methods(self):
        calls = []

        def whitelist(*args, **kwargs):
            calls.append({"args": args, "kwargs": kwargs})
            return lambda fn: fn

        sys.modules["frappe"] = types.SimpleNamespace(whitelist=whitelist)
        settings = importlib.import_module("madar.api.settings")

        methods = [
            settings.get_settings,
            settings.get_setting_metadata,
            settings.update_setting,
        ]
        self.assertEqual(len(calls), len(methods))
        self.assertIn("setting_key", inspect.signature(settings.update_setting).parameters)

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
        settings = importlib.import_module("madar.api.settings")

        with self.assertRaises(AuthenticationError):
            settings.get_settings()

    def test_update_delegates_to_service(self):
        sys.modules["frappe"] = types.SimpleNamespace(
            whitelist=lambda *args, **kwargs: lambda fn: fn,
            session=types.SimpleNamespace(user="Administrator"),
        )
        settings = importlib.import_module("madar.api.settings")
        calls = []
        settings.settings_service = types.SimpleNamespace(
            update_setting=lambda user, setting_key, value: calls.append((user, setting_key, value))
            or {"ok": True, "data": {}, "error": None}
        )

        result = settings.update_setting("payments.allow_overpayment", True)

        self.assertTrue(result["ok"])
        self.assertEqual(calls, [("Administrator", "payments.allow_overpayment", True)])


if __name__ == "__main__":
    unittest.main()
