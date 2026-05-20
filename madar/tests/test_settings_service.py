import types
import unittest
from datetime import datetime

from madar.services import settings_service
from madar.services import notification_service


class SettingsServiceTest(unittest.TestCase):
    def test_defaults_are_seeded_idempotently(self):
        fake = FakeFrappe(roles=["Administrator"])

        first = settings_service.ensure_default_settings(frappe_module=fake)
        second = settings_service.ensure_default_settings(frappe_module=fake)

        self.assertEqual(first["created"], len(settings_service.DEFAULT_SETTINGS))
        self.assertEqual(second["created"], 0)
        self.assertIn("attendance.duplicate_window_seconds", fake.settings)

    def test_admin_reads_non_secret_settings_only(self):
        fake = FakeFrappe(roles=["Administrator"])
        settings_service.ensure_default_settings(frappe_module=fake)
        fake.settings["erp.api_secret"] = FakeDoc(
            doctype="Madar Setting",
            setting_key="erp.api_secret",
            setting_value="hidden",
            value_type="string",
            category="erp",
            label_ar="سر ERP",
            description_ar="لا يعرض",
            is_secret=1,
            is_editable=1,
        )

        result = settings_service.get_settings("Administrator", frappe_module=fake)

        self.assertTrue(result["ok"])
        keys = {row["setting_key"] for row in result["data"]["items"]}
        self.assertIn("payments.allow_overpayment", keys)
        self.assertNotIn("erp.api_secret", keys)
        self.assertNotIn("hidden", str(result["data"]))

    def test_admin_updates_editable_non_secret_setting_with_type_validation(self):
        fake = FakeFrappe(roles=["Administrator"])
        settings_service.ensure_default_settings(frappe_module=fake)

        result = settings_service.update_setting(
            "Administrator",
            "payments.allow_overpayment",
            True,
            frappe_module=fake,
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["value"], True)
        self.assertEqual(fake.settings["payments.allow_overpayment"].updated_by, "Administrator")

    def test_non_admin_cannot_update_settings(self):
        fake = FakeFrappe(roles=["Madar Employee"])
        settings_service.ensure_default_settings(frappe_module=fake)

        result = settings_service.update_setting(
            "employee.test@example.com",
            "payments.allow_overpayment",
            True,
            frappe_module=fake,
        )

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "PERMISSION_DENIED")

    def test_unknown_or_invalid_values_are_rejected(self):
        fake = FakeFrappe(roles=["Administrator"])
        settings_service.ensure_default_settings(frappe_module=fake)

        unknown = settings_service.update_setting(
            "Administrator",
            "erp.api_key",
            "secret",
            frappe_module=fake,
        )
        invalid_int = settings_service.update_setting(
            "Administrator",
            "attendance.duplicate_window_seconds",
            "abc",
            frappe_module=fake,
        )
        invalid_list = settings_service.update_setting(
            "Administrator",
            "payments.enabled_methods",
            ["cash", "crypto"],
            frappe_module=fake,
        )

        self.assertEqual(unknown["error"]["code"], "SETTING_NOT_FOUND")
        self.assertEqual(invalid_int["error"]["code"], "SETTING_VALUE_INVALID")
        self.assertEqual(invalid_list["error"]["code"], "SETTING_VALUE_INVALID")

    def test_typed_get_setting_returns_default_or_stored_value(self):
        fake = FakeFrappe(roles=["Administrator"])
        settings_service.ensure_default_settings(frappe_module=fake)
        settings_service.update_setting(
            "Administrator",
            "attendance.duplicate_window_seconds",
            90,
            frappe_module=fake,
        )

        value = settings_service.get_setting_value(
            "attendance.duplicate_window_seconds",
            frappe_module=fake,
        )

        self.assertEqual(value, 90)

    def test_notifications_disabled_prevents_notification_creation(self):
        fake = FakeFrappe(roles=["Administrator"])
        settings_service.ensure_default_settings(frappe_module=fake)
        settings_service.update_setting(
            "Administrator",
            "notifications.enabled",
            False,
            frappe_module=fake,
        )

        result = notification_service.notify_user(
            "employee.test@example.com",
            "عنوان",
            "رسالة",
            "test_event",
            frappe_module=fake,
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["reason"], "notifications_disabled")


class FakeDoc:
    def __init__(self, **values):
        self.__dict__.update(values)
        self.name = values.get("name") or values.get("setting_key")
        self.comments = []

    def insert(self, ignore_permissions=False):
        self._store[self.setting_key] = self
        return self

    def save(self, ignore_permissions=False):
        self._store[self.setting_key] = self
        return self

    def add_comment(self, comment_type, text):
        self.comments.append((comment_type, text))


class FakeFrappe:
    def __init__(self, roles=None):
        self.roles = roles or []
        self.settings = {}
        self.db = types.SimpleNamespace(commit=lambda: None, exists=self.exists)
        self.utils = types.SimpleNamespace(now_datetime=lambda: datetime(2026, 5, 20, 12, 0, 0))

    def get_roles(self, user):
        if user == "Administrator":
            return ["Administrator"]
        return list(self.roles)

    def exists(self, doctype, name):
        return doctype == "Madar Setting" and name in self.settings

    def get_doc(self, doctype_or_values, name=None):
        if isinstance(doctype_or_values, dict):
            doc = FakeDoc(**doctype_or_values)
            doc._store = self.settings
            return doc
        if doctype_or_values == "Madar Setting" and name in self.settings:
            doc = self.settings[name]
            doc._store = self.settings
            return doc
        raise KeyError(name)

    def get_all(self, doctype, filters=None, fields=None, order_by=None, limit=1000):
        rows = list(self.settings.values()) if doctype == "Madar Setting" else []
        rows = _filter_rows(rows, filters or {})
        return [
            types.SimpleNamespace(**{field: getattr(row, field, None) for field in (fields or row.__dict__.keys())})
            for row in rows[:limit]
        ]


def _filter_rows(rows, filters):
    for key, value in filters.items():
        rows = [row for row in rows if getattr(row, key, None) == value]
    return rows


if __name__ == "__main__":
    unittest.main()
