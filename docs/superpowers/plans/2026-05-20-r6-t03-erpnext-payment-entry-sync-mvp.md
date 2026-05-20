# R6-T03 ERPNext Payment Entry Sync MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Sync collected Madar Payments to draft ERPNext Payment Entry records without submitting accounting documents or creating Sales Invoices.

**Architecture:** `Madar Payment` remains the operational source and stores ERP sync metadata. A dedicated `payment_erp_sync_service` validates readiness, prepares a safe Payment Entry payload, creates only draft ERPNext Payment Entry documents, and records success/failure. API wrappers require authentication and delegate to the service using permission keys.

**Tech Stack:** Frappe DocTypes, Python service/API tests, Flutter Material 3 Arabic UI, existing `FrappeApiClient`.

---

### Task 1: Backend Payment Sync Service

**Files:**
- Modify: `madar/madar/doctype/madar_payment/madar_payment.json`
- Create: `madar/services/payment_erp_sync_service.py`
- Create: `madar/tests/test_payment_erp_sync_service.py`
- Modify: `madar/services/payment_service.py`

- [ ] Add `erp_sync_status`, `erp_sync_error`, and `erp_payment_entry` fields to `Madar Payment`.
- [ ] Write failing tests for pending default, readiness validation, payload preparation, draft Payment Entry creation, success/failure metadata, already synced rejection, missing ERP Sales Order rejection, and no Sales Invoice creation.
- [ ] Implement service methods: `validate_payment_ready_for_sync`, `prepare_payment_entry_payload`, `create_payment_entry`, `sync_payment_to_erp`, `mark_payment_sync_success`, `mark_payment_sync_failed`.
- [ ] Set new payments to `erp_sync_status=pending`.

### Task 2: Backend API

**Files:**
- Create: `madar/api/payment_sync.py`
- Create: `madar/tests/test_payment_sync_api.py`

- [ ] Add authenticated whitelisted methods: `list_payment_sync_items`, `get_payment_sync_item`, `retry_payment_sync`.
- [ ] Require `accounting.view_sync_logs` or `system.full_access` inside the service layer.
- [ ] Return safe fields only and stable error codes.

### Task 3: Flutter Accounting Review Extension

**Files:**
- Create: `lib/features/accounting/payment_sync_models.dart`
- Modify: `lib/core/api/frappe_api_client.dart`
- Modify: `lib/features/accounting/erp_sync_review_screen.dart`
- Add/modify tests under `test/`.

- [ ] Add API methods for payment sync list/get/retry.
- [ ] Show payment sync items alongside existing ERP order sync review.
- [ ] Add retry button for pending/failed payments and Arabic status/method labels.

### Task 4: Docs, Verification, Deploy

**Files:**
- Modify: `docs/architecture/01-domain-boundaries.md`
- Modify: `docs/architecture/03-mobile-api-rules.md`

- [ ] Document that Payment Entry sync creates draft records only and no Sales Invoice/GL posting.
- [ ] Run backend and Flutter verification.
- [ ] Commit, push, deploy to staging, migrate/restart, and live-verify draft Payment Entry creation and safety boundaries.
