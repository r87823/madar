# Executive Architecture

Madar is the operational API and workflow layer between the Flutter mobile app and the ERPNext + Frappe HR/HRMS site.

```text
Flutter App -> Madar Frappe APIs -> ERPNext + Frappe HR/HRMS
```

The architecture protects ERPNext and HRMS by keeping sensitive resources behind Madar server-side APIs. Flutter communicates with Madar only. Madar then uses Frappe permissions, DocTypes, and server-side integrations to read or mutate ERPNext and HRMS data when a workflow requires it.

## Primary Responsibilities

Madar owns operational workflows:

- Orders.
- Approvals.
- Production.
- Delivery.
- Payments.
- Cashbox.
- Notifications.
- Employee self-service APIs.

ERPNext owns business system records:

- Customers.
- Items.
- Warehouses.
- Stock.
- Sales Orders.
- Sales Invoices.
- Payment Entries.
- Accounting reports.

HRMS owns workforce records:

- Employees.
- Attendance.
- Employee Checkins.
- Shifts.
- Leaves.
- Payroll.

## Security Direction

Flutter must not call ERPNext or HRMS sensitive resources directly, and it must not store ERPNext credentials. Mobile access must be expressed through Madar whitelisted methods that validate permissions, return stable JSON, and hide internal ERPNext/HRMS implementation details.

## Implementation Direction

Madar should use Frappe DocTypes and Frappe permissions rather than ad hoc security checks. Protected actions should call permission helper functions. Sensitive mutations should create audit logs. Status transitions should be handled through state machine services. Long-running work should be sent to Frappe background jobs.

