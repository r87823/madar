import types
import unittest

from madar.services import catalog_service


class CatalogServiceTest(unittest.TestCase):
    def test_list_products_returns_safe_item_projection_with_default_price(self):
        fake_frappe = FakeFrappe()

        result = catalog_service.list_products(
            user="branch.user@example.com",
            search="milk",
            frappe_module=fake_frappe,
        )

        self.assertEqual(result["ok"], True)
        self.assertEqual(
            result["data"]["items"],
            [
                {
                    "item_code": "MILK-001",
                    "item_name": "Milk",
                    "stock_uom": "Nos",
                    "disabled": 0,
                    "image": "/files/milk.png",
                    "default_price": 12.5,
                }
            ],
        )
        self.assertNotIn("valuation_rate", result["data"]["items"][0])

    def test_list_products_requires_order_create_permission(self):
        fake_frappe = FakeFrappe(roles=["Madar Employee"])

        result = catalog_service.list_products(
            user="employee.test@example.com",
            frappe_module=fake_frappe,
        )

        self.assertEqual(result["ok"], False)
        self.assertEqual(result["error"]["code"], "PERMISSION_DENIED")


class FakeFrappe:
    def __init__(self, *, roles=None):
        self.roles = roles or ["Madar Employee", "Madar Branch User"]
        self.items = [
            {
                "item_code": "MILK-001",
                "item_name": "Milk",
                "stock_uom": "Nos",
                "disabled": 0,
                "image": "/files/milk.png",
                "valuation_rate": 7,
            },
            {
                "item_code": "RICE-001",
                "item_name": "Rice",
                "stock_uom": "Kg",
                "disabled": 0,
                "image": None,
            },
        ]
        self.prices = {"MILK-001": 12.5}

    def get_roles(self, user):
        return list(self.roles)

    def get_all(self, doctype, filters=None, fields=None, order_by=None, limit=20):
        if doctype == "Item":
            rows = list(self.items)
            if filters:
                for key, value in filters.items():
                    if isinstance(value, list) and value[0] == "like":
                        needle = value[1].replace("%", "").lower()
                        rows = [row for row in rows if needle in row.get(key, "").lower()]
                    else:
                        rows = [row for row in rows if row.get(key) == value]
            return [types.SimpleNamespace(**{field: row.get(field) for field in fields}) for row in rows[:limit]]
        if doctype == "Item Price":
            item_code = filters.get("item_code")
            if item_code in self.prices:
                return [types.SimpleNamespace(price_list_rate=self.prices[item_code])]
            return []
        return []


if __name__ == "__main__":
    unittest.main()
