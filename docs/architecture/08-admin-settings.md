# Admin Settings

R9-T01 adds a safe Arabic-first admin settings foundation for non-secret operational settings. Internal setting keys remain English for code stability.

## Boundary

Admin settings may update only `Madar Setting` records. This feature must not create or submit ERPNext documents, Delivery Notes, Stock Entries, Sales Invoices, Payment Entries, GL Entries, users, roles, or business workflow records.

This task must not store or expose secrets. Do not add ERP API keys, API secrets, database credentials, SSH credentials, email passwords, WhatsApp tokens, payment gateway secrets, or any password fields.

## Storage

Settings are stored in the `Madar Setting` DocType as non-secret key/value rows:

- `setting_key`.
- `setting_value`.
- `value_type`.
- `category`.
- `label_ar`.
- `description_ar`.
- `is_secret`.
- `is_editable`.
- `updated_by`.
- `updated_at`.

Rows are seeded idempotently by `madar.patches.v0_1.create_default_settings`.

If any row has `is_secret=1`, it must not be returned to Flutter. R9-T01 does not create secret settings.

## Initial Settings

- `app.default_language`: Arabic UI default, value `ar`.
- `attendance.duplicate_window_seconds`: duplicate attendance action window, default `60`.
- `orders.require_items_before_submit`: future order submit guard, default `true`.
- `payments.allow_overpayment`: overpayment toggle, default `false`.
- `payments.enabled_methods`: enabled payment methods, default `["cash", "card", "transfer", "online"]`.
- `cashbox.require_review`: cashbox review requirement, default `true`.
- `notifications.enabled`: internal notification creation toggle, default `true`.
- `erp.auto_sync_sales_order`: future auto Sales Order sync toggle, default `false`.
- `erp.auto_create_sales_invoice`: future auto invoice draft toggle, default `false`.

ERP auto settings are stored as operational toggles only. They do not create automatic sync behavior in R9-T01.

## APIs

R9-T01 exposes:

```text
/api/method/madar.api.settings.get_settings
/api/method/madar.api.settings.get_setting_metadata
/api/method/madar.api.settings.update_setting
```

All endpoints require authentication and do not use `allow_guest=True`.

## Permissions

Settings access uses Madar permission keys:

- `system.full_access`.
- `settings.manage`.

`Madar Admin`, `Administrator`, and `System Manager` receive `system.full_access`. Other roles must not update settings unless explicitly granted `settings.manage` in a future task.

No protected settings endpoint may use direct role checks.

## Validation

Unknown settings return `SETTING_NOT_FOUND`. Non-editable settings return `SETTING_NOT_EDITABLE`. Secret rows return `SETTING_SECRET_NOT_READABLE`. Invalid values return `SETTING_VALUE_INVALID`.

The settings service validates:

- `bool`: true or false only.
- `int`: non-negative integer.
- `json`: controlled list for `payments.enabled_methods`.
- `string`: safe string, currently `app.default_language=ar` only.

## Current Integrations

R9-T01 safely wires a small set of existing behavior:

- Attendance duplicate protection reads `attendance.duplicate_window_seconds`.
- Payment collection reads `payments.allow_overpayment`.
- Payment collection validates `payments.enabled_methods`.
- Notification creation checks `notifications.enabled`.

If settings are unavailable, existing safe defaults are used.

## Flutter

Flutter shows an Arabic `الإعدادات` screen only for users with `system.full_access` or `settings.manage`. Boolean settings use switches, integer settings use a numeric field, and payment methods use controlled chips. No secret, password, API key, or raw credential field may be displayed.
