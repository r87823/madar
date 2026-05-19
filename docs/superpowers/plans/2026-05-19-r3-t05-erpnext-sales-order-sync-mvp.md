# R3-T05 ERPNext Sales Order Sync MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the first internal one-way sync from approved Madar Orders to draft ERPNext Sales Orders.

**Architecture:** `erp_sync_service` remains the only sync boundary. It validates an approved Madar Order, prepares the existing safe payload, creates a draft ERPNext Sales Order through Frappe DocType APIs, and writes sync metadata back to Madar Order. Flutter receives read-only status labels only and never calls ERPNext APIs.

**Tech Stack:** Frappe DocTypes, Python unittest, Flutter Material 3, Dart tests.

---

### Task 1: ERP Sync Flow Service

**Files:**
- Modify: `madar/services/erp_sync_service.py`
- Test: `madar/tests/test_erp_sync_service.py`

- [x] Write failing tests for `sync_order_to_erp`, `create_sales_order`, `map_madar_order_to_sales_order`, failure tracking, and already-synced rejection.
- [x] Run targeted sync tests and confirm they fail.
- [x] Implement minimal draft Sales Order creation through `frappe.get_doc(...).insert(ignore_permissions=True)`.
- [x] Save `erp_sales_order` and `erp_sync_status=synced` on success.
- [x] Save `erp_sync_status=failed` and a safe `erp_sync_error` when ERP creation fails.

### Task 2: Flutter Read-Only Sync Labels

**Files:**
- Modify: `lib/features/orders/order_models.dart`
- Modify: `lib/features/orders/order_list_screen.dart`
- Test: `test/order_approval_api_client_test.dart`
- Test: `test/order_screens_test.dart`

- [x] Write failing tests for synced and failed display labels.
- [x] Run targeted Flutter tests and confirm they fail.
- [x] Add a `displayStatusLabel` getter that accounts for ERP sync metadata.
- [x] Use the getter in order list/detail screens without adding sync actions.

### Task 3: Docs and Verification

**Files:**
- Modify: `docs/architecture/01-domain-boundaries.md`
- Modify: `docs/architecture/03-mobile-api-rules.md`

- [x] Document one-way internal sync lifecycle and that created Sales Orders are draft ERP representations.
- [x] Run backend verification.
- [x] Run Flutter verification.
- [x] Scan for credentials and accidental public ERP API exposure.
- [x] Commit, push, deploy, migrate/restart.
- [x] Live verify Sales Order count increases by one on sync, metadata is saved, failure is tracked, health/attendance/approval still work.
