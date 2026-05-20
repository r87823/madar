# R6-T04 ERP Sales Order Submit + Sales Invoice Draft Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let accounting/admin submit ERP Sales Orders and create draft ERPNext Sales Invoices for completed Madar Orders without invoice submission, Payment Entry submission, GL posting, Delivery Notes, or stock movement.

**Architecture:** Extend the existing `madar.services.erp_sync_service` because it already owns Sales Order ERP boundaries. `Madar Order` stores Sales Order docstatus and invoice sync metadata. API methods stay thin, authenticated, and delegate to the service using `accounting.view_sync_logs`.

**Tech Stack:** Frappe DocTypes, Python unittest, Flutter Material 3 accounting review UI.

---

### Task 1: Backend Service + Metadata

**Files:**
- Modify: `madar/madar/doctype/madar_order/madar_order.json`
- Modify: `madar/services/erp_sync_service.py`
- Create/modify: `madar/tests/test_invoice_erp_sync_service.py`

- [x] Add `erp_sales_order_docstatus`, `erp_sales_invoice`, `erp_invoice_sync_status`, `erp_invoice_sync_error`, `erp_invoice_created_at`.
- [x] Test Sales Order submit idempotency and missing Sales Order errors.
- [x] Test invoice eligibility: approved, ERP Sales Order exists/submitted, delivered/picked up, items/subtotal valid, not already invoiced.
- [x] Test draft Sales Invoice creation and failure tracking.

### Task 2: Backend API

**Files:**
- Modify: `madar/api/erp_sync.py`
- Modify: `madar/tests/test_erp_sync_api.py`

- [x] Add `submit_erp_sales_order`, `list_invoice_sync_orders`, `get_invoice_sync_order`, `retry_invoice_sync`.
- [x] Keep auth required and API layer delegation only.

### Task 3: Flutter Accounting UI

**Files:**
- Modify: `lib/features/accounting/erp_sync_models.dart`
- Modify: `lib/core/api/frappe_api_client.dart`
- Modify: `lib/features/accounting/erp_sync_review_screen.dart`
- Modify: `test/erp_sync_review_screen_test.dart`

- [x] Parse invoice sync fields and Sales Order docstatus.
- [x] Add Sales Order submit action.
- [x] Add invoice sync section/retry action with Arabic labels.

### Task 4: Docs, Verify, Deploy

**Files:**
- Modify: `docs/architecture/01-domain-boundaries.md`
- Modify: `docs/architecture/03-mobile-api-rules.md`

- [x] Document Draft-only Sales Invoice sync and accounting-controlled Sales Order submit.
- [ ] Run Python/Flutter verification, commit, push, deploy, migrate, and live verify.
