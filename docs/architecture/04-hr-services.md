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

## Rules

- Do not expose HRMS sensitive resources directly to Flutter.
- Do not store ERPNext or HRMS credentials in Flutter.
- Use whitelisted Madar methods for employee self-service APIs.
- Use Frappe permissions and Madar permission helpers for protected HR actions.
- Create audit logs for future sensitive HR mutations.
- Use background jobs for long-running HR operations.

