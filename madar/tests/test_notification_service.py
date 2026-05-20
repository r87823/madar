import json
import types
import unittest
from datetime import datetime

from madar.services import notification_service


class NotificationServiceTest(unittest.TestCase):
    def test_user_sees_only_own_notifications_and_unread_count(self):
        fake_frappe = FakeFrappe(
            notifications=[
                _notification("NOTIF-1", "user@example.com", is_read=0),
                _notification("NOTIF-2", "other@example.com", is_read=0),
                _notification("NOTIF-3", "user@example.com", is_read=1),
            ]
        )

        listed = notification_service.list_notifications(
            "user@example.com",
            frappe_module=fake_frappe,
        )
        count = notification_service.get_unread_count(
            "user@example.com",
            frappe_module=fake_frappe,
        )

        self.assertEqual(listed["ok"], True)
        self.assertEqual([item["name"] for item in listed["data"]["items"]], ["NOTIF-3", "NOTIF-1"])
        self.assertEqual(count["data"]["unread_count"], 1)
        self.assertNotIn("other@example.com", str(listed["data"]))

    def test_mark_read_only_works_for_own_notification(self):
        fake_frappe = FakeFrappe(
            notifications=[_notification("NOTIF-1", "owner@example.com", is_read=0)]
        )

        denied = notification_service.mark_read(
            "other@example.com",
            "NOTIF-1",
            frappe_module=fake_frappe,
        )
        marked = notification_service.mark_read(
            "owner@example.com",
            "NOTIF-1",
            frappe_module=fake_frappe,
        )

        self.assertEqual(denied["error"]["code"], "NOTIFICATION_NOT_FOUND")
        self.assertEqual(marked["ok"], True)
        self.assertEqual(marked["data"]["is_read"], True)
        self.assertEqual(fake_frappe.notifications[0]["is_read"], 1)
        self.assertEqual(fake_frappe.notifications[0]["read_at"], fake_frappe.now)

    def test_mark_all_read_only_affects_current_user(self):
        fake_frappe = FakeFrappe(
            notifications=[
                _notification("NOTIF-1", "user@example.com", is_read=0),
                _notification("NOTIF-2", "user@example.com", is_read=0),
                _notification("NOTIF-3", "other@example.com", is_read=0),
            ]
        )

        result = notification_service.mark_all_read(
            "user@example.com",
            frappe_module=fake_frappe,
        )

        self.assertEqual(result["ok"], True)
        self.assertEqual(result["data"]["updated"], 2)
        self.assertEqual([row["is_read"] for row in fake_frappe.notifications], [1, 1, 0])

    def test_notify_user_creates_arabic_safe_notification(self):
        fake_frappe = FakeFrappe()

        result = notification_service.notify_user(
            "user@example.com",
            title="طلب جديد بانتظار الاعتماد",
            message="تم إرسال الطلب MADAR-ORD-1 للاعتماد.",
            event_type="order_submitted",
            entity_type="Madar Order",
            entity_name="MADAR-ORD-1",
            priority="high",
            route_key="order_detail",
            route_params={"order_name": "MADAR-ORD-1"},
            action_label="عرض الطلب",
            frappe_module=fake_frappe,
        )

        self.assertEqual(result["ok"], True)
        self.assertEqual(fake_frappe.notifications[0]["recipient_user"], "user@example.com")
        self.assertEqual(fake_frappe.notifications[0]["title"], "طلب جديد بانتظار الاعتماد")
        self.assertEqual(fake_frappe.notifications[0]["is_read"], 0)
        self.assertEqual(fake_frappe.notifications[0]["priority"], "high")
        self.assertEqual(fake_frappe.notifications[0]["route_key"], "order_detail")
        self.assertEqual(json.loads(fake_frappe.notifications[0]["route_params_json"]), {"order_name": "MADAR-ORD-1"})
        self.assertEqual(result["data"]["route_params"], {"order_name": "MADAR-ORD-1"})
        self.assertEqual(result["data"]["action_label"], "عرض الطلب")

    def test_notification_without_route_key_still_works(self):
        fake_frappe = FakeFrappe()

        result = notification_service.notify_user(
            "user@example.com",
            title="عنوان",
            message="رسالة",
            event_type="manual",
            frappe_module=fake_frappe,
        )

        self.assertEqual(result["ok"], True)
        self.assertEqual(result["data"]["route_key"], "none")
        self.assertEqual(result["data"]["route_params"], {})

    def test_notify_users_deduplicates_recipients(self):
        fake_frappe = FakeFrappe()

        result = notification_service.notify_users(
            ["one@example.com", "one@example.com", "", "two@example.com"],
            title="تم اعتماد الطلب",
            message="تم اعتماد الطلب MADAR-ORD-1.",
            event_type="order_approved",
            frappe_module=fake_frappe,
        )

        self.assertEqual(result["ok"], True)
        self.assertEqual(result["data"]["created"], 2)
        self.assertEqual([row["recipient_user"] for row in fake_frappe.notifications], ["one@example.com", "two@example.com"])

    def test_notification_creation_failure_is_safe(self):
        fake_frappe = FakeFrappe(fail_insert=True)

        result = notification_service.safe_notify_user(
            "user@example.com",
            title="تم اعتماد الطلب",
            message="تم اعتماد الطلب MADAR-ORD-1.",
            event_type="order_approved",
            frappe_module=fake_frappe,
        )

        self.assertEqual(result["ok"], False)
        self.assertEqual(result["error"]["code"], "NOTIFICATION_CREATE_FAILED")
        self.assertEqual(fake_frappe.log_errors, ["NOTIFICATION_CREATE_FAILED"])

    def test_permission_recipient_lookup_uses_roles_without_direct_role_checks(self):
        fake_frappe = FakeFrappe(
            users=[
                {"name": "supervisor@example.com", "enabled": 1},
                {"name": "employee@example.com", "enabled": 1},
                {"name": "disabled@example.com", "enabled": 0},
            ],
            roles_by_user={
                "supervisor@example.com": ["Madar Branch Supervisor"],
                "employee@example.com": ["Madar Employee"],
                "disabled@example.com": ["Madar Branch Supervisor"],
            },
        )

        recipients = notification_service.users_with_permission(
            "orders.approve",
            frappe_module=fake_frappe,
        )

        self.assertEqual(recipients, ["supervisor@example.com"])


def _notification(name, recipient_user, is_read=0):
    return {
        "doctype": "Madar Notification",
        "name": name,
        "recipient_user": recipient_user,
        "title": "عنوان",
        "message": "رسالة",
        "event_type": "test_event",
        "entity_type": "Madar Order",
        "entity_name": "MADAR-ORD-1",
        "is_read": is_read,
        "read_at": None,
        "created_at": datetime(2026, 5, 20, 10, int(name.split("-")[-1]), 0),
        "priority": "normal",
        "route_key": "order_detail",
        "route_params_json": '{"order_name": "MADAR-ORD-1"}',
        "action_label": "عرض الطلب",
        "deep_link_status": "",
        "modified": name,
    }


class FakeDoc:
    def __init__(self, fake_frappe, values):
        self._fake_frappe = fake_frappe
        self._values = values
        for key, value in values.items():
            setattr(self, key, value)

    def insert(self, ignore_permissions=False):
        if self._fake_frappe.fail_insert:
            raise RuntimeError("insert failed")
        if not getattr(self, "name", None):
            self.name = f"NOTIF-{len(self._fake_frappe.notifications) + 1}"
        self._sync_values()
        self._fake_frappe.notifications.append(self._values)
        return self

    def save(self, ignore_permissions=False):
        self._sync_values()
        return self

    def _sync_values(self):
        for key, value in vars(self).items():
            if not key.startswith("_"):
                self._values[key] = value


class FakeFrappe:
    def __init__(self, *, notifications=None, users=None, roles_by_user=None, fail_insert=False):
        self.notifications = list(notifications or [])
        self.users = list(users or [])
        self.roles_by_user = dict(roles_by_user or {})
        self.fail_insert = fail_insert
        self.now = datetime(2026, 5, 20, 12, 0, 0)
        self.log_errors = []
        self.db = types.SimpleNamespace(commit=lambda: None)
        self.utils = types.SimpleNamespace(now_datetime=lambda: self.now)

    def get_roles(self, user):
        return list(self.roles_by_user.get(user, []))

    def get_all(self, doctype, filters=None, fields=None, order_by=None, limit=20):
        if doctype == "Madar Notification":
            rows = list(self.notifications)
            rows = _apply_filters(rows, filters)
            rows.sort(key=lambda row: row.get("created_at") or row.get("modified"), reverse=True)
            return [types.SimpleNamespace(**{field: row.get(field) for field in fields}) for row in rows[:limit]]
        if doctype == "User":
            rows = _apply_filters(list(self.users), filters)
            return [types.SimpleNamespace(**{field: row.get(field) for field in fields}) for row in rows[:limit]]
        return []

    def get_doc(self, doctype_or_values, name=None):
        if isinstance(doctype_or_values, dict):
            return FakeDoc(self, dict(doctype_or_values))
        for row in self.notifications:
            if row.get("doctype") == doctype_or_values and row.get("name") == name:
                return FakeDoc(self, row)
        raise KeyError(name)

    def log_error(self, title=None, message=None):
        self.log_errors.append(title or message)


def _apply_filters(rows, filters):
    for key, value in (filters or {}).items():
        if isinstance(value, list) and value[0] == "in":
            rows = [row for row in rows if row.get(key) in value[1]]
        else:
            rows = [row for row in rows if row.get(key) == value]
    return rows


if __name__ == "__main__":
    unittest.main()
