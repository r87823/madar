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

R3-T04 freezes approved Madar orders and introduces an internal ERP sync boundary. The boundary can validate an approved order and prepare a safe Sales Order-shaped payload, but it must not insert ERPNext `Sales Order` documents, mutate stock, create invoices, or post accounting entries. Actual ERPNext synchronization remains a later explicit server-side task.

R3-T05 adds the first one-way internal sync from an approved `Madar Order` to a draft ERPNext `Sales Order`. The Madar order remains the operational workflow source, while the ERPNext Sales Order is the commercial/accounting representation for later ERP processing. This sync does not submit the Sales Order, reserve stock, create Delivery Notes, create Sales Invoices, create Payment Entries, or trigger production.

### Production Mapping Foundation

R4-T01 adds Madar-owned production setup records for production centers, production departments, and item-to-department mappings. These records prepare approved operational orders for future production planning by validating that every order item has an active production department mapping.

This foundation does not create production work orders, mutate ERPNext Items, reserve stock, create delivery records, create invoices, create payments, or post accounting entries.

### Delivery Readiness

R5-T01 adds Madar-owned delivery readiness and dispatch state on `Madar Order`. Branch pickup is the default fulfillment method: production prepares the order, the order is dispatched to the destination branch, the branch receives it, marks it ready for customer pickup, and then marks customer pickup complete.

Customer delivery is supported as a secondary fulfillment method through a direct dispatch-to-customer flow. This phase does not assign drivers, optimize routes, track GPS, create ERPNext Delivery Notes, move stock, create invoices, create payments, or touch cashbox records.

R5-T02 adds `Madar Delivery Batch` as the operational assignment unit for drivers. Orders are linked to a batch through `Madar Delivery Batch Order`; drivers are assigned to the batch rather than to individual orders.

Branch pickup orders form `branch_transfer` batches and must share the same destination branch. Customer delivery orders form `customer_delivery` batches. Batch pickup, out-for-delivery, delivered, and returned transitions remain inside Madar and cascade safe delivery status updates to linked Madar orders. This still does not create ERPNext Delivery Notes, stock movements, invoices, payments, cashbox records, GPS records, or route optimization artifacts.

### Operational Payments

R6-T01 adds `Madar Payment` as the operational collection record. Madar updates payment summaries on `Madar Order` (`paid_amount`, `remaining_amount`, and `payment_status`) from collected Madar payments only.

Operational payments are not ERPNext accounting entries. R6-T01 must not create ERPNext `Payment Entry`, `Sales Invoice`, refunds, terminal integrations, or accounting postings.

### Cashbox Custody

R6-T02 adds Madar-owned daily cashbox custody for operational cash payments. Cashbox records and entries are custody records only: they track who collected cash, the daily expected cash from linked `Madar Payment` rows, submitted cash, differences, and cashier/accountant review.

Cashbox custody does not create ERPNext `Payment Entry`, `Sales Invoice`, GL entries, bank reconciliation records, refunds, or cash account postings. ERPNext accounting synchronization remains a later explicit workflow.

### Payment Entry Sync

R6-T03 adds one-way sync from `Madar Payment` to ERPNext `Payment Entry` as draft records only. `Madar Payment` remains the operational payment source, and the ERPNext Payment Entry is an accounting representation for later ERP review.

This sync requires the related Madar Order to already reference an ERPNext Sales Order. It stores `erp_sync_status`, `erp_sync_error`, and `erp_payment_entry` on the Madar Payment. It must not submit Payment Entries, create Sales Invoices, post GL entries, perform bank reconciliation, modify cashbox approval status, create refunds, or run bidirectional sync.

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
