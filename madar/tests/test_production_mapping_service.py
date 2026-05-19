import types
import unittest

from madar.permissions import checks, registry
from madar.services import production_mapping_service


class ProductionMappingServiceTest(unittest.TestCase):
    def test_permission_registry_includes_manage_mappings_for_full_access(self):
        self.assertIn("production.manage_mappings", registry.ALL_PERMISSION_KEYS)
        self.assertIn(
            "production.manage_mappings",
            checks.get_permissions_for_roles(["Madar Admin"]),
        )

    def test_branch_user_cannot_manage_mappings(self):
        fake_frappe = FakeFrappe(roles=["Madar Employee", "Madar Branch User"])

        result = production_mapping_service.create_or_update_item_department_mapping(
            user="branch.user@example.com",
            item_code="MILK-001",
            production_center="MAIN",
            production_department="MILK",
            frappe_module=fake_frappe,
        )

        self.assertEqual(result["ok"], False)
        self.assertEqual(result["error"]["code"], "PERMISSION_DENIED")
        self.assertEqual(fake_frappe.mappings, [])

    def test_production_user_can_view_active_departments_but_not_manage_mappings(self):
        fake_frappe = FakeFrappe(
            roles=["Madar Production User"],
            departments=[
                _department("MILK", "Milk Department", "MAIN", is_active=1),
                _department("OLD", "Old Department", "MAIN", is_active=0),
            ],
        )

        viewed = production_mapping_service.list_production_departments(
            user="production.user@example.com",
            frappe_module=fake_frappe,
        )
        managed = production_mapping_service.create_or_update_item_department_mapping(
            user="production.user@example.com",
            item_code="MILK-001",
            production_center="MAIN",
            production_department="MILK",
            frappe_module=fake_frappe,
        )

        self.assertEqual(viewed["ok"], True)
        self.assertEqual([row["name"] for row in viewed["data"]["items"]], ["MILK"])
        self.assertEqual(managed["ok"], False)
        self.assertEqual(managed["error"]["code"], "PERMISSION_DENIED")

    def test_admin_can_create_center_department_and_idempotent_item_mapping(self):
        fake_frappe = FakeFrappe(roles=["Madar Admin"])

        center = production_mapping_service.create_or_update_production_center(
            user="Administrator",
            center_name="Main Production Center",
            center_code="MAIN",
            frappe_module=fake_frappe,
        )
        department = production_mapping_service.create_or_update_production_department(
            user="Administrator",
            department_name="Milk Department",
            department_code="MILK",
            production_center="MAIN",
            frappe_module=fake_frappe,
        )
        first = production_mapping_service.create_or_update_item_department_mapping(
            user="Administrator",
            item_code="MILK-001",
            production_center="MAIN",
            production_department="MILK",
            frappe_module=fake_frappe,
        )
        second = production_mapping_service.create_or_update_item_department_mapping(
            user="Administrator",
            item_code="MILK-001",
            production_center="MAIN",
            production_department="MILK",
            frappe_module=fake_frappe,
        )

        self.assertEqual(center["ok"], True)
        self.assertEqual(department["ok"], True)
        self.assertEqual(first["ok"], True)
        self.assertEqual(second["ok"], True)
        self.assertEqual(len(fake_frappe.mappings), 1)
        self.assertEqual(first["data"]["item_name"], "Milk")
        self.assertEqual(set(first["data"]), set(production_mapping_service.MAPPING_FIELDS))

    def test_mapping_requires_existing_item_center_and_department(self):
        fake_frappe = FakeFrappe(roles=["Madar Admin"])

        missing_item = production_mapping_service.create_or_update_item_department_mapping(
            user="Administrator",
            item_code="UNKNOWN",
            production_center="MAIN",
            production_department="MILK",
            frappe_module=fake_frappe,
        )
        missing_department = production_mapping_service.create_or_update_item_department_mapping(
            user="Administrator",
            item_code="MILK-001",
            production_center="MAIN",
            production_department="UNKNOWN",
            frappe_module=fake_frappe,
        )

        self.assertEqual(missing_item["error"]["code"], "ITEM_NOT_FOUND")
        self.assertEqual(missing_department["error"]["code"], "PRODUCTION_DEPARTMENT_NOT_FOUND")

    def test_validate_order_department_mappings_returns_missing_inactive_mappings(self):
        fake_frappe = FakeFrappe(
            roles=["Madar Admin"],
            orders=[_order("MADAR-ORD-1", status="approved")],
            order_items=[
                _order_item("LINE-1", "MADAR-ORD-1", "MILK-001"),
                _order_item("LINE-2", "MADAR-ORD-1", "RICE-001"),
                _order_item("LINE-3", "MADAR-ORD-1", "TEA-001"),
            ],
            mappings=[
                _mapping("MILK-001", "Milk", "MAIN", "MILK", is_active=1),
                _mapping("RICE-001", "Rice", "MAIN", "RICE", is_active=0),
            ],
        )

        result = production_mapping_service.validate_order_department_mappings(
            user="Administrator",
            order_name="MADAR-ORD-1",
            frappe_module=fake_frappe,
        )

        self.assertEqual(result["ok"], True)
        self.assertEqual(result["data"]["is_valid"], False)
        self.assertEqual(result["data"]["missing_item_codes"], ["RICE-001", "TEA-001"])
        self.assertEqual(result["data"]["mapped_item_codes"], ["MILK-001"])

    def test_validate_order_department_mappings_requires_approved_order(self):
        fake_frappe = FakeFrappe(
            roles=["Madar Admin"],
            orders=[_order("MADAR-ORD-1", status="submitted")],
        )

        result = production_mapping_service.validate_order_department_mappings(
            user="Administrator",
            order_name="MADAR-ORD-1",
            frappe_module=fake_frappe,
        )

        self.assertEqual(result["ok"], False)
        self.assertEqual(result["error"]["code"], "ORDER_NOT_APPROVED")


def _center(name, center_name, is_active=1):
    return {
        "doctype": "Madar Production Center",
        "name": name,
        "center_name": center_name,
        "center_code": name,
        "is_active": is_active,
    }


def _department(name, department_name, production_center, is_active=1):
    return {
        "doctype": "Madar Production Department",
        "name": name,
        "department_name": department_name,
        "department_code": name,
        "production_center": production_center,
        "is_active": is_active,
    }


def _mapping(item_code, item_name, production_center, production_department, is_active=1):
    return {
        "doctype": "Madar Item Department Mapping",
        "name": item_code,
        "item_code": item_code,
        "item_name": item_name,
        "production_center": production_center,
        "production_department": production_department,
        "is_active": is_active,
    }


def _order(name, status="approved"):
    return {
        "doctype": "Madar Order",
        "name": name,
        "order_status": status,
    }


def _order_item(name, order_name, item_code):
    return {
        "doctype": "Madar Order Item",
        "name": name,
        "order_name": order_name,
        "item_code": item_code,
        "item_name": item_code,
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
    def __init__(
        self,
        *,
        roles=None,
        centers=None,
        departments=None,
        mappings=None,
        orders=None,
        order_items=None,
    ):
        self.roles = roles or ["Madar Admin"]
        self.items = {
            "MILK-001": {"doctype": "Item", "name": "MILK-001", "item_code": "MILK-001", "item_name": "Milk"},
            "RICE-001": {"doctype": "Item", "name": "RICE-001", "item_code": "RICE-001", "item_name": "Rice"},
            "TEA-001": {"doctype": "Item", "name": "TEA-001", "item_code": "TEA-001", "item_name": "Tea"},
        }
        self.centers = list(centers or [_center("MAIN", "Main Production Center")])
        self.departments = list(departments or [_department("MILK", "Milk Department", "MAIN")])
        self.mappings = list(mappings or [])
        self.orders = list(orders or [])
        self.order_items = list(order_items or [])
        self.audit_events = []
        self.db = types.SimpleNamespace(commit=lambda: None, exists=self.exists)
        self.utils = types.SimpleNamespace(now_datetime=lambda: "2026-05-19 12:00:00")

    def get_roles(self, user):
        return list(self.roles)

    def get_doc(self, doctype_or_values, name=None):
        if isinstance(doctype_or_values, dict):
            values = dict(doctype_or_values)
            if values["doctype"] == "Madar Item Department Mapping":
                values["name"] = values["item_code"]
            elif values["doctype"] == "Madar Production Center":
                values["name"] = values["center_code"]
            elif values["doctype"] == "Madar Production Department":
                values["name"] = values["department_code"]
            return FakeDoc(self, values)
        row = self.find_doc(doctype_or_values, name)
        if row:
            return FakeDoc(self, row)
        raise KeyError(name)

    def get_all(self, doctype, filters=None, fields=None, order_by=None, limit=20, pluck=None):
        rows = {
            "Madar Production Center": self.centers,
            "Madar Production Department": self.departments,
            "Madar Item Department Mapping": self.mappings,
            "Madar Order": self.orders,
            "Madar Order Item": self.order_items,
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
        if doctype == "Item":
            return self.items.get(name)
        rows = {
            "Madar Production Center": self.centers,
            "Madar Production Department": self.departments,
            "Madar Item Department Mapping": self.mappings,
            "Madar Order": self.orders,
        }.get(doctype, [])
        for row in rows:
            if row.get("name") == name:
                return row
        return None

    def insert_doc(self, values):
        target = {
            "Madar Production Center": self.centers,
            "Madar Production Department": self.departments,
            "Madar Item Department Mapping": self.mappings,
        }[values["doctype"]]
        target.append(values)

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
