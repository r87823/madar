# R3-T02 Order Line Items + Product Catalog Bridge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Madar-owned order line items and a safe backend product catalog bridge while keeping ERPNext Sales Order, stock, accounting, invoicing, delivery, production, and payments out of scope.

**Architecture:** Flutter calls only Madar whitelisted methods. Madar catalog APIs expose a safe Item projection, and Madar order item APIs mutate only scoped draft orders through service-layer functions that recalculate totals.

**Tech Stack:** Frappe Python custom app, Frappe DocTypes, Python unittest, Flutter Material 3, Dart widget/unit tests.

---

### Task 1: Backend Catalog Bridge

**Files:**
- Create: `madar/services/catalog_service.py`
- Create: `madar/api/catalog.py`
- Test: `madar/tests/test_catalog_service.py`
- Test: `madar/tests/test_catalog_api.py`

- [x] Write failing tests for safe product listing, search, limit, optional default price, and authenticated API delegation.
- [x] Run targeted tests and verify they fail because catalog files do not exist.
- [x] Implement `list_products` using safe Item fields only and optional Item Price lookup.
- [x] Add whitelisted authenticated API wrapper.

### Task 2: Backend Order Items

**Files:**
- Create: `madar/madar/doctype/madar_order_item/madar_order_item.json`
- Create: `madar/madar/doctype/madar_order_item/madar_order_item.py`
- Create: `madar/services/order_item_service.py`
- Create: `madar/api/order_items.py`
- Modify: `madar/madar/doctype/madar_order/madar_order.json`
- Modify: `madar/services/order_service.py`
- Test: `madar/tests/test_order_item_service.py`
- Test: `madar/tests/test_order_items_api.py`

- [x] Write failing tests for add/update/remove/list, totals recalculation, scope enforcement, permission denial, invalid quantity, and submitted/cancelled edit rejection.
- [x] Run targeted tests and verify they fail because item service/API/DocType are missing.
- [x] Add `Madar Order Item` DocType and `subtotal`/`items_count` fields on `Madar Order`.
- [x] Implement item mutations through service functions only and audit comments on the parent order.
- [x] Run targeted backend tests.

### Task 3: Flutter Order Items UX

**Files:**
- Create: `lib/features/orders/items/product_models.dart`
- Create: `lib/features/orders/items/order_item_models.dart`
- Create: `lib/features/orders/items/product_picker_sheet.dart`
- Create: `lib/features/orders/items/order_items_section.dart`
- Modify: `lib/core/api/frappe_api_client.dart`
- Modify: `lib/features/orders/order_models.dart`
- Modify: `lib/features/orders/order_detail_screen.dart`
- Test: `test/order_items_api_client_test.dart`
- Test: `test/order_items_screen_test.dart`

- [x] Write failing Dart tests for product parsing, order item parsing, Madar-only API paths, and detail screen item/totals display.
- [x] Run targeted Flutter tests and verify they fail because item models/UI are missing.
- [x] Implement API client methods and simple Arabic RTL item widgets.
- [x] Wire detail screen to add/search/update/remove items and display subtotal/items count.

### Task 4: Docs, Verification, Deploy

**Files:**
- Modify: `docs/architecture/01-domain-boundaries.md`
- Modify: `docs/architecture/02-permissions.md`
- Modify: `docs/architecture/03-mobile-api-rules.md`

- [x] Document catalog bridge and line-item boundaries.
- [x] Run backend and Flutter verification.
- [x] Commit, push, deploy to staging, migrate/restart.
- [x] Live verify branch user product browse, add/update/remove item, totals, submitted edit rejection, scope enforcement, attendance health, and no ERPNext Sales Order creation.
