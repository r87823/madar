import unittest
from datetime import datetime
from unittest.mock import patch

from madar.services import cashbox_service, delivery_service, order_service
from madar.tests.test_cashbox_service import FakeFrappe as CashboxFrappe
from madar.tests.test_delivery_service import FakeFrappe as DeliveryFrappe, _order as delivery_order
from madar.tests.test_order_service import FakeFrappe as OrderFrappe, _order as order


class NotificationIntegrationTest(unittest.TestCase):
    def test_order_submitted_notifies_approval_users_when_recipient_exists(self):
        fake_frappe = OrderFrappe(
            orders=[order("MADAR-ORD-1", "Main Branch", "branch.user@example.com", items_count=1)],
        )

        with patch("madar.services.order_service.notification_service") as notifications:
            notifications.users_with_permission.return_value = ["branch.supervisor@example.com"]
            order_service.submit_order(
                "branch.user@example.com",
                "MADAR-ORD-1",
                frappe_module=fake_frappe,
            )

        notifications.safe_notify_users.assert_called_once()
        args, kwargs = notifications.safe_notify_users.call_args
        self.assertEqual(args[0], ["branch.supervisor@example.com"])
        self.assertEqual(kwargs["title"], "طلب جديد بانتظار الاعتماد")
        self.assertIn("MADAR-ORD-1", kwargs["message"])
        self.assertEqual(kwargs["event_type"], "order_submitted")

    def test_return_reject_and_approve_notify_order_creator(self):
        fake_frappe = OrderFrappe(
            roles=["Madar Employee", "Madar Branch Supervisor"],
            orders=[
                order("MADAR-ORD-1", "Main Branch", "creator@example.com", status="submitted", items_count=1),
                order("MADAR-ORD-2", "Main Branch", "creator@example.com", status="submitted", items_count=1),
                order("MADAR-ORD-3", "Main Branch", "creator@example.com", status="submitted", items_count=1),
            ],
        )

        with patch("madar.services.order_service.notification_service") as notifications:
            notifications.users_with_permission.return_value = []
            order_service.return_order_for_edit(
                "branch.supervisor@example.com",
                "MADAR-ORD-1",
                "بيانات ناقصة",
                frappe_module=fake_frappe,
            )
            order_service.reject_order(
                "branch.supervisor@example.com",
                "MADAR-ORD-2",
                "مكرر",
                frappe_module=fake_frappe,
            )
            order_service.approve_order(
                "branch.supervisor@example.com",
                "MADAR-ORD-3",
                frappe_module=fake_frappe,
            )

        calls = notifications.safe_notify_user.call_args_list
        self.assertEqual(calls[0].args[0], "creator@example.com")
        self.assertEqual(calls[0].kwargs["title"], "تم إرجاع الطلب للتعديل")
        self.assertEqual(calls[1].kwargs["title"], "تم رفض الطلب")
        self.assertEqual(calls[2].kwargs["title"], "تم اعتماد الطلب")

    def test_delivery_batch_assigned_notifies_driver(self):
        fake_frappe = DeliveryFrappe(
            roles=["Madar Driver"],
            orders=[delivery_order("MADAR-ORD-1", delivery_status="ready_for_dispatch")],
        )
        batch = delivery_service.create_delivery_batch(
            "driver.test@example.com",
            ["MADAR-ORD-1"],
            frappe_module=fake_frappe,
        )

        with patch("madar.services.delivery_service.notification_service") as notifications:
            delivery_service.assign_driver(
                "driver.test@example.com",
                batch["data"]["name"],
                "driver.test@example.com",
                frappe_module=fake_frappe,
            )

        notifications.safe_notify_user.assert_called_once()
        self.assertEqual(notifications.safe_notify_user.call_args.args[0], "driver.test@example.com")
        self.assertEqual(notifications.safe_notify_user.call_args.kwargs["title"], "تم إسناد دفعة توصيل")

    def test_cashbox_return_notifies_owner(self):
        fake_frappe = CashboxFrappe(
            roles=["Madar Accountant"],
            cashboxes=[
                {
                    "doctype": "Madar Cashbox",
                    "name": "CASHBOX-1",
                    "user": "cashier.test@example.com",
                    "cashbox_date": "2026-05-19",
                    "status": "submitted",
                    "expected_cash": 50,
                    "submitted_cash": 40,
                    "difference": -10,
                    "submitted_at": datetime(2026, 5, 20, 11, 0, 0),
                    "reviewed_by": "",
                    "reviewed_at": None,
                    "return_reason": "",
                    "closed_at": None,
                    "modified": "CASHBOX-1",
                }
            ],
        )

        with patch("madar.services.cashbox_service.notification_service") as notifications:
            cashbox_service.return_cashbox(
                "accountant.test@example.com",
                "CASHBOX-1",
                "فرق في المبلغ",
                frappe_module=fake_frappe,
            )

        notifications.safe_notify_user.assert_called_once()
        self.assertEqual(notifications.safe_notify_user.call_args.args[0], "cashier.test@example.com")
        self.assertEqual(notifications.safe_notify_user.call_args.kwargs["title"], "تم إرجاع الصندوق")


if __name__ == "__main__":
    unittest.main()
