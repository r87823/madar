import frappe


@frappe.whitelist(allow_guest=True)
def ping():
    return {
        "ok": True,
        "app": "madar",
        "site": frappe.local.site,
    }
