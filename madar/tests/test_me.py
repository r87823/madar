import importlib
import sys
import types
import unittest


class CurrentUserContextApiTest(unittest.TestCase):
    def tearDown(self):
        sys.modules.pop("frappe", None)
        sys.modules.pop("frappe.utils", None)
        sys.modules.pop("madar.api.me", None)

    def test_get_context_is_authenticated_whitelisted_method(self):
        whitelist_calls = []

        def whitelist(*args, **kwargs):
            whitelist_calls.append({"args": args, "kwargs": kwargs})
            return lambda fn: fn

        fake_frappe = types.SimpleNamespace(whitelist=whitelist)
        sys.modules["frappe"] = fake_frappe
        sys.modules["frappe.utils"] = types.SimpleNamespace(get_fullname=lambda user: user)

        importlib.import_module("madar.api.me")

        self.assertEqual(whitelist_calls, [{"args": (), "kwargs": {}}])

    def test_get_context_returns_current_user_context(self):
        fake_frappe = types.SimpleNamespace(
            whitelist=lambda *args, **kwargs: lambda fn: fn,
            session=types.SimpleNamespace(user="mobile@example.com", sid="hidden"),
            get_roles=lambda user: ["Employee", "Driver"],
            get_meta=lambda doctype: _FakeMeta(["user_id"]),
            get_all=lambda doctype, filters=None, fields=None, limit=20: [],
        )
        sys.modules["frappe"] = fake_frappe
        sys.modules["frappe.utils"] = types.SimpleNamespace(get_fullname=lambda user: "Mobile User")

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

    def test_get_context_includes_safe_employee_context_when_linked(self):
        fake_frappe = types.SimpleNamespace(
            whitelist=lambda *args, **kwargs: lambda fn: fn,
            session=types.SimpleNamespace(user="mobile@example.com"),
            get_roles=lambda user: ["Employee"],
            get_meta=lambda doctype: _FakeMeta(
                ["user_id", "employee_name", "company", "department", "designation", "branch"]
            ),
            get_all=lambda doctype, filters=None, fields=None, limit=20: [
                {
                    "name": "EMP-0001",
                    "employee_name": "Mobile Worker",
                    "company": "Madar",
                    "department": "Operations",
                    "designation": "Driver",
                    "branch": "Riyadh",
                }
            ],
        )
        sys.modules["frappe"] = fake_frappe
        sys.modules["frappe.utils"] = types.SimpleNamespace(get_fullname=lambda user: "Mobile User")

        me = importlib.import_module("madar.api.me")
        context = me.get_context()

        self.assertEqual(
            context["employee"],
            {
                "name": "EMP-0001",
                "employee_name": "Mobile Worker",
                "company": "Madar",
                "department": "Operations",
                "designation": "Driver",
                "branch": "Riyadh",
            },
        )
        self.assertIn("employee_services.view_self", context["permissions"])
        self.assertIsNone(context["branch"])

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
            get_roles=lambda user: [],
        )
        sys.modules["frappe"] = fake_frappe
        sys.modules["frappe.utils"] = types.SimpleNamespace(get_fullname=lambda user: "Guest")

        me = importlib.import_module("madar.api.me")

        with self.assertRaises(AuthenticationError):
            me.get_context()


if __name__ == "__main__":
    unittest.main()


class _FakeMeta:
    def __init__(self, fields):
        self._fields = set(fields)

    def has_field(self, fieldname):
        return fieldname in self._fields
