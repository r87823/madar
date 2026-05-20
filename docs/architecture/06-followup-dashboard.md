# Follow-up Dashboard

R8-T01 adds a read-only operational follow-up dashboard for Madar. The Flutter screen is named `لوحة المتابعة` and summarizes counts and alerts that the current user is allowed to see.

## Boundary

The dashboard is a summary surface only. It must not create, update, submit, cancel, or delete Madar or ERPNext documents. It must not create ERPNext Delivery Notes, Stock Entries, Sales Invoices, Payment Entries, GL Entries, or any external notification records.

Flutter calls only:

```text
/api/method/madar.api.followup_dashboard.get_summary
```

The endpoint requires authentication and does not use `allow_guest=True`.

## Response Shape

The endpoint returns the existing Madar envelope:

```json
{
  "ok": true,
  "data": {
    "cards": [],
    "alerts": []
  },
  "error": null
}
```

Each card contains:

- `key`.
- `title`.
- `value`.
- `subtitle`.
- `priority`.
- `route_key`.
- `route_params`.

Each alert contains:

- `key`.
- `title`.
- `message`.
- `priority`.
- `route_key`.
- `route_params`.

Titles and user-visible alert messages are Arabic-first. Route keys remain stable English identifiers for Flutter navigation.

## Permission Visibility

The service uses Madar permission keys and scope helpers. It must not use direct protected role checks.

Implemented cards:

- `orders_today`: visible to `orders.create`, `orders.approve`, or `system.full_access`.
- `orders_pending_approval`: visible to `orders.approve` or `system.full_access`.
- `production_in_progress`: visible to `production.view_work_orders` or `system.full_access`.
- `production_delayed`: visible to `production.view_work_orders` or `system.full_access`.
- `ready_for_dispatch`: visible to `delivery.view_assigned_batches`, `delivery.update_batch`, or `system.full_access`.
- `active_delivery_batches`: visible to `delivery.view_assigned_batches`, `delivery.update_batch`, or `system.full_access`.
- `payments_today`: visible to `payments.collect`, `accounting.view_sync_logs`, or `system.full_access`.
- `cashboxes_waiting_review`: visible to `cashbox.review`, `accounting.view_sync_logs`, or `system.full_access`.
- `erp_sync_failed`: visible to `accounting.view_sync_logs` or `system.full_access`.
- `accounting_ready_for_review`: visible to `accounting.view_sync_logs` or `system.full_access`.
- `unread_notifications`: visible to all authenticated users.
- `attendance_state`: visible to users with `attendance.check_in`, `attendance.check_out`, or `system.full_access`.

## Scope Rules

Branch-scoped users see branch-scoped counts where the underlying workflow has a branch field, such as Madar Orders. Production users are limited by `department_names` where the work order department is known. Drivers see only their assigned active delivery batches. Accounting users may see accounting-wide sync and review summaries. `system.full_access` sees all summary cards.

The dashboard returns counts and safe status text only. It does not expose raw document rows, sensitive customer/payment details, ERP tracebacks, salary data, bank details, national identifiers, API secrets, passwords, or session internals.

## Alerts

High-priority alerts are generated for actionable count failures such as delayed production, waiting cashboxes, and ERP sync failures. Query failures should not break the whole dashboard; the affected count can safely fall back to zero.

## Flutter Navigation

Flutter may use `route_key` to open already implemented Madar screens:

- `orders_list`.
- `approval_queue`.
- `production_queue`.
- `dispatch_queue`.
- `my_delivery_batches`.
- `cashbox_review`.
- `erp_sync_review`.
- `accounting_review`.
- `notifications`.
- `attendance`.

Unsupported route keys show:

```text
لا يمكن فتح هذا القسم الآن
```

Navigation does not grant authorization. The destination screen must still fetch data through Madar APIs, and backend permissions and scopes remain authoritative.
