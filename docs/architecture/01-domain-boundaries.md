# Domain Boundaries

Madar, ERPNext, and HRMS share one Frappe site, but they do not share ownership of every business concept. The boundary is based on system responsibility, not database proximity.

## Madar-Owned Domains

Madar owns operational workflows and the mobile-facing orchestration around them:

- Orders.
- Approvals.
- Production.
- Delivery.
- Payments.
- Cashbox.
- Notifications.
- Employee self-service APIs.

Madar may reference ERPNext and HRMS records, but it should not silently replace their ownership. For example, a Madar workflow may refer to a Customer or Employee, while ERPNext or HRMS remains responsible for the canonical record.

## ERPNext-Owned Domains

ERPNext owns commercial, inventory, accounting, and reporting records:

- Customers.
- Items.
- Warehouses.
- Stock.
- Sales Orders.
- Sales Invoices.
- Payment Entries.
- Accounting reports.

Madar should use ERPNext through Frappe document APIs or explicit server-side service functions. It should not duplicate core ERPNext accounting or stock logic.

## HRMS-Owned Domains

HRMS owns workforce records:

- Employees.
- Attendance.
- Employee Checkins.
- Shifts.
- Leaves.
- Payroll.

Madar employee self-service APIs can expose controlled mobile operations, but HRMS remains the source of truth for employee and HR records.

## Boundary Rules

- Flutter calls Madar APIs only for protected workflows.
- Madar validates mobile intent and authorization before touching ERPNext or HRMS resources.
- ERPNext and HRMS records must be changed through supported Frappe document behavior, not direct SQL mutations.
- Cross-domain workflows must keep a clear audit trail when sensitive data changes.
- Future domain services should be small, named by capability, and testable without requiring Flutter behavior.

