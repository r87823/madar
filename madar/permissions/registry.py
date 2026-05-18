ALL_PERMISSION_KEYS = [
    "system.full_access",
    "attendance.check_in",
    "attendance.check_out",
    "employee_services.view_self",
    "employee_services.request_leave",
    "orders.create",
    "orders.submit_for_approval",
    "orders.approve",
    "production.view_work_orders",
    "production.update_work_order",
    "delivery.view_assigned_batches",
    "delivery.update_batch",
    "payments.collect",
    "cashbox.view_own",
    "cashbox.submit",
    "accounting.view_sync_logs",
]


ROLE_PERMISSION_MAP = {
    "Administrator": ["system.full_access"],
    "System Manager": ["system.full_access"],
    "Employee": [
        "attendance.check_in",
        "attendance.check_out",
        "employee_services.view_self",
        "employee_services.request_leave",
    ],
    "Branch User": [
        "orders.create",
        "orders.submit_for_approval",
    ],
    "Branch Supervisor": [
        "orders.approve",
    ],
    "Production User": [
        "production.view_work_orders",
        "production.update_work_order",
    ],
    "Driver": [
        "delivery.view_assigned_batches",
        "delivery.update_batch",
        "payments.collect",
        "cashbox.view_own",
        "cashbox.submit",
    ],
    "Accounts User": [
        "accounting.view_sync_logs",
    ],
    "Cashier": [
        "payments.collect",
        "cashbox.view_own",
        "cashbox.submit",
    ],
}

