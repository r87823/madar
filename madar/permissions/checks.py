from madar.permissions.registry import ALL_PERMISSION_KEYS, ROLE_PERMISSION_MAP


def get_permissions_for_roles(roles):
    role_names = set(roles or [])
    if any("system.full_access" in ROLE_PERMISSION_MAP.get(role, []) for role in role_names):
        return list(ALL_PERMISSION_KEYS)

    granted = set()
    for role in role_names:
        granted.update(ROLE_PERMISSION_MAP.get(role, []))

    return [permission for permission in ALL_PERMISSION_KEYS if permission in granted]


def has_permission(roles, permission_key):
    return permission_key in get_permissions_for_roles(roles)


def build_user_context(user, full_name, roles, employee=None, **_ignored_sensitive_values):
    role_list = list(roles or [])
    return {
        "user": user,
        "full_name": full_name,
        "roles": role_list,
        "permissions": get_permissions_for_roles(role_list),
        "employee": employee,
        "branch": None,
    }
