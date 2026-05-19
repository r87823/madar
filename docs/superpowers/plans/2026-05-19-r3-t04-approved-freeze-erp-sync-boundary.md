# R3-T04 Approved Freeze and ERP Sync Boundary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Freeze approved Madar operational orders and add an isolated ERP sync boundary that prepares safe Sales Order payloads without creating ERPNext documents.

**Architecture:** Approval remains in `order_service`; approved orders receive immutable sync metadata and stay operational-only. A new `erp_sync_service` owns validation, payload preparation, and sync result markers, with no API route and no ERPNext Sales Order insertion.

**Tech Stack:** Frappe custom app DocTypes, Python unittest, Flutter Material 3, Dart widget/unit tests.

---

### Task 1: Backend Freeze Metadata

**Files:**
- Modify: `madar/madar/doctype/madar_order/madar_order.json`
- Modify: `madar/services/order_service.py`
- Test: `madar/tests/test_order_approval_service.py`

- [x] Write failing tests that approval sets `approved_at`, `approved_by`, and `erp_sync_status=pending`.
- [x] Run targeted approval tests and confirm the new tests fail.
- [x] Add DocType fields for `approved_by`, `erp_sync_status`, `erp_sync_error`, and `erp_sales_order`.
- [x] Update approval serialization and transition logic.
- [x] Run targeted approval tests and confirm they pass.

### Task 2: ERP Sync Boundary Service

**Files:**
- Create: `madar/services/erp_sync_service.py`
- Test: `madar/tests/test_erp_sync_service.py`
- Modify: `docs/architecture/01-domain-boundaries.md`
- Modify: `docs/architecture/03-mobile-api-rules.md`

- [x] Write failing tests for approved-order validation, already-synced rejection, empty-item rejection, safe payload shape, failed marker, and success marker.
- [x] Run sync service tests and confirm they fail because the service does not exist yet.
- [x] Implement `prepare_sales_order_payload(order_name)`, `validate_order_ready_for_sync(order_name)`, `mark_sync_failed(order_name, error)`, and `mark_sync_success(order_name, sales_order_name)`.
- [x] Ensure the service never creates `Sales Order` documents and only reads Madar Order/Items.
- [x] Document the operational-to-ERP boundary and the absence of mobile sync actions.

### Task 3: Flutter Read-Only Approved State

**Files:**
- Modify: `lib/features/orders/order_models.dart`
- Modify: `lib/features/orders/order_detail_screen.dart`
- Test: `test/order_approval_api_client_test.dart`
- Test: `test/order_screens_test.dart`

- [x] Write failing Flutter tests for approved label `معتمد - جاهز للمزامنة` and read-only approved detail screen copy.
- [x] Run targeted Flutter tests and confirm they fail.
- [x] Add sync metadata fields to `MadarOrder` and update the approved Arabic label.
- [x] Show a small read-only sync readiness row on approved orders without adding sync actions.
- [x] Run targeted Flutter tests and confirm they pass.

### Task 4: Verification and Deployment

- [x] Run backend verification: `python3 -m unittest discover -s madar/tests`, compileall, and `git diff --check`.
- [x] Run Flutter verification: `flutter analyze`, `flutter test`, and `flutter build web`.
- [x] Security scan for credentials and forbidden ERPNext Sales Order insertion.
- [x] Commit, push, deploy to staging, migrate/restart.
- [x] Live verify approved order freeze, approval metadata, payload preparation, unchanged Sales Order count, health, attendance, and existing approval flow.
