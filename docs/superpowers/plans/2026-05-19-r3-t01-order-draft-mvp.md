# R3-T01 Order Draft MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build Madar operational draft orders with scoped listing, status transitions, and Flutter screens without ERPNext Sales Order integration.

**Architecture:** Backend uses a Frappe DocType `Madar Order`, an API layer in `madar/api/orders.py`, and transition/business rules in `madar/services/order_service.py`. Flutter calls only Madar whitelisted APIs and shows simple Arabic RTL screens for list/create/details.

**Tech Stack:** Frappe Python custom app, Python unittest, Flutter Material 3, Dart tests.

---

### Task 1: Backend Order Service and API

**Files:**
- Create: `madar/madar/doctype/madar_order/madar_order.json`
- Create: `madar/madar/doctype/madar_order/madar_order.py`
- Create: `madar/api/orders.py`
- Create: `madar/services/order_service.py`
- Test: `madar/tests/test_order_service.py`
- Test: `madar/tests/test_orders_api.py`

- [x] Write failing Python tests for create/list/get/submit/cancel, permissions, scopes, and invalid transitions.
- [x] Run targeted tests and verify they fail because orders implementation is missing.
- [x] Add the DocType metadata and service implementation using injected frappe modules for tests.
- [x] Add whitelisted authenticated API wrappers that delegate to the service only.
- [x] Run targeted tests and full backend verification.

### Task 2: Flutter Order Flow

**Files:**
- Create: `lib/features/orders/order_models.dart`
- Create: `lib/features/orders/order_list_screen.dart`
- Create: `lib/features/orders/create_order_screen.dart`
- Create: `lib/features/orders/order_detail_screen.dart`
- Modify: `lib/core/api/frappe_api_client.dart`
- Modify: `lib/features/dashboard/dashboard_screen.dart`
- Test: `test/orders_api_client_test.dart`
- Test: `test/order_screens_test.dart`

- [x] Write failing Dart tests for order API parsing and dashboard/list/create/detail navigation.
- [x] Run targeted Flutter tests and verify they fail because order flow is missing.
- [x] Implement minimal models, API client methods, screens, and dashboard navigation.
- [x] Run Flutter tests/analyze/build.

### Task 3: Docs, Deploy, Live Verification

**Files:**
- Modify: `docs/architecture/01-domain-boundaries.md`
- Modify: `docs/architecture/02-permissions.md`
- Modify: `docs/architecture/03-mobile-api-rules.md`

- [x] Document Madar Order as operational-only and explicitly not ERPNext Sales Order.
- [x] Run local full verification.
- [x] Commit, deploy to staging, migrate/restart.
- [x] Live verify branch user can create/list/submit, non-order user is denied, scopes apply, health and attendance still work.
