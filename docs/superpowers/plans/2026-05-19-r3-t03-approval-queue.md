# R3-T03 Submit Order to Approval Queue Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add branch supervisor approval queue for submitted Madar Orders without ERPNext Sales Order, stock, accounting, invoicing, delivery, production, payment, or cashbox integration.

**Architecture:** Existing order APIs remain service-backed. Approval actions are service-layer status transitions using permission keys and branch scopes, with audit comments for every mutation.

**Tech Stack:** Frappe Python custom app, Python unittest, Flutter Material 3, Dart widget/unit tests.

---

### Task 1: Backend Approval Workflow

**Files:**
- Modify: `madar/services/order_service.py`
- Modify: `madar/api/orders.py`
- Modify: `madar/madar/doctype/madar_order/madar_order.json`
- Test: `madar/tests/test_order_approval_service.py`
- Test: `madar/tests/test_orders_api.py`

- [x] Write failing tests for non-empty submit, returned submit, queue scope, approve, return, reject, reasons, permissions, and invalid transitions.
- [x] Run targeted tests and verify they fail before implementation.
- [x] Implement statuses and service transitions.
- [x] Add whitelisted API wrappers that delegate only to service functions.

### Task 2: Flutter Approval Queue

**Files:**
- Modify: `lib/features/orders/order_models.dart`
- Modify: `lib/core/api/frappe_api_client.dart`
- Modify: `lib/features/dashboard/dashboard_screen.dart`
- Modify: `lib/app/madar_app.dart`
- Create: `lib/features/orders/approval_queue_screen.dart`
- Test: `test/order_approval_api_client_test.dart`
- Test: `test/order_approval_screen_test.dart`

- [x] Write failing tests for status labels, approval API paths, dashboard approval navigation, and queue actions.
- [x] Run targeted Flutter tests and verify they fail before implementation.
- [x] Implement approval queue screen and reason dialog.
- [x] Wire dashboard card `اعتماد الطلبات` to approval queue.

### Task 3: Docs, Verification, Deploy

**Files:**
- Modify: `docs/architecture/02-permissions.md`
- Modify: `docs/architecture/03-mobile-api-rules.md`
- Modify: `docs/architecture/01-domain-boundaries.md`

- [x] Document approval statuses, permissions, and no ERPNext Sales Order creation.
- [x] Run backend and Flutter verification.
- [x] Commit, push, deploy to staging, migrate/restart.
- [x] Live verify submit, queue, approve, return, reject, permissions, scopes, item edit rules, health, attendance, and unchanged Sales Order count.
