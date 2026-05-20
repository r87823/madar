import importlib
import inspect
import sys
import types
import unittest


class NotificationsApiTest(unittest.TestCase):
    def tearDown(self):
        sys.modules.pop("frappe", None)
        sys.modules.pop("madar.api.notifications", None)

    def test_api_methods_are_whitelisted_and_delegate(self):
        whitelist_calls = []

        def whitelist(*args, **kwargs):
            whitelist_calls.append({"args": args, "kwargs": kwargs})
            return lambda fn: fn

        sys.modules["frappe"] = types.SimpleNamespace(whitelist=whitelist)
        notifications = importlib.import_module("madar.api.notifications")

        self.assertEqual(len(whitelist_calls), 4)
        self.assertEqual(set(inspect.signature(notifications.list_notifications).parameters), set())
        self.assertEqual(set(inspect.signature(notifications.get_unread_count).parameters), set())
        self.assertEqual(set(inspect.signature(notifications.mark_notification_read).parameters), {"notification_name"})
        self.assertEqual(set(inspect.signature(notifications.mark_all_notifications_read).parameters), set())

    def test_list_notifications_delegates_for_authenticated_user(self):
        sys.modules["frappe"] = types.SimpleNamespace(
            whitelist=lambda *args, **kwargs: lambda fn: fn,
            session=types.SimpleNamespace(user="user@example.com"),
        )
        notifications = importlib.import_module("madar.api.notifications")
        calls = []
        notifications.notification_service = types.SimpleNamespace(
            list_notifications=lambda user: calls.append(("list", user)) or {"ok": True},
            get_unread_count=lambda user: calls.append(("count", user)) or {"ok": True},
            mark_read=lambda user, notification_name: calls.append(("read", user, notification_name)) or {"ok": True},
            mark_all_read=lambda user: calls.append(("all", user)) or {"ok": True},
        )

        result = notifications.list_notifications()
        notifications.get_unread_count()
        notifications.mark_notification_read("NOTIF-1")
        notifications.mark_all_notifications_read()

        self.assertEqual(result["ok"], True)
        self.assertEqual(
            calls,
            [
                ("list", "user@example.com"),
                ("count", "user@example.com"),
                ("read", "user@example.com", "NOTIF-1"),
                ("all", "user@example.com"),
            ],
        )

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
        notifications = importlib.import_module("madar.api.notifications")

        with self.assertRaises(AuthenticationError):
            notifications.get_unread_count()


if __name__ == "__main__":
    unittest.main()
