import importlib
import inspect
import sys
import types
import unittest


class AttendanceApiTest(unittest.TestCase):
    def tearDown(self):
        sys.modules.pop("frappe", None)
        sys.modules.pop("madar.api.attendance", None)

    def test_attendance_methods_are_authenticated_whitelisted_methods(self):
        whitelist_calls = []

        def whitelist(*args, **kwargs):
            whitelist_calls.append({"args": args, "kwargs": kwargs})
            return lambda fn: fn

        sys.modules["frappe"] = types.SimpleNamespace(whitelist=whitelist)

        attendance = importlib.import_module("madar.api.attendance")

        self.assertEqual(len(whitelist_calls), 4)
        self.assertTrue(all(call == {"args": (), "kwargs": {}} for call in whitelist_calls))
        self.assertEqual(inspect.signature(attendance.check_in).parameters, {})
        self.assertEqual(inspect.signature(attendance.check_out).parameters, {})

    def test_attendance_methods_reject_guest(self):
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

        attendance = importlib.import_module("madar.api.attendance")

        with self.assertRaises(AuthenticationError):
            attendance.get_status()

    def test_attendance_methods_use_session_user(self):
        sys.modules["frappe"] = types.SimpleNamespace(
            whitelist=lambda *args, **kwargs: lambda fn: fn,
            session=types.SimpleNamespace(user="employee.test@example.com"),
        )
        attendance = importlib.import_module("madar.api.attendance")
        calls = []
        attendance.attendance_service = types.SimpleNamespace(
            get_status=lambda user: calls.append(("status", user)) or {"ok": True},
            get_history=lambda user: calls.append(("history", user)) or {"ok": True},
            check_in=lambda user: calls.append(("in", user)) or {"ok": True},
            check_out=lambda user: calls.append(("out", user)) or {"ok": True},
        )

        attendance.get_status()
        attendance.get_history()
        attendance.check_in()
        attendance.check_out()

        self.assertEqual(
            calls,
            [
                ("status", "employee.test@example.com"),
                ("history", "employee.test@example.com"),
                ("in", "employee.test@example.com"),
                ("out", "employee.test@example.com"),
            ],
        )


if __name__ == "__main__":
    unittest.main()
