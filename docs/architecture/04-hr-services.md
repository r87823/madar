# HR Services

Madar may provide employee self-service APIs for Flutter, but HRMS remains the source of truth for employee and HR records.

## Ownership

HRMS owns:

- Employees.
- Attendance.
- Employee Checkins.
- Shifts.
- Leaves.
- Payroll.

Madar owns:

- Mobile-facing employee self-service API orchestration.
- Permission checks around mobile HR actions.
- Stable response shapes and mobile error codes.
- Audit logging for future sensitive HR mutations.

## Service Boundary

Future HR services in Madar should be thin orchestration layers. They may validate mobile requests, call permission helpers, call HRMS/Frappe document behavior, and format mobile responses. They should not duplicate HRMS payroll, attendance, leave, or shift engines.

## Employee Context Lookup

The authenticated current user context endpoint may include a safe Employee summary when HRMS links an Employee to the current Frappe user.

The lookup is read-only:

- Use the current Frappe session user.
- Prefer `Employee.user_id` when that field exists.
- Return `employee: null` if the Employee DocType is unavailable, the field is unavailable, no Employee is linked, or lookup fails.
- Do not create or update Employee records.
- Do not expose salary, bank details, national IDs, private HR data, credentials, or session internals.

Safe Employee context fields are limited to:

- `name`.
- `employee_name`.
- `company`.
- `department`.
- `designation`.
- `branch`, only when the field exists.
- `image`, only when the field exists.
- `status`, only when the field exists.

Top-level `branch` remains `null` until branch access rules are defined.

## Branch Context and Scopes

The authenticated current user context may include a safe top-level Branch summary when Employee context includes a branch value.

Branch lookup is read-only:

- Use `employee.branch` when available.
- If the Branch DocType exists, read only safe display fields.
- If the Branch DocType is unavailable or lookup fails, return a minimal branch context from `employee.branch`.
- If there is no employee or no employee branch, return `branch: null`.
- Do not create or update Branch records.

Safe Branch fields are limited to:

- `name`.
- `branch`.
- `company`.

The context also includes read-only scope helpers:

- `branch_names`: employee branch or `[]`.
- `department_names`: employee department or `[]`.
- `["*"]` may be returned by the scope helper for `system.full_access` users.

These scopes are only a foundation for future filtering. They do not implement attendance, leave, payroll, order, delivery, payment, cashbox, production, approval, or notification behavior.

## Rules

- Do not expose HRMS sensitive resources directly to Flutter.
- Do not store ERPNext or HRMS credentials in Flutter.
- Use whitelisted Madar methods for employee self-service APIs.
- Use Frappe permissions and Madar permission helpers for protected HR actions.
- Create audit logs for future sensitive HR mutations.
- Use background jobs for long-running HR operations.
