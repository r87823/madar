# Madar Agent Rules

Madar is a Frappe custom app installed on the same site as ERPNext and Frappe HR/HRMS. Its first responsibility is to provide a controlled operational API layer for the Flutter mobile app while preserving ERPNext and HRMS as the source systems for their own domains.

## Product Boundary

- Flutter App -> Madar Frappe APIs -> ERPNext + Frappe HR/HRMS.
- Flutter must not call ERPNext or HRMS sensitive resources directly.
- Flutter must not store ERPNext user credentials.
- Madar owns operational workflows and mobile-facing orchestration.
- ERPNext owns commercial, inventory, accounting, and reporting records.
- HRMS owns employee, attendance, shift, leave, and payroll records.

## Implementation Rules

- Use Frappe DocTypes and Frappe permissions as the authorization foundation.
- Expose mobile APIs only through Frappe whitelisted methods.
- Do not perform direct role checks for protected actions.
- Use permission helper functions from `madar.permissions` for protected actions.
- Any future sensitive mutation must create an audit log.
- Any future status transition must go through a state machine service.
- Any long-running process must use Frappe background jobs.
- Any mobile endpoint must return predictable JSON and stable error codes.

## Scope Guard

Do not add order, delivery, payment, cashbox, production, approval, notification, or HR business logic during architecture bootstrap tasks. Create rules, package boundaries, and documentation only unless a later task explicitly asks for business behavior.

## Existing Health Endpoint

Keep the existing `madar/api/health.py` endpoint working. Architecture changes must not remove, rename, or change health-check behavior unless a task explicitly covers health checks.

## Coding Expectations

- Prefer small services with clear dependencies.
- Keep mobile response shapes stable once introduced.
- Keep all sensitive behavior server-side in Madar.
- Avoid direct database writes when a Frappe document API or ERPNext/HRMS service API is available.
- Add tests when adding executable behavior.

