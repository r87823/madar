import importlib
import sys
import types
import unittest


class PaymentApiTest(unittest.TestCase):
    def tearDown(self):
        sys.modules.pop("frappe", None)
        sys.modules.pop("madar.api.payments", None)

    def test_payment_methods_use_session_user_and_service_layer(self):
        sys.modules["frappe"] = types.SimpleNamespace(
            whitelist=lambda *args, **kwargs: lambda fn: fn,
            session=types.SimpleNamespace(user="cashier.test@example.com"),
        )
        payments = importlib.import_module("madar.api.payments")
        calls = []
        payments.payment_service = types.SimpleNamespace(
            collect_payment=lambda user, order_name, amount, payment_method, reference_no="", notes="": calls.append(
                ("collect", user, order_name, amount, payment_method, reference_no, notes)
            )
            or {"ok": True},
            list_order_payments=lambda user, order_name: calls.append(("list", user, order_name)) or {"ok": True},
            get_payment=lambda user, payment_name: calls.append(("get", user, payment_name)) or {"ok": True},
        )

        payments.collect_payment("MADAR-ORD-1", "25", "cash", "REF-1", "notes")
        payments.list_order_payments("MADAR-ORD-1")
        payments.get_payment("PAY-1")

        self.assertEqual(
            calls,
            [
                ("collect", "cashier.test@example.com", "MADAR-ORD-1", "25", "cash", "REF-1", "notes"),
                ("list", "cashier.test@example.com", "MADAR-ORD-1"),
                ("get", "cashier.test@example.com", "PAY-1"),
            ],
        )

    def test_payment_methods_reject_guest(self):
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

        payments = importlib.import_module("madar.api.payments")

        with self.assertRaises(AuthenticationError):
            payments.list_order_payments("MADAR-ORD-1")


if __name__ == "__main__":
    unittest.main()
