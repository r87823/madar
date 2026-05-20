from madar.services.settings_service import ensure_default_settings


def execute(frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    ensure_default_settings(frappe_module=frappe_module)
