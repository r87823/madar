import types
import unittest

from madar.services import work_order_service


class WorkOrderServiceTest(unittest.TestCase):
    def test_admin_creates_work_orders_grouped_by_center_and_department(self):
        fake_frappe = FakeFrappe(
            roles=["Madar Admin"],
            orders=[_order("MADAR-ORD-1")],
            order_items=[
                _order_item("LINE-1", "MADAR-ORD-1", "MILK-001", qty=2),
                _order_item("LINE-2", "MADAR-ORD-1", "CHEESE-001", qty=1),
                _order_item("LINE-3", "MADAR-ORD-1", "BREAD-001", qty=3),
            ],
            mappings=[
                _mapping("MILK-001", "MAIN", "DAIRY"),
                _mapping("CHEESE-001", "MAIN", "DAIRY"),
                _mapping("BREAD-001", "MAIN", "BAKERY"),
            ],
        )

        result = work_order_service.create_work_orders_from_order(
            user="Administrator",
            order_name="MADAR-ORD-1",
            frappe_module=fake_frappe,
        )

        self.assertEqual(result["ok"], True)
        self.assertEqual(len(result["data"]["items"]), 2)
        self.assertEqual(
            [(row["production_center"], row["production_department"]) for row in result["data"]["items"]],
            [("MAIN", "BAKERY"), ("MAIN", "DAIRY")],
        )
        self.assertEqual(fake_frappe.work_orders[0]["status"], "pending")
        self.assertEqual(len(fake_frappe.work_order_items), 3)
        self.assertEqual(fake_frappe.created_erp_work_orders, [])

    def test_create_work_orders_is_idempotent_for_order(self):
        fake_frappe = FakeFrappe(
            roles=["Madar Admin"],
            orders=[_order("MADAR-ORD-1")],
            order_items=[_order_item("LINE-1", "MADAR-ORD-1", "MILK-001")],
            mappings=[_mapping("MILK-001", "MAIN", "DAIRY")],
        )

        first = work_order_service.create_work_orders_from_order(
            user="Administrator",
            order_name="MADAR-ORD-1",
            frappe_module=fake_frappe,
        )
        second = work_order_service.create_work_orders_from_order(
            user="Administrator",
            order_name="MADAR-ORD-1",
            frappe_module=fake_frappe,
        )

        self.assertEqual(first["ok"], True)
        self.assertEqual(second["ok"], True)
        self.assertEqual(len(fake_frappe.work_orders), 1)
        self.assertEqual(len(fake_frappe.work_order_items), 1)

    def test_missing_mapping_blocks_work_order_creation(self):
        fake_frappe = FakeFrappe(
            roles=["Madar Admin"],
            orders=[_order("MADAR-ORD-1")],
            order_items=[
                _order_item("LINE-1", "MADAR-ORD-1", "MILK-001"),
                _order_item("LINE-2", "MADAR-ORD-1", "UNKNOWN-001"),
            ],
            mappings=[_mapping("MILK-001", "MAIN", "DAIRY")],
        )

        result = work_order_service.create_work_orders_from_order(
            user="Administrator",
            order_name="MADAR-ORD-1",
            frappe_module=fake_frappe,
        )

        self.assertEqual(result["ok"], False)
        self.assertEqual(result["error"]["code"], "ITEM_DEPARTMENT_MAPPING_MISSING")
        self.assertEqual(result["data"]["missing_item_codes"], ["UNKNOWN-001"])
        self.assertEqual(fake_frappe.work_orders, [])

    def test_create_requires_approved_order_and_manage_permission(self):
        not_approved = FakeFrappe(roles=["Madar Admin"], orders=[_order("MADAR-ORD-1", status="submitted")])
        branch_user = FakeFrappe(
            roles=["Madar Branch User"],
            orders=[_order("MADAR-ORD-2")],
        )

        invalid = work_order_service.create_work_orders_from_order(
            user="Administrator",
            order_name="MADAR-ORD-1",
            frappe_module=not_approved,
        )
        denied = work_order_service.create_work_orders_from_order(
            user="branch.user@example.com",
            order_name="MADAR-ORD-2",
            frappe_module=branch_user,
        )

        self.assertEqual(invalid["error"]["code"], "ORDER_NOT_APPROVED")
        self.assertEqual(denied["error"]["code"], "PERMISSION_DENIED")

    def test_production_user_lists_and_gets_department_scoped_work_orders(self):
        fake_frappe = FakeFrappe(
            roles=["Madar Production User"],
            employee={"user_id": "production.user@example.com", "department": "DAIRY"},
            work_orders=[
                _work_order("WO-1", "MADAR-ORD-1", "MAIN", "DAIRY"),
                _work_order("WO-2", "MADAR-ORD-1", "MAIN", "BAKERY"),
            ],
            work_order_items=[_work_order_item("WOI-1", "WO-1", "MILK-001")],
        )

        listed = work_order_service.list_work_orders(
            user="production.user@example.com",
            frappe_module=fake_frappe,
        )
        fetched = work_order_service.get_work_order(
            user="production.user@example.com",
            work_order_name="WO-1",
            frappe_module=fake_frappe,
        )
        hidden = work_order_service.get_work_order(
            user="production.user@example.com",
            work_order_name="WO-2",
            frappe_module=fake_frappe,
        )

        self.assertEqual([row["name"] for row in listed["data"]["items"]], ["WO-1"])
        self.assertEqual(fetched["ok"], True)
        self.assertEqual(fetched["data"]["items"][0]["item_code"], "MILK-001")
        self.assertEqual(hidden["ok"], False)
        self.assertEqual(hidden["error"]["code"], "WORK_ORDER_NOT_FOUND")

    def test_lifecycle_transitions_and_delay_reason_are_controlled(self):
        fake_frappe = FakeFrappe(
            roles=["Madar Production User"],
            employee={"user_id": "production.user@example.com", "department": "DAIRY"},
            work_orders=[_work_order("WO-1", "MADAR-ORD-1", "MAIN", "DAIRY")],
        )

        accepted = work_order_service.accept_work_order("production.user@example.com", "WO-1", fake_frappe)
        started = work_order_service.start_work_order("production.user@example.com", "WO-1", fake_frappe)
        ready = work_order_service.mark_work_order_ready("production.user@example.com", "WO-1", fake_frappe)
        delayed_without_reason = work_order_service.mark_work_order_delayed(
            "production.user@example.com",
            "WO-1",
            "",
            fake_frappe,
        )

        self.assertEqual(accepted["data"]["status"], "accepted")
        self.assertEqual(started["data"]["status"], "in_production")
        self.assertEqual(ready["data"]["status"], "ready")
        self.assertEqual(delayed_without_reason["error"]["code"], "REASON_REQUIRED")
        self.assertTrue(fake_frappe.audit_events)

    def test_delay_allowed_from_pending_or_in_production_only(self):
        pending = FakeFrappe(
            roles=["Madar Production User"],
            employee={"user_id": "production.user@example.com", "department": "DAIRY"},
            work_orders=[_work_order("WO-1", "MADAR-ORD-1", "MAIN", "DAIRY")],
        )
        accepted = FakeFrappe(
            roles=["Madar Production User"],
            employee={"user_id": "production.user@example.com", "department": "DAIRY"},
            work_orders=[_work_order("WO-2", "MADAR-ORD-1", "MAIN", "DAIRY", status="accepted")],
        )

        delayed = work_order_service.mark_work_order_delayed(
            "production.user@example.com",
            "WO-1",
            "Machine issue",
            pending,
        )
        rejected = work_order_service.mark_work_order_delayed(
            "production.user@example.com",
            "WO-2",
            "Machine issue",
            accepted,
        )

        self.assertEqual(delayed["data"]["status"], "delayed")
        self.assertEqual(rejected["error"]["code"], "INVALID_WORK_ORDER_TRANSITION")

    def test_branch_user_cannot_update_work_order(self):
        fake_frappe = FakeFrappe(
            roles=["Madar Branch User"],
            work_orders=[_work_order("WO-1", "MADAR-ORD-1", "MAIN", "DAIRY")],
        )

        result = work_order_service.accept_work_order("branch.user@example.com", "WO-1", fake_frappe)

        self.assertEqual(result["ok"], False)
        self.assertEqual(result["error"]["code"], "PERMISSION_DENIED")
        self.assertEqual(fake_frappe.work_orders[0]["status"], "pending")


def _order(name, status="approved"):
    return {
        "doctype": "Madar Order",
        "name": name,
        "order_status": status,
    }


def _order_item(name, order_name, item_code, qty=1):
    return {
        "doctype": "Madar Order Item",
        "name": name,
        "order_name": order_name,
        "item_code": item_code,
        "item_name": item_code,
        "qty": qty,
        "notes": "",
    }


def _mapping(item_code, production_center, production_department, is_active=1):
    return {
        "doctype": "Madar Item Department Mapping",
        "name": item_code,
        "item_code": item_code,
        "item_name": item_code,
        "production_center": production_center,
        "production_department": production_department,
        "is_active": is_active,
    }


def _work_order(name, madar_order, production_center, production_department, status="pending"):
    return {
        "doctype": "Madar Work Order",
        "name": name,
        "madar_order": madar_order,
        "production_center": production_center,
        "production_department": production_department,
        "status": status,
        "accepted_at": None,
        "started_at": None,
        "ready_at": None,
        "delayed_at": None,
        "delay_reason": None,
        "created_from_order_at": "2026-05-19 12:00:00",
    }


def _work_order_item(name, work_order, item_code, qty=1):
    return {
        "doctype": "Madar Work Order Item",
        "name": name,
        "work_order": work_order,
        "madar_order_item": "LINE-1",
        "item_code": item_code,
        "item_name": item_code,
        "qty": qty,
        "notes": "",
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


class FakeMeta:
    def has_field(self, field):
        return True


class FakeFrappe:
    def __init__(
        self,
        *,
        roles=None,
        employee=None,
        orders=None,
        order_items=None,
        mappings=None,
        work_orders=None,
        work_order_items=None,
    ):
        self.roles = roles or ["Madar Admin"]
        self.employee = employee
        self.orders = list(orders or [])
        self.order_items = list(order_items or [])
        self.mappings = list(mappings or [])
        self.work_orders = list(work_orders or [])
        self.work_order_items = list(work_order_items or [])
        self.audit_events = []
        self.created_erp_work_orders = []
        self.db = types.SimpleNamespace(commit=lambda: None, exists=self.exists)
        self.utils = types.SimpleNamespace(now_datetime=lambda: "2026-05-19 12:00:00")

    def get_roles(self, user):
        return list(self.roles)

    def get_meta(self, doctype):
        if doctype == "Employee":
            return FakeMeta()
        raise KeyError(doctype)

    def get_doc(self, doctype_or_values, name=None):
        if isinstance(doctype_or_values, dict):
            values = dict(doctype_or_values)
            if values["doctype"] == "Madar Work Order":
                values["name"] = f"WO-{len(self.work_orders) + 1}"
            elif values["doctype"] == "Madar Work Order Item":
                values["name"] = f"WOI-{len(self.work_order_items) + 1}"
            elif values["doctype"] == "Work Order":
                self.created_erp_work_orders.append(values)
                raise AssertionError("Madar work orders must not create ERPNext Work Order")
            return FakeDoc(self, values)
        row = self.find_doc(doctype_or_values, name)
        if row:
            return FakeDoc(self, row)
        raise KeyError(name)

    def get_all(self, doctype, filters=None, fields=None, order_by=None, limit=20, pluck=None):
        if doctype == "Employee":
            rows = [self.employee] if self.employee else []
        else:
            rows = {
                "Madar Order": self.orders,
                "Madar Order Item": self.order_items,
                "Madar Item Department Mapping": self.mappings,
                "Madar Work Order": self.work_orders,
                "Madar Work Order Item": self.work_order_items,
            }.get(doctype, [])
        rows = self.filter_rows(rows, filters)
        if order_by:
            rows.sort(key=lambda row: row.get("modified") or row.get("name"), reverse="desc" in order_by)
        if pluck:
            return [row.get(pluck) for row in rows[:limit]]
        return [types.SimpleNamespace(**{field: row.get(field) for field in fields}) for row in rows[:limit]]

    def exists(self, doctype, name):
        return bool(self.find_doc(doctype, name))

    def find_doc(self, doctype, name):
        rows = {
            "Madar Order": self.orders,
            "Madar Work Order": self.work_orders,
        }.get(doctype, [])
        for row in rows:
            if row.get("name") == name:
                return row
        return None

    def insert_doc(self, values):
        if values["doctype"] == "Madar Work Order":
            self.work_orders.append(values)
        elif values["doctype"] == "Madar Work Order Item":
            self.work_order_items.append(values)
        else:
            raise AssertionError(values["doctype"])

    def filter_rows(self, rows, filters):
        filtered = list(rows)
        for key, value in (filters or {}).items():
            if isinstance(value, list) and value[0] == "in":
                filtered = [row for row in filtered if row.get(key) in value[1]]
            else:
                filtered = [row for row in filtered if row.get(key) == value]
        return filtered


if __name__ == "__main__":
    unittest.main()
