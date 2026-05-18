# Madar Plans

This file tracks project-level implementation order. It is intentionally lightweight until feature tasks begin.

## R0: Foundation

- R0-T01: Madar project rules and architecture bootstrap.
- R0-T02: Define base mobile API response envelope and error code registry.
- R0-T03: Define permission helper patterns and audit log requirements.
- R0-T04: Define state machine service pattern for future workflow transitions.
- R0-T05: Define background job conventions for long-running operations.

## Future Domains

Future domain work must be planned before implementation and must respect the boundaries in `docs/architecture`.

- Orders and approvals.
- Production.
- Delivery.
- Payments and cashbox.
- Notifications.
- Employee self-service APIs.

## Delivery Rules

- Do not implement business logic in foundation tasks.
- For each feature task, document the DocTypes, permissions, mobile APIs, audit logs, and tests before coding.
- Keep ERPNext and HRMS as source systems for their owned records.
- Keep Flutter isolated from ERPNext and HRMS sensitive resources through Madar APIs.

