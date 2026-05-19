# Mobile API Rules

Flutter communicates with Madar through whitelisted Frappe methods. Madar is responsible for authentication, authorization, validation, orchestration, and stable response formatting.

## Access Rules

- Mobile APIs must be Frappe whitelisted methods.
- Flutter must not call ERPNext or HRMS sensitive resources directly.
- Flutter must not store ERPNext credentials.
- Mobile endpoints must validate permission server-side.
- Protected endpoint code must use permission helper functions, not direct role checks.
- Authenticated mobile context is available at `/api/method/madar.api.me.get_context`.
- The context endpoint must not use `allow_guest=True`.
- Future protected actions should evaluate Madar permission keys, not raw role names.
- Madar-specific Frappe Roles are bootstrapped during migration and mapped to Madar permission keys.
- Current user context may include a safe read-only Employee summary when a linked Employee exists.
- Employee lookup failures must not break the current user context endpoint.
- Current user context includes a `scopes` object with `branch_names` and `department_names`.
- The top-level `branch` value is read-only and may be `null` or a safe Branch summary.
- Scope values are a foundation for future filtering only; no domain filtering is implemented in this task.

## Readiness Endpoint

Madar exposes a basic readiness endpoint for safe service checks:

```text
/api/method/madar.api.health.ping
```

The endpoint returns a static service payload and must not call ERPNext, HRMS, or perform database mutations.

## Response Shape

Every future mobile endpoint should return predictable JSON. Once the shared envelope is defined, endpoints should use it consistently.

Recommended direction:

```json
{
  "ok": true,
  "data": {},
  "error": null
}
```

For failures:

```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "STABLE_ERROR_CODE",
    "message": "Human-readable message"
  }
}
```

## Error Codes

Mobile endpoints must use stable error codes so Flutter can handle failures safely. Future codes should be documented before broad use and should not expose sensitive internal details.

Suggested categories:

- `AUTH_REQUIRED`.
- `PERMISSION_DENIED`.
- `VALIDATION_FAILED`.
- `NOT_FOUND`.
- `CONFLICT`.
- `INVALID_STATE_TRANSITION`.
- `BACKGROUND_JOB_QUEUED`.
- `INTERNAL_ERROR`.

Attendance endpoints also use:

- `EMPLOYEE_NOT_LINKED`.
- `EMPLOYEE_CHECKIN_UNAVAILABLE`.
- `DUPLICATE_CHECKIN`.
- `ALREADY_CHECKED_IN`.
- `ALREADY_CHECKED_OUT`.

Order draft endpoints also use:

- `ORDER_NOT_FOUND`.
- `INVALID_ORDER_TRANSITION`.

## Order Draft Endpoints

R3-T01 exposes Madar operational order draft endpoints only:

```text
/api/method/madar.api.orders.create_draft
/api/method/madar.api.orders.list_orders
/api/method/madar.api.orders.get_order
/api/method/madar.api.orders.submit_order
/api/method/madar.api.orders.cancel_order
```

These endpoints are authenticated, return the shared `ok/data/error` envelope, and must not call ERPNext Sales Order APIs or `/api/resource` endpoints. Flutter sends only customer display fields and notes; Madar derives actor, branch, scopes, and status server-side.

## Long-Running Work

Any long-running process must use Frappe background jobs. Mobile endpoints should enqueue the job and return a stable response that lets Flutter track or refresh status.
