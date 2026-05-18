from madar.permissions.roles import MADAR_ROLES


def execute(frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    for role_name in MADAR_ROLES:
        if frappe_module.db.exists("Role", role_name):
            continue

        frappe_module.get_doc(
            {
                "doctype": "Role",
                "role_name": role_name,
                "desk_access": 1,
            }
        ).insert(ignore_permissions=True)

    frappe_module.db.commit()

