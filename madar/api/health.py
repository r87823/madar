import frappe


@frappe.whitelist()
def ping():
    return {
        "ok": True,
        "app": "madar",
        "service": "Madar Frappe Backend",
    }
