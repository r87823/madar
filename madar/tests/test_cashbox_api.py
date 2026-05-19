import importlib
import sys
import types
import unittest


class CashboxApiTest(unittest.TestCase):
    def tearDown(self):
        sys.modules.pop("frappe", None)
        sys.modules.pop("madar.api.cashbox", None)

    def test_cashbox_methods_use_session_user_and_service_layer(self):
        sys.modules["frappe"] = types.SimpleNamespace(
            whitelist=lambda *args, **kwargs: lambda fn: fn,
            session=types.SimpleNamespace(user="cashier.test@example.com"),
        )
        cashbox = importlib.import_module("madar.api.cashbox")
        calls = []
        cashbox.cashbox_service = types.SimpleNamespace(
            get_my_cashbox=lambda user: calls.append(("my", user)) or {"ok": True},
            list_my_cashbox_entries=lambda user, cashbox_name=None: calls.append(
                ("entries", user, cashbox_name)
            )
            or {"ok": True},
            submit_my_cashbox=lambda user, submitted_cash: calls.append(("submit", user, submitted_cash))
            or {"ok": True},
            list_cashboxes_for_review=lambda user: calls.append(("review", user)) or {"ok": True},
            get_cashbox=lambda user, cashbox_name: calls.append(("get", user, cashbox_name)) or {"ok": True},
            approve_cashbox=lambda user, cashbox_name: calls.append(("approve", user, cashbox_name))
            or {"ok": True},
            return_cashbox=lambda user, cashbox_name, reason: calls.append(("return", user, cashbox_name, reason))
            or {"ok": True},
        )

        cashbox.get_my_cashbox()
        cashbox.list_my_cashbox_entries("CASHBOX-1")
        cashbox.submit_my_cashbox("40")
        cashbox.list_cashboxes_for_review()
        cashbox.get_cashbox("CASHBOX-1")
        cashbox.approve_cashbox("CASHBOX-1")
        cashbox.return_cashbox("CASHBOX-1", "Short cash")

        self.assertEqual(
            calls,
            [
                ("my", "cashier.test@example.com"),
                ("entries", "cashier.test@example.com", "CASHBOX-1"),
                ("submit", "cashier.test@example.com", "40"),
                ("review", "cashier.test@example.com"),
                ("get", "cashier.test@example.com", "CASHBOX-1"),
                ("approve", "cashier.test@example.com", "CASHBOX-1"),
                ("return", "cashier.test@example.com", "CASHBOX-1", "Short cash"),
            ],
        )

    def test_cashbox_methods_reject_guest(self):
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

        cashbox = importlib.import_module("madar.api.cashbox")

        with self.assertRaises(AuthenticationError):
            cashbox.get_my_cashbox()


if __name__ == "__main__":
    unittest.main()
