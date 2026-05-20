from madar.permissions.roles import (
    MADAR_ACCOUNTANT,
    MADAR_ADMIN,
    MADAR_BRANCH_SUPERVISOR,
    MADAR_BRANCH_USER,
    MADAR_CASHIER,
    MADAR_DRIVER,
    MADAR_EMPLOYEE,
    MADAR_PRODUCTION_USER,
)


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
    "production.manage_mappings",
    "delivery.view_assigned_batches",
    "delivery.update_batch",
    "payments.collect",
    "cashbox.view_own",
    "cashbox.submit",
    "cashbox.review",
    "accounting.view_sync_logs",
    "accounting.finalize",
    "settings.manage",
]


ROLE_PERMISSION_MAP = {
    "Administrator": ["system.full_access"],
    "System Manager": ["system.full_access"],
    "Accounts User": ["accounting.view_sync_logs"],
    MADAR_ADMIN: ["system.full_access"],
    "Employee": [
        "attendance.check_in",
        "attendance.check_out",
        "employee_services.view_self",
        "employee_services.request_leave",
    ],
    MADAR_EMPLOYEE: [
        "attendance.check_in",
        "attendance.check_out",
        "employee_services.view_self",
        "employee_services.request_leave",
    ],
    MADAR_BRANCH_USER: [
        "orders.create",
        "orders.submit_for_approval",
    ],
    MADAR_BRANCH_SUPERVISOR: [
        "orders.approve",
    ],
    MADAR_PRODUCTION_USER: [
        "production.view_work_orders",
        "production.update_work_order",
    ],
    MADAR_DRIVER: [
        "delivery.view_assigned_batches",
        "delivery.update_batch",
        "payments.collect",
        "cashbox.view_own",
        "cashbox.submit",
    ],
    MADAR_ACCOUNTANT: [
        "accounting.view_sync_logs",
        "accounting.finalize",
        "cashbox.review",
    ],
    MADAR_CASHIER: [
        "payments.collect",
        "cashbox.view_own",
        "cashbox.submit",
        "cashbox.review",
    ],
}
