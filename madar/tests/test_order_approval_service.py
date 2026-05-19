import unittest
from datetime import datetime

from madar.services import order_service
from madar.tests.test_order_service import FakeFrappe, _order


class OrderApprovalServiceTest(unittest.TestCase):
    def test_submit_requires_at_least_one_item(self):
        fake_frappe = FakeFrappe(
            orders=[_order("MADAR-ORD-1", "Main Branch", "branch.user@example.com")]
        )

        result = order_service.submit_order(
            user="branch.user@example.com",
            order_name="MADAR-ORD-1",
            frappe_module=fake_frappe,
        )

        self.assertEqual(result["ok"], False)
        self.assertEqual(result["error"]["code"], "ORDER_HAS_NO_ITEMS")

    def test_submit_allows_returned_for_edit_with_items(self):
        fake_frappe = FakeFrappe(
            orders=[
                _order(
                    "MADAR-ORD-1",
                    "Main Branch",
                    "branch.user@example.com",
                    status="returned_for_edit",
                    items_count=1,
                )
            ]
        )

        result = order_service.submit_order(
            user="branch.user@example.com",
            order_name="MADAR-ORD-1",
            frappe_module=fake_frappe,
        )

        self.assertEqual(result["ok"], True)
        self.assertEqual(result["data"]["order_status"], "submitted")

    def test_approval_queue_requires_approval_permission_and_scope(self):
        fake_frappe = FakeFrappe(
            roles=["Madar Employee", "Madar Branch Supervisor"],
            orders=[
                _order("MADAR-ORD-1", "Main Branch", "branch.user@example.com", status="submitted", items_count=1),
                _order("MADAR-ORD-2", "HQ", "accountant.test@example.com", status="submitted", items_count=1),
                _order("MADAR-ORD-3", "Main Branch", "branch.user@example.com", status="draft", items_count=1),
            ],
        )

        result = order_service.list_approval_queue(
            user="branch.supervisor@example.com",
            frappe_module=fake_frappe,
        )

        self.assertEqual(result["ok"], True)
        self.assertEqual([item["name"] for item in result["data"]["items"]], ["MADAR-ORD-1"])

    def test_employee_cannot_access_approval_queue(self):
        fake_frappe = FakeFrappe(roles=["Madar Employee"])

        result = order_service.list_approval_queue(
            user="employee.test@example.com",
            frappe_module=fake_frappe,
        )

        self.assertEqual(result["ok"], False)
        self.assertEqual(result["error"]["code"], "PERMISSION_DENIED")

    def test_approve_return_and_reject_submitted_orders(self):
        now = datetime(2026, 5, 19, 10, 0, 0)
        fake_frappe = FakeFrappe(
            roles=["Madar Employee", "Madar Branch Supervisor"],
            now=now,
            orders=[
                _order("MADAR-ORD-1", "Main Branch", "branch.user@example.com", status="submitted", items_count=1),
                _order("MADAR-ORD-2", "Main Branch", "branch.user@example.com", status="submitted", items_count=1),
                _order("MADAR-ORD-3", "Main Branch", "branch.user@example.com", status="submitted", items_count=1),
            ],
        )

        approved = order_service.approve_order(
            user="branch.supervisor@example.com",
            order_name="MADAR-ORD-1",
            frappe_module=fake_frappe,
        )
        returned = order_service.return_order_for_edit(
            user="branch.supervisor@example.com",
            order_name="MADAR-ORD-2",
            reason="Missing phone confirmation",
            frappe_module=fake_frappe,
        )
        rejected = order_service.reject_order(
            user="branch.supervisor@example.com",
            order_name="MADAR-ORD-3",
            reason="Duplicate order",
            frappe_module=fake_frappe,
        )

        self.assertEqual(approved["data"]["order_status"], "approved")
        self.assertEqual(returned["data"]["order_status"], "returned_for_edit")
        self.assertEqual(rejected["data"]["order_status"], "rejected")
        self.assertEqual(fake_frappe.audit_events[-3]["action"], "approve_order")
        self.assertEqual(fake_frappe.audit_events[-2]["action"], "return_order_for_edit")
        self.assertEqual(fake_frappe.audit_events[-1]["action"], "reject_order")

    def test_return_and_reject_require_reason(self):
        fake_frappe = FakeFrappe(
            roles=["Madar Employee", "Madar Branch Supervisor"],
            orders=[
                _order("MADAR-ORD-1", "Main Branch", "branch.user@example.com", status="submitted", items_count=1)
            ],
        )

        returned = order_service.return_order_for_edit(
            user="branch.supervisor@example.com",
            order_name="MADAR-ORD-1",
            reason="",
            frappe_module=fake_frappe,
        )
        rejected = order_service.reject_order(
            user="branch.supervisor@example.com",
            order_name="MADAR-ORD-1",
            reason="",
            frappe_module=fake_frappe,
        )

        self.assertEqual(returned["error"]["code"], "REASON_REQUIRED")
        self.assertEqual(rejected["error"]["code"], "REASON_REQUIRED")

    def test_only_submitted_orders_can_be_approved(self):
        fake_frappe = FakeFrappe(
            roles=["Madar Employee", "Madar Branch Supervisor"],
            orders=[
                _order("MADAR-ORD-1", "Main Branch", "branch.user@example.com", status="approved", items_count=1)
            ],
        )

        result = order_service.approve_order(
            user="branch.supervisor@example.com",
            order_name="MADAR-ORD-1",
            frappe_module=fake_frappe,
        )

        self.assertEqual(result["ok"], False)
        self.assertEqual(result["error"]["code"], "INVALID_ORDER_TRANSITION")


if __name__ == "__main__":
    unittest.main()
