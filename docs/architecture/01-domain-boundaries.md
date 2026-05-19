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

### Operational Order Drafts

`Madar Order` is an operational workflow document owned by Madar. In R3-T01 it supports only draft order capture, scoped viewing, and simple `draft`, `submitted`, and `cancelled` transitions.

`Madar Order` is not an ERPNext Sales Order. Creating, submitting, or cancelling a Madar order must not create stock, accounting, invoice, delivery, payment, or ERPNext Sales Order records. ERPNext integration comes in a later task through explicit server-side services.

R3-T02 adds `Madar Order Item` records and order totals for operational draft capture only. Adding, editing, or removing these line items must not reserve stock, validate warehouse availability, create invoices, create payments, apply taxes, or create ERPNext Sales Orders.

Madar may expose a safe product catalog bridge over ERPNext `Item`, but Flutter must never call ERPNext Item APIs directly. The bridge returns only mobile-safe display fields and an optional safe default price.

R3-T03 adds branch supervisor approval decisions for submitted Madar orders. Approval, return-for-edit, and rejection remain Madar operational states only and must not create ERPNext Sales Orders or downstream stock/accounting documents.

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
