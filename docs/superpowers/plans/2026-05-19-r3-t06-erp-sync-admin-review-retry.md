# R3-T06 ERP Sync Admin Review and Retry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add authenticated accounting/admin tools to review ERP sync status and retry pending or failed Madar Order syncs.

**Architecture:** Public API wrappers live in `madar/api/erp_sync.py` and only authenticate/delegate. `erp_sync_service` owns permission checks, safe list/detail serialization, retry state validation, and calls the existing `sync_order_to_erp`. Flutter gets a read-only accounting review screen with retry buttons for pending/failed rows.

**Tech Stack:** Frappe whitelisted methods, Python unittest, Flutter Material 3, Dart widget/API tests.

---

### Task 1: Backend Review and Retry Service

**Files:**
- Modify: `madar/services/erp_sync_service.py`
- Test: `madar/tests/test_erp_sync_service.py`

- [x] Write failing tests for permission denial, listing safe sync fields, detail lookup, retry pending/failed, and rejecting synced retry.
- [x] Run targeted service tests and confirm they fail.
- [x] Implement `list_sync_orders(user)`, `get_sync_order(user, order_name)`, and `retry_sync_order(user, order_name)`.
- [x] Ensure safe fields only and safe errors.

### Task 2: Backend API Wrappers

**Files:**
- Create: `madar/api/erp_sync.py`
- Test: `madar/tests/test_erp_sync_api.py`

- [x] Write failing API wrapper tests for authentication, whitelisting, and service delegation.
- [x] Run targeted API tests and confirm they fail.
- [x] Implement whitelisted authenticated wrappers for `list_sync_orders`, `get_sync_order`, and `retry_sync_order`.

### Task 3: Flutter Accounting Review

**Files:**
- Modify: `lib/core/api/frappe_api_client.dart`
- Modify: `lib/features/dashboard/dashboard_screen.dart`
- Modify: `lib/app/madar_app.dart`
- Create: `lib/features/accounting/erp_sync_review_screen.dart`
- Test: `test/erp_sync_api_client_test.dart`
- Test: `test/erp_sync_review_screen_test.dart`
- Update existing dashboard tests for the new callback.

- [x] Write failing tests for API paths, accounting dashboard navigation, safe status labels, and retry button visibility.
- [x] Run targeted Flutter tests and confirm they fail.
- [x] Implement API client methods and review screen.
- [x] Wire dashboard card `المحاسبة والمزامنة` to the review screen.

### Task 4: Docs, Verification, Deploy

**Files:**
- Modify: `docs/architecture/02-permissions.md`
- Modify: `docs/architecture/03-mobile-api-rules.md`

- [x] Document review/retry permissions, endpoints, and safe fields.
- [x] Run backend verification.
- [x] Run Flutter verification.
- [x] Scan for credentials and unrelated ERP workflow creation.
- [x] Commit, push, deploy, migrate/restart.
- [x] Live verify accountant access, employee denial, retry behavior, synced retry rejection, health, attendance, approval, and no invoice/payment/delivery creation.
