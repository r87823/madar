SAFE_EMPLOYEE_FIELDS = [
    "name",
    "employee_name",
    "company",
    "department",
    "designation",
    "branch",
    "image",
    "status",
]


def get_employee_context(user, frappe_module=None):
    if not user:
        return None

    if frappe_module is None:
        import frappe as frappe_module

    try:
        meta = frappe_module.get_meta("Employee")
        if not meta.has_field("user_id"):
            return None

        fields = [field for field in SAFE_EMPLOYEE_FIELDS if field == "name" or meta.has_field(field)]
        rows = frappe_module.get_all(
            "Employee",
            filters={"user_id": user},
            fields=fields,
            limit=1,
        )
    except Exception:
        return None

    if not rows:
        return None

    employee = rows[0]
    context = {}
    for field in fields:
        value = _get_value(employee, field)
        if value is not None:
            context[field] = value

    return context or None


def _get_value(row, field):
    if isinstance(row, dict):
        return row.get(field)
    return getattr(row, field, None)

