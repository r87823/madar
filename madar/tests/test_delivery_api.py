import importlib
import sys
import types
import unittest


class DeliveryApiTest(unittest.TestCase):
    def tearDown(self):
        sys.modules.pop("frappe", None)
        sys.modules.pop("madar.api.delivery", None)

    def test_delivery_methods_use_session_user_and_service_layer(self):
        sys.modules["frappe"] = types.SimpleNamespace(
            whitelist=lambda *args, **kwargs: lambda fn: fn,
            session=types.SimpleNamespace(user="driver.test@example.com"),
        )
        delivery = importlib.import_module("madar.api.delivery")
        calls = []
        delivery.delivery_service = types.SimpleNamespace(
            list_dispatch_queue=lambda user: calls.append(("list", user)) or {"ok": True},
            mark_dispatched_to_branch=lambda user, order_name: calls.append(("to_branch", user, order_name)) or {"ok": True},
            mark_received_at_branch=lambda user, order_name: calls.append(("received", user, order_name)) or {"ok": True},
            mark_ready_for_customer_pickup=lambda user, order_name: calls.append(("pickup_ready", user, order_name)) or {"ok": True},
            mark_customer_picked_up=lambda user, order_name: calls.append(("picked_up", user, order_name)) or {"ok": True},
            mark_dispatched_to_customer=lambda user, order_name: calls.append(("to_customer", user, order_name)) or {"ok": True},
            mark_delivered_to_customer=lambda user, order_name: calls.append(("delivered", user, order_name)) or {"ok": True},
            mark_failed_delivery=lambda user, order_name, reason: calls.append(("failed", user, order_name, reason)) or {"ok": True},
        )

        delivery.list_dispatch_queue()
        delivery.mark_dispatched_to_branch("MADAR-ORD-1")
        delivery.mark_received_at_branch("MADAR-ORD-1")
        delivery.mark_ready_for_customer_pickup("MADAR-ORD-1")
        delivery.mark_customer_picked_up("MADAR-ORD-1")
        delivery.mark_dispatched_to_customer("MADAR-ORD-1")
        delivery.mark_delivered_to_customer("MADAR-ORD-1")
        delivery.mark_failed_delivery("MADAR-ORD-1", "reason")

        self.assertEqual(
            calls,
            [
                ("list", "driver.test@example.com"),
                ("to_branch", "driver.test@example.com", "MADAR-ORD-1"),
                ("received", "driver.test@example.com", "MADAR-ORD-1"),
                ("pickup_ready", "driver.test@example.com", "MADAR-ORD-1"),
                ("picked_up", "driver.test@example.com", "MADAR-ORD-1"),
                ("to_customer", "driver.test@example.com", "MADAR-ORD-1"),
                ("delivered", "driver.test@example.com", "MADAR-ORD-1"),
                ("failed", "driver.test@example.com", "MADAR-ORD-1", "reason"),
            ],
        )


if __name__ == "__main__":
    unittest.main()

