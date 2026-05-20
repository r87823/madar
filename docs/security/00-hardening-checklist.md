# Madar Security Hardening Checklist

R10-T01 is a hardening pass for the current staging MVP. It does not introduce
new workflows and must not create, submit, or mutate ERPNext accounting,
delivery, or stock documents.

## Guest Endpoints

Allowed guest endpoint:

- `/api/method/madar.api.health.ping`

All other `frappe.whitelist()` methods must authenticate the current Frappe
session and reject `Guest`.

## Permission Model

Protected actions must use Madar permission keys from `madar.permissions`, not
direct role checks in business services.

Critical permission gates:

- `accounting.finalize` or `system.full_access` is required to submit ERP Sales
  Invoices, submit ERP Payment Entries, or finalize accounting.
- `settings.manage` or `system.full_access` is required to update admin
  settings.
- `accounting.view_sync_logs` is read-only for accounting review and sync
  visibility unless paired with stronger permissions.
- `payments.collect`, `cashbox.review`, `delivery.update_batch`,
  `production.update_work_order`, `orders.create`, and `orders.approve` remain
  separate operational permissions.

Direct role names are allowed only in the permission registry, role bootstrap,
tests, and documentation.

## Scope Model

Scope-sensitive services must continue to enforce:

- Branch users only see and mutate orders/payments/cashbox actions inside their
  branch scope.
- Branch pickup receiving and customer handoff are limited to scoped
  destination branches.
- Drivers only see and update delivery batches assigned to them unless they
  have broader delivery/admin permissions.
- Production users see department work where department scope is available.
- Users see only their own notifications.
- Users see only their own cashbox unless they have review/accounting/admin
  permission.

## Flutter Boundary

Flutter must call Madar/Frappe whitelisted methods only. It must not call:

- `/api/resource`
- ERPNext DocTypes directly
- Sales Order
- Sales Invoice
- Payment Entry
- Delivery Note
- Stock Entry

Flutter must not contain ERP credentials, API keys, passwords, SSH credentials,
or payment gateway secrets.

## Settings Safety

Admin settings are non-secret operational switches only. `Madar Setting` rows
with `is_secret=1` must not be returned to Flutter. Unknown setting keys and
invalid value types must be rejected.

R10 scan expectation:

- No ERP credential setting keys.
- No password or secret fields in the Flutter settings UI.
- Settings changes are the only mutation allowed by R9/R10 settings work.

## ERP Finalization Safety

There must be no automatic final submit. ERP finalization is explicit and
accounting-controlled.

Allowed finalization mutations are limited to the existing explicit APIs:

- Submit existing ERP Sales Invoice Draft.
- Submit existing ERP Payment Entry Drafts.
- Mark Madar accounting finalization metadata.

Still disallowed in this hardening task:

- Delivery Note creation.
- Stock Entry creation.
- Refunds.
- Cancellations.
- Credit notes.
- Automatic background finalization.

## Notifications Safety

Notifications are in-app only. Users can list, count, and mark read only their
own notifications. Deep link metadata is navigation context only; target
backend APIs must still enforce permissions and scopes.

Notification failures must not break the workflow that triggered them.

## Automated Scan

Run:

```bash
python3 scripts/check_security_rules.py
```

The script checks:

- Unsafe `allow_guest=True`.
- Flutter direct ERP/resource access.
- Direct Madar role names in service/API logic.
- Obvious committed credential patterns.

The script is intentionally lightweight and does not replace code review.
