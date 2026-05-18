SAFE_BRANCH_FIELDS = [
    "name",
    "branch",
    "company",
]


def get_branch_context(employee, frappe_module=None):
    branch_name = _get_value(employee, "branch")
    if not branch_name:
        return None

    if frappe_module is None:
        import frappe as frappe_module

    try:
        meta = frappe_module.get_meta("Branch")
        fields = [field for field in SAFE_BRANCH_FIELDS if field == "name" or meta.has_field(field)]
        rows = frappe_module.get_all(
            "Branch",
            filters={"name": branch_name},
            fields=fields,
            limit=1,
        )
    except Exception:
        return _minimal_branch_context(branch_name)

    if not rows:
        return _minimal_branch_context(branch_name)

    branch = rows[0]
    context = {}
    for field in fields:
        value = _get_value(branch, field)
        if value is not None:
            context[field] = value

    return context or _minimal_branch_context(branch_name)


def _minimal_branch_context(branch_name):
    return {
        "name": branch_name,
        "branch": branch_name,
    }


def _get_value(row, field):
    if not row:
        return None
    if isinstance(row, dict):
        return row.get(field)
    return getattr(row, field, None)

