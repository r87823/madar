# Detailed Reports

R8-T02 adds read-only detailed operational reports with safe filters, pagination, and permission-aware visibility. Reports are Arabic-first in Flutter under `التقارير`.

## Boundary

Reports are read-only. They must not create, update, submit, cancel, or delete Madar records or ERPNext records. They must not create ERPNext Delivery Notes, Stock Entries, Sales Invoices, Payment Entries, GL Entries, or export files.

Flutter calls only Madar whitelisted methods under:

```text
/api/method/madar.api.reports.*
```

Flutter must not call ERPNext report APIs, Frappe `/api/resource`, or ERPNext DocTypes directly.

## APIs

R8-T02 exposes:

```text
/api/method/madar.api.reports.get_orders_report
/api/method/madar.api.reports.get_payments_report
/api/method/madar.api.reports.get_production_report
/api/method/madar.api.reports.get_delivery_report
/api/method/madar.api.reports.get_cashbox_report
/api/method/madar.api.reports.get_erp_sync_errors_report
```

All endpoints require authentication and do not use `allow_guest=True`.

## Response Shape

Each report returns:

```json
{
  "ok": true,
  "data": {
    "items": [],
    "total": 0,
    "page": 1,
    "page_size": 20,
    "filters": {},
    "summary": {
      "total_amount": 0,
      "count": 0
    }
  },
  "error": null
}
```

`page_size` is capped server-side. If no dates are supplied, reports use a safe default recent date range.

## Reports

`تقرير الطلبات` exposes safe order columns only: order name, customer name, branch, destination branch, order status, production status, delivery status, payment status, subtotal, paid amount, remaining amount, and created date.

`تقرير المدفوعات` exposes safe payment columns only: payment name, Madar order, amount, payment method, payment status, collection context, collected by user, collected timestamp, ERP sync status, and ERP Payment Entry reference.

`تقرير الإنتاج` exposes safe work order columns only: work order name, Madar order, production center, production department, status, lifecycle timestamps, and delay reason.

`تقرير التوصيل` exposes safe delivery batch columns only: batch name, batch type, driver user, destination branch, status, and lifecycle timestamps.

`تقرير الصناديق` exposes safe cashbox columns only: cashbox name, user, date, status, expected cash, submitted cash, difference, submitted timestamp, reviewer, and reviewed timestamp.

`تقرير أخطاء ERP` aggregates failures from Madar Order Sales Order sync, Madar Order Sales Invoice sync, and Madar Payment sync. It exposes entity type, entity name, sync status, safe error, ERP reference, and updated timestamp. Raw tracebacks and secrets must be removed.

## Permissions And Scope

Report access uses Madar permission keys and scope helpers. No protected report uses direct role checks.

- Orders report: `orders.create`, `orders.approve`, or `system.full_access`.
- Payments report: `payments.collect`, `accounting.view_sync_logs`, or `system.full_access`.
- Production report: `production.view_work_orders` or `system.full_access`.
- Delivery report: `delivery.view_assigned_batches`, `delivery.update_batch`, or `system.full_access`.
- Cashbox report: `cashbox.view_own`, `cashbox.review`, `accounting.view_sync_logs`, or `system.full_access`.
- ERP sync errors report: `accounting.view_sync_logs` or `system.full_access`.

Branch-scoped users only see scoped branch order data where branch context exists. Production users only see department-scoped work orders where department context exists. Drivers only see assigned delivery batches. Non-accounting payment collectors only see their own collected payments. Cashbox owners see their own cashboxes unless they also have review/accounting permission. Accounting users may see accounting-wide payment, cashbox, and ERP sync report data.

## Flutter

The `التقارير` screen provides a simple report menu, text filters, summary count/amount, and paginated metadata. It must not expose export buttons, charting controls, ERP submit actions, or any mutation action.
