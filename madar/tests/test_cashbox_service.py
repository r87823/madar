import types
import unittest
from datetime import datetime

from madar.services import cashbox_service


class CashboxServiceTest(unittest.TestCase):
    def test_cash_payment_creates_daily_cashbox_entry_and_calculates_expected_cash(self):
        fake_frappe = FakeFrappe()
        payment = _payment("PAY-1", amount=40)

        result = cashbox_service.record_cash_payment(payment, frappe_module=fake_frappe)
        cashbox = cashbox_service.get_my_cashbox("cashier.test@example.com", frappe_module=fake_frappe)
        entries = cashbox_service.list_my_cashbox_entries("cashier.test@example.com", frappe_module=fake_frappe)

        self.assertEqual(result["ok"], True)
        self.assertEqual(len(fake_frappe.cashboxes), 1)
        self.assertEqual(len(fake_frappe.cashbox_entries), 1)
        self.assertEqual(cashbox["data"]["expected_cash"], 40.0)
        self.assertEqual(entries["data"]["items"][0]["payment"], "PAY-1")
        self.assertEqual(fake_frappe.created_erp_payment_entries, [])
        self.assertEqual(fake_frappe.created_sales_invoices, [])

    def test_non_cash_payment_does_not_create_cashbox_entry(self):
        fake_frappe = FakeFrappe()
        payment = _payment("PAY-1", amount=40, method="card")

        result = cashbox_service.record_cash_payment(payment, frappe_module=fake_frappe)

        self.assertEqual(result["ok"], True)
        self.assertEqual(result["data"]["skipped"], True)
        self.assertEqual(fake_frappe.cashboxes, [])
        self.assertEqual(fake_frappe.cashbox_entries, [])

    def test_daily_cashbox_is_unique_by_user_and_date(self):
        fake_frappe = FakeFrappe()

        first = cashbox_service.record_cash_payment(_payment("PAY-1", amount=25), frappe_module=fake_frappe)
        second = cashbox_service.record_cash_payment(_payment("PAY-2", amount=15), frappe_module=fake_frappe)

        self.assertEqual(first["data"]["cashbox"], second["data"]["cashbox"])
        self.assertEqual(len(fake_frappe.cashboxes), 1)
        self.assertEqual(cashbox_service.get_my_cashbox("cashier.test@example.com", frappe_module=fake_frappe)["data"]["expected_cash"], 40.0)

    def test_submit_cashbox_calculates_difference_and_blocks_approved_modification(self):
        fake_frappe = FakeFrappe()
        cashbox_service.record_cash_payment(_payment("PAY-1", amount=40), frappe_module=fake_frappe)

        submitted = cashbox_service.submit_my_cashbox("cashier.test@example.com", 35, frappe_module=fake_frappe)
        duplicate = cashbox_service.submit_my_cashbox("cashier.test@example.com", 35, frappe_module=fake_frappe)
        approved = cashbox_service.approve_cashbox("accountant.test@example.com", submitted["data"]["name"], frappe_module=fake_frappe)
        after_approved = cashbox_service.submit_my_cashbox("cashier.test@example.com", 40, frappe_module=fake_frappe)

        self.assertEqual(submitted["data"]["status"], "submitted")
        self.assertEqual(submitted["data"]["difference"], -5.0)
        self.assertEqual(duplicate["error"]["code"], "CASHBOX_ALREADY_SUBMITTED")
        self.assertEqual(approved["data"]["status"], "approved")
        self.assertEqual(after_approved["error"]["code"], "CASHBOX_ALREADY_APPROVED")

    def test_return_requires_reason_and_returned_cashbox_can_be_resubmitted(self):
        fake_frappe = FakeFrappe()
        cashbox_service.record_cash_payment(_payment("PAY-1", amount=40), frappe_module=fake_frappe)
        submitted = cashbox_service.submit_my_cashbox("cashier.test@example.com", 30, frappe_module=fake_frappe)

        missing_reason = cashbox_service.return_cashbox("accountant.test@example.com", submitted["data"]["name"], "", frappe_module=fake_frappe)
        returned = cashbox_service.return_cashbox("accountant.test@example.com", submitted["data"]["name"], "Short cash", frappe_module=fake_frappe)
        resubmitted = cashbox_service.submit_my_cashbox("cashier.test@example.com", 40, frappe_module=fake_frappe)

        self.assertEqual(missing_reason["error"]["code"], "CASHBOX_RETURN_REASON_REQUIRED")
        self.assertEqual(returned["data"]["status"], "returned")
        self.assertEqual(resubmitted["data"]["status"], "submitted")
        self.assertEqual(resubmitted["data"]["difference"], 0.0)

    def test_owner_and_reviewer_access_rules(self):
        fake_frappe = FakeFrappe()
        cashbox_service.record_cash_payment(_payment("PAY-1", amount=40), frappe_module=fake_frappe)
        cashbox_name = fake_frappe.cashboxes[0]["name"]
        cashbox_service.submit_my_cashbox("cashier.test@example.com", 40, frappe_module=fake_frappe)

        owner = cashbox_service.get_cashbox("cashier.test@example.com", cashbox_name, frappe_module=fake_frappe)
        other_user = cashbox_service.get_cashbox("employee.test@example.com", cashbox_name, frappe_module=fake_frappe)
        reviewer_list = cashbox_service.list_cashboxes_for_review("accountant.test@example.com", frappe_module=fake_frappe)

        self.assertEqual(owner["ok"], True)
        self.assertEqual(other_user["error"]["code"], "PERMISSION_DENIED")
        self.assertEqual([row["name"] for row in reviewer_list["data"]["items"]], [cashbox_name])

    def test_submit_requires_non_negative_cash_and_submit_permission(self):
        invalid_cash = FakeFrappe()
        no_permission = FakeFrappe(roles=["Madar Employee"])
        cashbox_service.record_cash_payment(_payment("PAY-1", amount=40), frappe_module=invalid_cash)
        cashbox_service.record_cash_payment(_payment("PAY-1", amount=40), frappe_module=no_permission)

        invalid = cashbox_service.submit_my_cashbox("cashier.test@example.com", -1, frappe_module=invalid_cash)
        denied = cashbox_service.submit_my_cashbox("employee.test@example.com", 40, frappe_module=no_permission)

        self.assertEqual(invalid["error"]["code"], "CASHBOX_SUBMITTED_CASH_INVALID")
        self.assertEqual(denied["error"]["code"], "PERMISSION_DENIED")


def _payment(name, *, amount, method="cash", user="cashier.test@example.com"):
    return {
        "doctype": "Madar Payment",
        "name": name,
        "madar_order": "MADAR-ORD-1",
        "amount": amount,
        "payment_method": method,
        "payment_status": "collected",
        "collected_by_user": user,
        "collected_at": datetime(2026, 5, 19, 12, 0, 0),
    }


class FakeDoc:
    def __init__(self, fake_frappe, values):
        self._fake_frappe = fake_frappe
        self._values = values
        for key, value in values.items():
            setattr(self, key, value)

    def insert(self, ignore_permissions=False):
        self._fake_frappe.insert_doc(self._values)
        return self

    def save(self, ignore_permissions=False):
        for key, value in vars(self).items():
            if not key.startswith("_"):
                self._values[key] = value
        return self

    def add_comment(self, comment_type, text):
        self._fake_frappe.audit_events.append({"comment_type": comment_type, "text": text})


class FakeFrappe:
    def __init__(self, *, roles=None, cashboxes=None, cashbox_entries=None):
        self.roles = roles or ["Madar Cashier"]
        self.cashboxes = list(cashboxes or [])
        self.cashbox_entries = list(cashbox_entries or [])
        self.now = datetime(2026, 5, 19, 12, 0, 0)
        self.audit_events = []
        self.created_erp_payment_entries = []
        self.created_sales_invoices = []
        self.db = types.SimpleNamespace(commit=lambda: None)
        self.utils = types.SimpleNamespace(now_datetime=lambda: self.now)

    def get_roles(self, user):
        if user == "accountant.test@example.com":
            return ["Madar Accountant"]
        if user == "employee.test@example.com":
            return ["Madar Employee"]
        return list(self.roles)

    def get_doc(self, doctype_or_values, name=None):
        if isinstance(doctype_or_values, dict):
            values = dict(doctype_or_values)
            if values["doctype"] == "Madar Cashbox":
                values["name"] = f"CASHBOX-{len(self.cashboxes) + 1}"
            elif values["doctype"] == "Madar Cashbox Entry":
                values["name"] = f"CASHBOX-ENTRY-{len(self.cashbox_entries) + 1}"
            return FakeDoc(self, values)
        if doctype_or_values == "Payment Entry":
            self.created_erp_payment_entries.append(name)
            raise AssertionError("Cashbox must not create ERPNext Payment Entry")
        if doctype_or_values == "Sales Invoice":
            self.created_sales_invoices.append(name)
            raise AssertionError("Cashbox must not create Sales Invoice")
        rows = {
            "Madar Cashbox": self.cashboxes,
            "Madar Cashbox Entry": self.cashbox_entries,
        }.get(doctype_or_values, [])
        for row in rows:
            if row.get("doctype") == doctype_or_values and row.get("name") == name:
                return FakeDoc(self, row)
        raise KeyError(name)

    def get_all(self, doctype, filters=None, fields=None, order_by=None, limit=20):
        rows = {
            "Madar Cashbox": self.cashboxes,
            "Madar Cashbox Entry": self.cashbox_entries,
        }.get(doctype, [])
        rows = self._filter_rows(rows, filters)
        if order_by:
            rows.sort(key=lambda row: row.get("modified") or row.get("name"), reverse="desc" in order_by)
        return [types.SimpleNamespace(**{field: row.get(field) for field in fields}) for row in rows[:limit]]

    def insert_doc(self, values):
        if values["doctype"] == "Madar Cashbox":
            self.cashboxes.append(values)
        elif values["doctype"] == "Madar Cashbox Entry":
            self.cashbox_entries.append(values)
        else:
            raise AssertionError(values["doctype"])

    def _filter_rows(self, rows, filters):
        filtered = list(rows)
        for key, value in (filters or {}).items():
            if isinstance(value, list) and value[0] == "in":
                filtered = [row for row in filtered if row.get(key) in value[1]]
            else:
                filtered = [row for row in filtered if row.get(key) == value]
        return filtered


if __name__ == "__main__":
    unittest.main()
