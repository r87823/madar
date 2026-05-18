# Mobile API Rules

Flutter communicates with Madar through whitelisted Frappe methods. Madar is responsible for authentication, authorization, validation, orchestration, and stable response formatting.

## Access Rules

- Mobile APIs must be Frappe whitelisted methods.
- Flutter must not call ERPNext or HRMS sensitive resources directly.
- Flutter must not store ERPNext credentials.
- Mobile endpoints must validate permission server-side.
- Protected endpoint code must use permission helper functions, not direct role checks.

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

## Long-Running Work

Any long-running process must use Frappe background jobs. Mobile endpoints should enqueue the job and return a stable response that lets Flutter track or refresh status.
