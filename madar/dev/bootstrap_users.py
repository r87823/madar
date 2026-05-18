import os
from dataclasses import dataclass
from datetime import date

from madar.permissions import checks
from madar.permissions.roles import (
    MADAR_ACCOUNTANT,
    MADAR_BRANCH_SUPERVISOR,
    MADAR_BRANCH_USER,
    MADAR_CASHIER,
    MADAR_DRIVER,
    MADAR_EMPLOYEE,
)
from madar.permissions.scopes import get_context_scopes
from madar.services.branch_context import get_branch_context
from madar.services.employee_context import get_employee_context


BOOTSTRAP_ENABLED_CONFIG_KEY = "enable_madar_dev_user_bootstrap"
BOOTSTRAP_ENABLED_ENV = "MADAR_ENABLE_DEV_USER_BOOTSTRAP"
BOOTSTRAP_PASSWORD_CONFIG_KEY = "madar_dev_user_password"
BOOTSTRAP_PASSWORD_ENV = "MADAR_DEV_USER_PASSWORD"
DEFAULT_COMPANY = "Madar"
DEFAULT_GENDER = "Other"
DEFAULT_DATE_OF_BIRTH = date(1990, 1, 1)
DEFAULT_DATE_OF_JOINING = date(2026, 1, 1)
DEFAULT_NAMING_SERIES = "HR-EMP-"


@dataclass(frozen=True)
class DevUserDefinition:
    email: str
    full_name: str
    roles: tuple
    department: str
    branch: str


DEV_USERS = [
    DevUserDefinition(
        email="employee.test@example.com",
        full_name="Madar Dev Employee",
        roles=(MADAR_EMPLOYEE,),
        department="General",
        branch="Main Branch",
    ),
    DevUserDefinition(
        email="driver.test@example.com",
        full_name="Madar Dev Driver",
        roles=(MADAR_EMPLOYEE, MADAR_DRIVER),
        department="Delivery",
        branch="Main Branch",
    ),
    DevUserDefinition(
        email="branch.user@example.com",
        full_name="Madar Dev Branch User",
        roles=(MADAR_EMPLOYEE, MADAR_BRANCH_USER),
        department="Branch Operations",
        branch="Main Branch",
    ),
    DevUserDefinition(
        email="branch.supervisor@example.com",
        full_name="Madar Dev Branch Supervisor",
        roles=(MADAR_EMPLOYEE, MADAR_BRANCH_SUPERVISOR),
        department="Branch Operations",
        branch="Main Branch",
    ),
    DevUserDefinition(
        email="cashier.test@example.com",
        full_name="Madar Dev Cashier",
        roles=(MADAR_EMPLOYEE, MADAR_CASHIER),
        department="Finance",
        branch="Main Branch",
    ),
    DevUserDefinition(
        email="accountant.test@example.com",
        full_name="Madar Dev Accountant",
        roles=(MADAR_EMPLOYEE, MADAR_ACCOUNTANT),
        department="Finance",
        branch="HQ",
    ),
]


def bootstrap_dev_users(frappe_module=None, password=None, enabled=None):
    if frappe_module is None:
        import frappe as frappe_module

    if enabled is None:
        enabled = _is_bootstrap_enabled(frappe_module)

    if not enabled:
        return {"enabled": False, "users": []}

    resolved_password = password or _get_bootstrap_password(frappe_module)
    if not resolved_password:
        raise RuntimeError(
            "Madar dev user bootstrap requires MADAR_DEV_USER_PASSWORD or site config."
        )

    company = _get_default_company(frappe_module)
    department_names = _ensure_departments(frappe_module, company)
    _ensure_branches_if_available(frappe_module)

    bootstrapped_users = []
    for definition in DEV_USERS:
        user_doc = _ensure_user(frappe_module, definition, resolved_password)
        _ensure_roles(user_doc, definition.roles)
        _ensure_employee(frappe_module, definition, company, department_names.get(definition.department))
        bootstrapped_users.append(definition.email)

    frappe_module.db.commit()
    return {"enabled": True, "users": bootstrapped_users}


def get_expected_context_for_dev_user(email, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    roles = frappe_module.get_roles(email)
    permissions = checks.get_permissions_for_roles(roles)
    employee = get_employee_context(email, frappe_module=frappe_module)
    return {
        "user": email,
        "roles": list(roles or []),
        "permissions": permissions,
        "employee": employee,
        "branch": get_branch_context(employee, frappe_module=frappe_module),
        "scopes": get_context_scopes(employee=employee, permissions=permissions),
    }


def _is_bootstrap_enabled(frappe_module):
    config_value = _get_config_value(frappe_module, BOOTSTRAP_ENABLED_CONFIG_KEY)
    env_value = os.environ.get(BOOTSTRAP_ENABLED_ENV)
    return _truthy(config_value) or _truthy(env_value)


def _get_bootstrap_password(frappe_module):
    return os.environ.get(BOOTSTRAP_PASSWORD_ENV) or _get_config_value(
        frappe_module,
        BOOTSTRAP_PASSWORD_CONFIG_KEY,
    )


def _get_config_value(frappe_module, key):
    return getattr(getattr(frappe_module, "conf", None), key, None)


def _truthy(value):
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _get_default_company(frappe_module):
    try:
        companies = frappe_module.get_all("Company", pluck="name", limit=1)
    except Exception:
        companies = []

    if companies:
        return companies[0]
    return DEFAULT_COMPANY


def _ensure_departments(frappe_module, company):
    department_names = {}
    for department in sorted({definition.department for definition in DEV_USERS}):
        existing = _find_department(frappe_module, department, company)
        if existing:
            department_names[department] = existing
            continue

        department_doc = frappe_module.get_doc(
            {
                "doctype": "Department",
                "department_name": department,
                "company": company,
            }
        ).insert(ignore_permissions=True)
        department_names[department] = getattr(department_doc, "name", department)

    return department_names


def _find_department(frappe_module, department, company):
    try:
        rows = frappe_module.get_all(
            "Department",
            filters={"department_name": department, "company": company},
            pluck="name",
            limit=1,
        )
        if rows:
            return rows[0]
    except Exception:
        pass

    if frappe_module.db.exists("Department", department):
        return department

    return None


def _ensure_branches_if_available(frappe_module):
    try:
        frappe_module.get_meta("Branch")
    except Exception:
        return

    for branch in sorted({definition.branch for definition in DEV_USERS}):
        if frappe_module.db.exists("Branch", branch):
            continue
        frappe_module.get_doc(
            {
                "doctype": "Branch",
                "branch": branch,
            }
        ).insert(ignore_permissions=True)


def _ensure_user(frappe_module, definition, password):
    if frappe_module.db.exists("User", definition.email):
        user_doc = _get_existing_doc(frappe_module, "User", definition.email)
    else:
        user_doc = frappe_module.get_doc(
            {
                "doctype": "User",
                "email": definition.email,
                "first_name": definition.full_name,
                "full_name": definition.full_name,
                "enabled": 1,
                "user_type": "System User",
                "send_welcome_email": 0,
            }
        ).insert(ignore_permissions=True)

    _set_password_fields(user_doc, password)
    _set_force_reset_fields(user_doc)
    user_doc.save(ignore_permissions=True)
    return user_doc


def _ensure_roles(user_doc, role_names):
    existing_roles = _get_role_names(user_doc)
    missing_roles = [role_name for role_name in role_names if role_name not in existing_roles]
    if missing_roles:
        user_doc.add_roles(*missing_roles)


def _ensure_employee(frappe_module, definition, company, department):
    employee_id = _find_employee_for_user(frappe_module, definition.email)
    values = {
        "doctype": "Employee",
        "naming_series": DEFAULT_NAMING_SERIES,
        "employee_name": definition.full_name,
        "first_name": definition.full_name,
        "gender": DEFAULT_GENDER,
        "date_of_birth": DEFAULT_DATE_OF_BIRTH,
        "date_of_joining": DEFAULT_DATE_OF_JOINING,
        "company": company,
        "department": department or definition.department,
        "user_id": definition.email,
        "branch": definition.branch,
        "status": "Active",
    }

    if employee_id and frappe_module.db.exists("Employee", employee_id):
        employee_doc = _get_existing_doc(frappe_module, "Employee", employee_id)
        for field, value in values.items():
            if field != "doctype":
                setattr(employee_doc, field, value)
        employee_doc.save(ignore_permissions=True)
        return employee_doc

    return frappe_module.get_doc(values).insert(ignore_permissions=True)


def _get_existing_doc(frappe_module, doctype, name):
    return frappe_module.get_doc(doctype, name)


def _find_employee_for_user(frappe_module, email):
    try:
        rows = frappe_module.get_all(
            "Employee",
            filters={"user_id": email},
            pluck="name",
            limit=1,
        )
        if rows:
            return rows[0]
    except Exception:
        return None
    return None


def _get_role_names(user_doc):
    role_names = set()
    for role in getattr(user_doc, "roles", []) or []:
        if isinstance(role, str):
            role_names.add(role)
        else:
            role_name = getattr(role, "role", None) or getattr(role, "name", None)
            if role_name:
                role_names.add(role_name)
    return role_names


def _set_password_fields(user_doc, password):
    if hasattr(user_doc, "new_password"):
        user_doc.new_password = password
    else:
        setattr(user_doc, "new_password", password)


def _set_force_reset_fields(user_doc):
    setattr(user_doc, "reset_password_key", "force-reset")
