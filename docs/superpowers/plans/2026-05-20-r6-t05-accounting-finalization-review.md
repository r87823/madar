# R6-T05 Accounting Finalization Review Implementation Plan

**Goal:** Add Madar-only accounting finalization review summaries for orders without submitting ERP Sales Invoices, submitting Payment Entries, posting GL, creating Delivery Notes, or moving stock.

**Architecture:** `madar.services.accounting_review_service` owns read-only aggregation and Madar-only review status changes. `madar.api.accounting_review` remains a thin authenticated wrapper. Flutter extends the existing accounting review screen with a “مراجعة الإقفال” section.

## Backend

- [x] Add Madar Order fields: `accounting_status`, `accounting_review_notes`, `accounting_reviewed_by`, `accounting_reviewed_at`.
- [x] Create `accounting_review_service` with safe summaries for order, ERP Sales Order, ERP Sales Invoice, payments, cashbox, readiness flags, and alerts.
- [x] Create authenticated whitelisted APIs: list, get, mark reviewed, mark needs attention.
- [x] Keep all ERP behavior read-only and avoid Sales Invoice submit, Payment Entry submit, GL posting, Delivery Note, or stock movement.

## Flutter

- [x] Add accounting review models and API client methods.
- [x] Extend the accounting/sync screen with “مراجعة الإقفال”.
- [x] Show safe summary cards for الطلب، أمر البيع، الفاتورة، المدفوعات، الصندوق، والتنبيهات.
- [x] Add Madar-only actions: “تمّت المراجعة” and “يحتاج مراجعة / ملاحظة”.

## Verification

- [ ] Run backend tests, compileall, and diff check.
- [ ] Run Flutter analyze, test, and web build.
- [ ] Deploy to staging and verify no ERP final submit or GL posting occurs.
