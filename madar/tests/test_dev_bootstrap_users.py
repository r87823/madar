import types
import unittest

from madar.dev import bootstrap_users
from madar.permissions import roles


class DevUserBootstrapTest(unittest.TestCase):
    def test_bootstrap_is_disabled_by_default(self):
        fake_frappe = FakeFrappe()

        result = bootstrap_users.bootstrap_dev_users(frappe_module=fake_frappe)

        self.assertEqual(result, {"enabled": False, "users": []})
        self.assertEqual(fake_frappe.created_users, [])
        self.assertEqual(fake_frappe.created_employees, [])

    def test_bootstrap_creates_required_users_employees_roles_and_context(self):
        fake_frappe = FakeFrappe(config={"enable_madar_dev_user_bootstrap": 1})

        result = bootstrap_users.bootstrap_dev_users(
            frappe_module=fake_frappe,
            password="temporary-secret",
        )

        self.assertEqual(result["enabled"], True)
        self.assertEqual(
            set(result["users"]),
            {definition.email for definition in bootstrap_users.DEV_USERS},
        )
        driver = fake_frappe.users["driver.test@example.com"]
        self.assertEqual(driver.roles, {roles.MADAR_EMPLOYEE, roles.MADAR_DRIVER})
        self.assertEqual(driver.new_password, "temporary-secret")
        self.assertEqual(driver.reset_password_key, "force-reset")

        employee = fake_frappe.employees["Madar Dev Driver"]
        self.assertEqual(employee.user_id, "driver.test@example.com")
        self.assertEqual(employee.department, "Delivery")
        self.assertEqual(employee.branch, "Main Branch")
        self.assertEqual(employee.employee_name, "Madar Dev Driver")
        self.assertFalse(hasattr(employee, "salary"))
        self.assertFalse(hasattr(employee, "bank_ac_no"))

    def test_bootstrap_is_idempotent_for_existing_user_employee_and_roles(self):
        fake_frappe = FakeFrappe(config={"enable_madar_dev_user_bootstrap": 1})

        bootstrap_users.bootstrap_dev_users(frappe_module=fake_frappe, password="first")
        bootstrap_users.bootstrap_dev_users(frappe_module=fake_frappe, password="second")

        self.assertEqual(fake_frappe.created_users.count("driver.test@example.com"), 1)
        self.assertEqual(fake_frappe.created_employees.count("Madar Dev Driver"), 1)
        driver = fake_frappe.users["driver.test@example.com"]
        self.assertEqual(driver.roles, {roles.MADAR_EMPLOYEE, roles.MADAR_DRIVER})
        self.assertEqual(driver.added_roles.count(roles.MADAR_DRIVER), 1)
        self.assertEqual(driver.new_password, "second")

    def test_existing_user_does_not_fail_and_missing_role_is_added(self):
        fake_frappe = FakeFrappe(config={"enable_madar_dev_user_bootstrap": 1})
        fake_frappe.users["driver.test@example.com"] = FakeUser(
            fake_frappe,
            "driver.test@example.com",
        )

        bootstrap_users.bootstrap_dev_users(frappe_module=fake_frappe, password="secret")

        driver = fake_frappe.users["driver.test@example.com"]
        self.assertEqual(driver.roles, {roles.MADAR_EMPLOYEE, roles.MADAR_DRIVER})
        self.assertNotIn("driver.test@example.com", fake_frappe.created_users)

    def test_missing_branch_doctype_skips_branch_creation_but_keeps_employee_branch_value(self):
        fake_frappe = FakeFrappe(
            config={"enable_madar_dev_user_bootstrap": 1},
            missing_branch_doctype=True,
        )

        bootstrap_users.bootstrap_dev_users(frappe_module=fake_frappe, password="secret")

        self.assertEqual(fake_frappe.created_branches, [])
        self.assertEqual(fake_frappe.employees["Madar Dev Employee"].branch, "Main Branch")

    def test_get_context_reflects_expected_permissions_and_scopes(self):
        fake_frappe = FakeFrappe(config={"enable_madar_dev_user_bootstrap": 1})
        bootstrap_users.bootstrap_dev_users(frappe_module=fake_frappe, password="secret")

        context = bootstrap_users.get_expected_context_for_dev_user(
            "driver.test@example.com",
            frappe_module=fake_frappe,
        )

        self.assertIn("delivery.update_batch", context["permissions"])
        self.assertIn("payments.collect", context["permissions"])
        self.assertEqual(context["employee"]["department"], "Delivery")
        self.assertEqual(context["employee"]["branch"], "Main Branch")
        self.assertEqual(context["scopes"]["branch_names"], ["Main Branch"])
        self.assertEqual(context["scopes"]["department_names"], ["Delivery"])
        self.assertNotIn("salary", context["employee"])
        self.assertNotIn("bank_ac_no", context["employee"])


class FakeFrappe:
    def __init__(self, config=None, missing_branch_doctype=False):
        self.conf = types.SimpleNamespace(**(config or {}))
        self.missing_branch_doctype = missing_branch_doctype
        self.users = {}
        self.employees = {}
        self.departments = set()
        self.branches = set()
        self.created_users = []
        self.created_employees = []
        self.created_departments = []
        self.created_branches = []
        self.commits = 0
        self.db = FakeDB(self)

    def get_doc(self, *args):
        if len(args) == 2:
            doctype, name = args
            if doctype == "User":
                return self.users[name]
            if doctype == "Employee":
                return self.employees[name]
            raise AssertionError(f"unexpected existing doctype {doctype}")

        values = args[0]
        doctype = values["doctype"]
        if doctype == "User":
            return FakeUser(self, values["email"], values)
        if doctype == "Employee":
            return FakeEmployee(self, values["employee_name"], values)
        if doctype == "Department":
            return FakeNamedDoc(self, "Department", values["department_name"], values)
        if doctype == "Branch":
            return FakeNamedDoc(self, "Branch", values["branch"], values)
        raise AssertionError(f"unexpected doctype {doctype}")

    def get_meta(self, doctype):
        if doctype == "Branch" and self.missing_branch_doctype:
            raise RuntimeError("missing Branch")
        if doctype == "Employee":
            return FakeMeta(["user_id", "employee_name", "company", "department", "designation", "branch"])
        if doctype == "Branch":
            return FakeMeta(["branch", "company"])
        raise RuntimeError(f"unexpected meta {doctype}")

    def get_roles(self, user):
        return sorted(self.users[user].roles)

    def get_all(self, doctype, filters=None, fields=None, pluck=None, limit=20):
        if doctype == "Company" and pluck == "name":
            return ["Madar"]
        if doctype == "Department" and pluck == "name":
            department_name = filters.get("department_name")
            return [department_name] if department_name in self.departments else []
        if doctype == "Employee":
            if pluck == "name":
                for employee in self.employees.values():
                    if employee.user_id == filters.get("user_id"):
                        return [employee.name]
                return []
            for employee in self.employees.values():
                if employee.user_id == filters.get("user_id"):
                    return [{field: getattr(employee, field, None) for field in fields}]
        if doctype == "Branch":
            branch_name = filters.get("name")
            if branch_name in self.branches:
                return [{"name": branch_name, "branch": branch_name, "company": "Madar"}]
        return []


class FakeDB:
    def __init__(self, frappe):
        self.frappe = frappe

    def exists(self, doctype, name):
        if doctype == "User":
            return name in self.frappe.users
        if doctype == "Employee":
            return name in self.frappe.employees
        if doctype == "Department":
            return name in self.frappe.departments
        if doctype == "Branch":
            return (not self.frappe.missing_branch_doctype) and name in self.frappe.branches
        return False

    def commit(self):
        self.frappe.commits += 1


class FakeUser:
    def __init__(self, frappe, email, values=None):
        self._frappe = frappe
        self.email = email
        self.name = email
        self.roles = set()
        self.added_roles = []
        self.new_password = None
        self.reset_password_key = None
        for key, value in (values or {}).items():
            setattr(self, key, value)

    def insert(self, ignore_permissions=False):
        self._frappe.users[self.email] = self
        self._frappe.created_users.append(self.email)
        return self

    def add_roles(self, *role_names):
        for role_name in role_names:
            if role_name not in self.roles:
                self.roles.add(role_name)
                self.added_roles.append(role_name)

    def save(self, ignore_permissions=False):
        return self


class FakeEmployee:
    def __init__(self, frappe, name, values):
        self._frappe = frappe
        self.name = name
        for key, value in values.items():
            setattr(self, key, value)

    def insert(self, ignore_permissions=False):
        self._frappe.employees[self.name] = self
        self._frappe.created_employees.append(self.name)
        return self

    def save(self, ignore_permissions=False):
        return self


class FakeNamedDoc:
    def __init__(self, frappe, doctype, name, values):
        self._frappe = frappe
        self.doctype = doctype
        self.name = name
        for key, value in values.items():
            setattr(self, key, value)

    def insert(self, ignore_permissions=False):
        if self.doctype == "Department":
            self._frappe.departments.add(self.name)
            self._frappe.created_departments.append(self.name)
        elif self.doctype == "Branch":
            self._frappe.branches.add(self.name)
            self._frappe.created_branches.append(self.name)
        return self


class FakeMeta:
    def __init__(self, fields):
        self._fields = set(fields)

    def has_field(self, fieldname):
        return fieldname in self._fields
