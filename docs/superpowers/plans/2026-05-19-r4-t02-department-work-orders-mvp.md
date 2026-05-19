# R4-T02 Department Work Orders MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create Madar operational work orders grouped by production center and department from approved mapped Madar Orders.

**Architecture:** Add `Madar Work Order` and `Madar Work Order Item` DocTypes. Keep creation, idempotency, department grouping, scoped reads, and lifecycle transitions inside `madar.services.work_order_service`; API wrappers authenticate and delegate only. Flutter adds an Arabic RTL work order list/detail flow behind the existing `أوامر الإنتاج` dashboard card.

**Tech Stack:** Frappe DocTypes and whitelisted methods, Python unittest with fake Frappe modules, Flutter Material 3, Dart API/widget tests.

---

### Task 1: Backend Work Order Service

**Files:**
- Create: `madar/services/work_order_service.py`
- Test: `madar/tests/test_work_order_service.py`

- [x] Write failing tests for approved-order creation, department grouping, idempotency, missing mapping blocking, permission denial, scoped list/get, lifecycle transitions, delay reason, and branch-user update denial.
- [x] Run targeted tests and confirm they fail.
- [x] Implement minimal service methods with safe envelopes and audit comments.
- [x] Run targeted tests and confirm they pass.

### Task 2: DocTypes and API Wrappers

**Files:**
- Create: `madar/madar/doctype/madar_work_order/*`
- Create: `madar/madar/doctype/madar_work_order_item/*`
- Create: `madar/api/work_orders.py`
- Test: `madar/tests/test_work_orders_api.py`

- [x] Write failing tests for authenticated whitelisted methods and service delegation.
- [x] Run targeted tests and confirm they fail.
- [x] Add DocType JSON/controllers and whitelisted API wrappers.
- [x] Run targeted tests and confirm they pass.

### Task 3: Flutter Work Orders

**Files:**
- Modify: `lib/core/api/frappe_api_client.dart`
- Modify: `lib/features/dashboard/dashboard_screen.dart`
- Modify: `lib/app/madar_app.dart`
- Create: `lib/features/production/work_order_models.dart`
- Create: `lib/features/production/work_order_list_screen.dart`
- Create: `lib/features/production/work_order_detail_screen.dart`
- Test: `test/work_orders_api_client_test.dart`
- Test: `test/work_orders_screen_test.dart`

- [x] Write failing tests for Madar-only API paths, dashboard navigation, list/detail rendering, status labels, and lifecycle action calls.
- [x] Run targeted Flutter tests and confirm they fail.
- [x] Implement API methods, models, and Arabic RTL list/detail screens.
- [x] Run targeted Flutter tests and confirm they pass.

### Task 4: Docs, Verification, Deployment

**Files:**
- Modify: `docs/architecture/02-permissions.md`
- Modify: `docs/architecture/03-mobile-api-rules.md`
- Modify: `docs/architecture/05-production-services.md`

- [x] Document work order permissions, endpoints, lifecycle, grouping, idempotency, and no-ERPNext-work-order boundary.
- [x] Run backend verification: `python3 -m unittest discover -s madar/tests`, compileall, `git diff --check`.
- [x] Run Flutter verification: `flutter analyze`, `flutter test`, `flutter build web`.
- [x] Deploy to staging, migrate/restart, and live verify admin creation, repeated create idempotency, missing mapping blocking, production-user list/get/update, delay reason requirement, branch-user update denial, no ERPNext Work Order creation, and existing health/attendance/order/ERP sync flows.
