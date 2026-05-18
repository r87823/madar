FULL_ACCESS_PERMISSION = "system.full_access"


def get_context_scopes(employee, permissions):
    if FULL_ACCESS_PERMISSION in set(permissions or []):
        return {
            "branch_names": ["*"],
            "department_names": ["*"],
        }

    return {
        "branch_names": _scope_values(employee, "branch"),
        "department_names": _scope_values(employee, "department"),
    }


def _scope_values(source, field):
    value = _get_value(source, field)
    if not value:
        return []
    return list(dict.fromkeys([value]))


def _get_value(source, field):
    if not source:
        return None
    if isinstance(source, dict):
        return source.get(field)
    return getattr(source, field, None)

