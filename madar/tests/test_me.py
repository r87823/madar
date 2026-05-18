import importlib
import sys
import types
import unittest


class CurrentUserContextApiTest(unittest.TestCase):
    def tearDown(self):
        sys.modules.pop("frappe", None)
        sys.modules.pop("madar.api.me", None)

    def test_get_context_is_authenticated_whitelisted_method(self):
        whitelist_calls = []

        def whitelist(*args, **kwargs):
            whitelist_calls.append({"args": args, "kwargs": kwargs})
            return lambda fn: fn

        fake_frappe = types.SimpleNamespace(whitelist=whitelist)
        sys.modules["frappe"] = fake_frappe

        importlib.import_module("madar.api.me")

        self.assertEqual(whitelist_calls, [{"args": (), "kwargs": {}}])

    def test_get_context_returns_current_user_context(self):
        fake_frappe = types.SimpleNamespace(
            whitelist=lambda *args, **kwargs: lambda fn: fn,
            session=types.SimpleNamespace(user="mobile@example.com", sid="hidden"),
            get_fullname=lambda user: "Mobile User",
            get_roles=lambda user: ["Employee", "Driver"],
        )
        sys.modules["frappe"] = fake_frappe

        me = importlib.import_module("madar.api.me")

        self.assertEqual(
            me.get_context(),
            {
                "user": "mobile@example.com",
                "full_name": "Mobile User",
                "roles": ["Employee", "Driver"],
                "permissions": [
                    "attendance.check_in",
                    "attendance.check_out",
                    "employee_services.view_self",
                    "employee_services.request_leave",
                    "delivery.view_assigned_batches",
                    "delivery.update_batch",
                    "payments.collect",
                    "cashbox.view_own",
                    "cashbox.submit",
                ],
                "employee": None,
                "branch": None,
            },
        )

    def test_get_context_rejects_guest_user(self):
        class AuthenticationError(Exception):
            pass

        def throw(message, exc):
            raise exc(message)

        fake_frappe = types.SimpleNamespace(
            whitelist=lambda *args, **kwargs: lambda fn: fn,
            session=types.SimpleNamespace(user="Guest"),
            AuthenticationError=AuthenticationError,
            throw=throw,
            get_fullname=lambda user: "Guest",
            get_roles=lambda user: [],
        )
        sys.modules["frappe"] = fake_frappe

        me = importlib.import_module("madar.api.me")

        with self.assertRaises(AuthenticationError):
            me.get_context()


if __name__ == "__main__":
    unittest.main()
