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
- `ORDER_HAS_NO_ITEMS`.
- `REASON_REQUIRED`.
- `ORDER_NOT_EDITABLE`.
- `ORDER_ITEM_NOT_FOUND`.
- `PRODUCT_NOT_FOUND`.
- `INVALID_QUANTITY`.

Production mapping endpoints also use:

- `ITEM_NOT_FOUND`.
- `PRODUCTION_CENTER_NOT_FOUND`.
- `PRODUCTION_DEPARTMENT_NOT_FOUND`.
- `CENTER_CODE_REQUIRED`.
- `DEPARTMENT_CODE_REQUIRED`.

Production work order endpoints also use:

- `WORK_ORDER_NOT_FOUND`.
- `ITEM_DEPARTMENT_MAPPING_MISSING`.
- `INVALID_WORK_ORDER_TRANSITION`.

Delivery endpoints also use:

- `FULFILLMENT_METHOD_REQUIRED`.
- `DESTINATION_BRANCH_REQUIRED`.
- `INVALID_DELIVERY_TRANSITION`.
- `ORDER_NOT_READY_FOR_DISPATCH`.
- `OUT_OF_SCOPE`.

## Order Draft Endpoints

R3-T01 exposes Madar operational order draft endpoints only:

```text
/api/method/madar.api.orders.create_draft
/api/method/madar.api.orders.list_orders
/api/method/madar.api.orders.get_order
/api/method/madar.api.orders.submit_order
/api/method/madar.api.orders.cancel_order
/api/method/madar.api.orders.list_approval_queue
/api/method/madar.api.orders.approve_order
/api/method/madar.api.orders.return_order_for_edit
/api/method/madar.api.orders.reject_order
```

These endpoints are authenticated, return the shared `ok/data/error` envelope, and must not call ERPNext Sales Order APIs or `/api/resource` endpoints. Flutter sends only customer display fields and notes; Madar derives actor, branch, scopes, and status server-side.

## Catalog and Order Item Endpoints

R3-T02 exposes catalog and item APIs through Madar only:

```text
/api/method/madar.api.catalog.list_products
/api/method/madar.api.order_items.list_order_items
/api/method/madar.api.order_items.add_item
/api/method/madar.api.order_items.update_item_qty
/api/method/madar.api.order_items.remove_item
```

Flutter must not call ERPNext `Item`, `Item Price`, stock, warehouse, accounting, or Sales Order endpoints directly. Catalog responses expose only:

- `item_code`.
- `item_name`.
- `stock_uom`.
- `disabled`.
- `image`.
- `default_price`.

Order item mutation APIs derive unit price, line total, subtotal, item count, actor, and scope server-side. Flutter sends only order, item, quantity, and optional notes.

Approval actions are also Madar-only. Flutter sends only the order name and the decision reason when required; Madar validates permission, branch scope, current status, and audit comments server-side.

Approved orders may include ERP sync metadata such as `erp_sync_status`, `erp_sync_error`, and `erp_sales_order` in safe order responses. Flutter may display this metadata as read-only context, but it must not expose ERP sync actions. R3-T04 sync helpers are internal service methods only and do not create ERPNext Sales Orders.

R3-T05 keeps ERP sync internal/admin-only. Mobile clients must not receive a sync button or call ERPNext APIs directly. When an approved order is synced server-side, Flutter may display `تمت المزامنة`; when sync fails, Flutter may display `فشل في المزامنة` from safe Madar metadata only.

R3-T06 adds authenticated Madar-only ERP sync review endpoints:

```text
/api/method/madar.api.erp_sync.list_sync_orders
/api/method/madar.api.erp_sync.get_sync_order
/api/method/madar.api.erp_sync.retry_sync_order
/api/method/madar.api.erp_sync.submit_erp_sales_order
/api/method/madar.api.erp_sync.list_invoice_sync_orders
/api/method/madar.api.erp_sync.get_invoice_sync_order
/api/method/madar.api.erp_sync.retry_invoice_sync
```

They require `accounting.view_sync_logs` and expose only safe sync fields: order name, customer name, subtotal, order status, delivery status, ERP sync status, safe ERP sync error, ERP Sales Order reference, Sales Order docstatus, invoice sync status, safe invoice sync error, ERP Sales Invoice reference, approved timestamp, and approver. Retry is allowed only for pending or failed sync rows; synced Sales Order rows return `ORDER_ALREADY_SYNCED`, and already invoiced rows return `SALES_INVOICE_ALREADY_SYNCED`.

R6-T04 allows accounting/admin users to submit a synced ERP Sales Order and create a draft ERP Sales Invoice only after delivery completion. Flutter may call only the Madar review endpoints above. Flutter must not call ERPNext Sales Order or Sales Invoice APIs directly, must not send invoice line/accounting fields, and must not expose a Sales Invoice submit action.

Server-side invoice sync creates ERPNext `Sales Invoice` with `docstatus=0` only. This phase must not submit Sales Invoice, submit Payment Entry, post GL entries, create Delivery Note, move stock, allocate payments, or expose raw ERP exceptions.

R6-T05 adds Madar-only accounting finalization review endpoints:

```text
/api/method/madar.api.accounting_review.list_orders_for_accounting_review
/api/method/madar.api.accounting_review.get_order_accounting_summary
/api/method/madar.api.accounting_review.mark_accounting_reviewed
/api/method/madar.api.accounting_review.mark_accounting_needs_attention
```

These endpoints require authentication and `accounting.view_sync_logs` or `system.full_access`. They expose safe summary fields only: Madar Order totals/status, ERP Sales Order sync/submit metadata, ERP Sales Invoice draft sync metadata, payment totals/status summaries, cashbox review summaries, readiness flags, and stable alert codes. Flutter may mark a Madar order as reviewed or needing attention, but it must not expose buttons for submitting Sales Invoice, submitting Payment Entry, posting GL, creating Delivery Note, or moving stock.

R6-T06 adds final accounting submit endpoints:

```text
/api/method/madar.api.accounting_finalization.get_finalization_status
/api/method/madar.api.accounting_finalization.submit_sales_invoice
/api/method/madar.api.accounting_finalization.submit_payment_entries
/api/method/madar.api.accounting_finalization.finalize_order_accounting
```

`get_finalization_status` requires `accounting.view_sync_logs` or `system.full_access` and is read-only. The submit/finalize endpoints require `accounting.finalize` or `system.full_access`; `accounting.view_sync_logs` alone must not authorize them.

Flutter must show a confirmation dialog before final submit actions because ERPNext may post GL entries when documents are submitted. Flutter must not send ERPNext document fields, allocation details, GL data, Delivery Note data, Stock Entry data, or docstatus values. Madar derives the ERP Sales Invoice and Payment Entry records from the Madar order and linked Madar payments.

## Notification Endpoints

R7-T01 exposes authenticated in-app notification endpoints:

```text
/api/method/madar.api.notifications.list_notifications
/api/method/madar.api.notifications.get_unread_count
/api/method/madar.api.notifications.mark_notification_read
/api/method/madar.api.notifications.mark_all_notifications_read
```

These endpoints return only notifications for the authenticated user. Flutter must not call Frappe `/api/resource/Madar Notification` directly, must not request another user's notifications, and must not treat notifications as authorization. They are display hints only; backend permissions remain the source of truth.

R7-T02 adds safe navigation metadata to notification responses:

- `route_key`.
- `route_params`.
- `action_label`.
- `deep_link_status`.

Route metadata must contain only safe identifiers such as Madar order names, delivery batch names, work order names, cashbox names, or ERP sync entity references. Flutter may use `route_key` to open an implemented Madar screen, but the target screen must still fetch data through Madar APIs so backend permissions and scopes remain authoritative. If the route cannot be opened, Flutter shows the Arabic safe message:

```text
لا يمكن فتح هذا العنصر أو لا تملك صلاحية الوصول
```

Notification endpoint errors also use:

- `NOTIFICATION_NOT_FOUND`.
- `NOTIFICATION_CREATE_FAILED`.
- `RECIPIENT_REQUIRED`.

## Production Mapping Endpoints

R4-T01 exposes Madar-only production mapping endpoints:

```text
/api/method/madar.api.production_mapping.list_production_centers
/api/method/madar.api.production_mapping.list_production_departments
/api/method/madar.api.production_mapping.list_item_department_mappings
/api/method/madar.api.production_mapping.create_or_update_production_center
/api/method/madar.api.production_mapping.create_or_update_production_department
/api/method/madar.api.production_mapping.create_or_update_item_department_mapping
/api/method/madar.api.production_mapping.validate_order_department_mappings
```

Flutter may use these endpoints only through Madar. It must not call ERPNext Item APIs or Frappe `/api/resource` endpoints directly. Product selection continues to use the safe catalog bridge.

Mapping responses expose only production center, production department, item code, item name, and active flags. Validation checks approved Madar orders and returns missing item codes for active mappings. It must not create production work orders, mutate ERPNext, reserve stock, create invoices, create delivery documents, or create payments.

## Production Work Order Endpoints

R4-T02 exposes Madar-only production work order endpoints:

```text
/api/method/madar.api.work_orders.create_work_orders_from_order
/api/method/madar.api.work_orders.list_work_orders
/api/method/madar.api.work_orders.get_work_order
/api/method/madar.api.work_orders.accept_work_order
/api/method/madar.api.work_orders.start_work_order
/api/method/madar.api.work_orders.mark_work_order_ready
/api/method/madar.api.work_orders.mark_work_order_delayed
```

These endpoints create and update Madar operational work orders only. They must not create ERPNext `Work Order`, manufacturing BOM, stock reservation, Delivery Note, Sales Invoice, Payment Entry, payroll, or cashbox records.

Flutter sends only a Madar work order name and, for delay, a reason. Madar derives actor, scope, status transition, timestamps, and audit comments server-side.

Work order mutations also update the parent Madar Order production summary server-side. Order responses may include read-only `production_status` and `production_ready_at` fields for Flutter display. Flutter must treat these fields as derived context and must not send production status values.

## Delivery Dispatch Endpoints

R5-T01 exposes Madar-only delivery readiness and dispatch endpoints:

```text
/api/method/madar.api.delivery.list_dispatch_queue
/api/method/madar.api.delivery.mark_dispatched_to_branch
/api/method/madar.api.delivery.mark_received_at_branch
/api/method/madar.api.delivery.mark_ready_for_customer_pickup
/api/method/madar.api.delivery.mark_customer_picked_up
/api/method/madar.api.delivery.mark_dispatched_to_customer
/api/method/madar.api.delivery.mark_delivered_to_customer
/api/method/madar.api.delivery.mark_failed_delivery
```

Order creation may send `fulfillment_method` and `destination_branch`. `branch_pickup` is the default and primary option. `destination_branch` is required for branch pickup and optional for customer delivery in this phase.

Delivery readiness is derived from production readiness. When `production_status` becomes `ready`, Madar sets `delivery_status=ready_for_dispatch` and `ready_for_dispatch_at` using server time if the field is empty. Flutter displays delivery state and may request valid transitions only through Madar APIs.

These endpoints must not create ERPNext Delivery Notes, stock entries, invoices, payment entries, cashbox records, driver assignments, route plans, or GPS tracking records.

R5-T02 adds Madar-only delivery batch and driver assignment endpoints:

```text
/api/method/madar.api.delivery.create_delivery_batch
/api/method/madar.api.delivery.assign_driver
/api/method/madar.api.delivery.list_delivery_batches
/api/method/madar.api.delivery.get_delivery_batch
/api/method/madar.api.delivery.list_my_delivery_batches
/api/method/madar.api.delivery.mark_batch_picked_up
/api/method/madar.api.delivery.mark_batch_out_for_delivery
/api/method/madar.api.delivery.mark_batch_delivered
/api/method/madar.api.delivery.mark_batch_returned
```

Drivers are assigned to `Madar Delivery Batch`, not directly to individual orders. Batch APIs group ready orders and cascade allowed delivery status changes back to linked Madar orders server-side. Branch transfer batches and customer delivery batches must remain separate, and branch transfer batches cannot mix destination branches.

Flutter may select ready orders, request a batch, assign a driver by user id/email, and let the assigned driver update batch status. Flutter must not send order delivery statuses, create ERPNext delivery documents, move stock, collect payment, create cashbox entries, or call ERPNext Delivery Note APIs.

## Payment Collection Endpoints

R6-T01 exposes Madar-only operational payment endpoints:

```text
/api/method/madar.api.payments.collect_payment
/api/method/madar.api.payments.list_order_payments
/api/method/madar.api.payments.get_payment
```

These endpoints require authentication. `collect_payment` requires `payments.collect`, validates amount and payment method server-side, derives collection scope from the authenticated user, and recalculates `paid_amount`, `remaining_amount`, and `payment_status` on the Madar Order through the payment service.

Flutter may send only `order_name`, `amount`, `payment_method`, optional `reference_no`, and optional notes. Flutter must not send card details, order payment totals, cashbox custody data, ERPNext Payment Entry data, Sales Invoice data, or accounting posting fields.

Branch pickup collection is branch-scoped. Customer delivery collection is limited to orders linked to a delivery batch assigned to the driver. `system.full_access` may collect as admin context.

R6-T01 must not create ERPNext `Payment Entry`, `Sales Invoice`, refunds, terminal transactions, or accounting ledger entries. R6-T02 adds Madar cashbox custody for cash payments only; it still must not create ERPNext accounting documents.

## Cashbox Endpoints

R6-T02 exposes Madar-only operational cashbox endpoints:

```text
/api/method/madar.api.cashbox.get_my_cashbox
/api/method/madar.api.cashbox.list_my_cashbox_entries
/api/method/madar.api.cashbox.submit_my_cashbox
/api/method/madar.api.cashbox.list_cashboxes_for_review
/api/method/madar.api.cashbox.get_cashbox
/api/method/madar.api.cashbox.approve_cashbox
/api/method/madar.api.cashbox.return_cashbox
```

These endpoints require authentication and use permission keys. Flutter may submit only `submitted_cash` for the user's own cashbox and a return reason for review actions. Flutter must not send expected cash, calculated difference, payment links, ERPNext Payment Entry data, Sales Invoice data, or accounting posting fields.

Expected cash is calculated from `Madar Cashbox Entry` records created server-side when a collected `Madar Payment` uses `payment_method=cash`. Non-cash methods must not create cashbox entries. Cashbox records are operational custody records only and must not create ERPNext `Payment Entry`, `Sales Invoice`, GL entries, bank reconciliation records, or refunds.

## Payment ERP Sync Endpoints

R6-T03 exposes accounting/admin review endpoints for Madar Payment ERP sync:

```text
/api/method/madar.api.payment_sync.list_payment_sync_items
/api/method/madar.api.payment_sync.get_payment_sync_item
/api/method/madar.api.payment_sync.retry_payment_sync
```

These endpoints require authentication and `accounting.view_sync_logs` or `system.full_access`. Flutter may list safe sync metadata and request retry for pending/failed Madar Payments. Flutter must not call ERPNext Payment Entry APIs directly and must not send Payment Entry fields, customer account fields, posting accounts, or docstatus.

Server-side sync creates ERPNext `Payment Entry` with `docstatus=0` only. This phase must not submit Payment Entry, create Sales Invoice, post GL entries, perform bank reconciliation, modify cashbox approval status, create refunds, or expose raw ERP exceptions.

## Long-Running Work

Any long-running process must use Frappe background jobs. Mobile endpoints should enqueue the job and return a stable response that lets Flutter track or refresh status.
