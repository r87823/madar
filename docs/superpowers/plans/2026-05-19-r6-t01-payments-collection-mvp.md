# R6-T01 Payments Collection MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Madar operational payment collection with partial/full status tracking, scoped collection, and Flutter payment UI without ERPNext Payment Entry, invoice, or cashbox creation.

**Architecture:** Madar records payments in its own `Madar Payment` DocType and recalculates order payment summary fields through `madar.services.payment_service`. APIs are whitelisted wrappers that authenticate and delegate to the service. Flutter calls only Madar APIs and displays/collects safe operational payment data.

**Tech Stack:** Frappe DocTypes and whitelisted Python APIs, Python unittest service fakes, Flutter Material 3 RTL screens/widgets, existing `FrappeApiClient` envelope parsing.

---

### Task 1: Backend Payment Service TDD

**Files:**
- Create: `madar/services/payment_service.py`
- Modify: `madar/tests/test_payment_service.py`
- Modify: `madar/madar/doctype/madar_order/madar_order.json`

- [ ] Write failing tests for valid partial/full collection, overpayment rejection, invalid methods, unpaid/partially_paid/paid recalculation, branch scope, driver assigned-batch scope, no ERP Payment Entry/Sales Invoice/cashbox creation.
- [ ] Run `python3 -m unittest madar.tests.test_payment_service` and confirm failures are due to missing service.
- [ ] Implement minimal service methods: `collect_payment`, `list_order_payments`, `get_payment`, payment/order serializers, scope checks, and order summary recalculation.
- [ ] Run `python3 -m unittest madar.tests.test_payment_service` and make it pass.

### Task 2: Frappe DocType and API

**Files:**
- Create: `madar/madar/doctype/madar_payment/__init__.py`
- Create: `madar/madar/doctype/madar_payment/madar_payment.py`
- Create: `madar/madar/doctype/madar_payment/madar_payment.json`
- Create: `madar/api/payments.py`
- Modify: `madar/tests/test_payment_api.py`

- [ ] Write API delegation/auth tests for `collect_payment`, `list_order_payments`, and `get_payment`.
- [ ] Add `Madar Payment` DocType JSON and whitelisted API wrappers.
- [ ] Run backend test suite.

### Task 3: Flutter Payment Models and Order Detail UI

**Files:**
- Create: `lib/features/payments/payment_models.dart`
- Create: `lib/features/payments/payment_section.dart`
- Modify: `lib/core/api/frappe_api_client.dart`
- Modify: `lib/features/orders/order_models.dart`
- Modify: `lib/features/orders/order_detail_screen.dart`
- Modify: Flutter tests under `test/`

- [ ] Write widget/model tests for payment status labels, order detail summary, payment history, and collect form visibility for `payments.collect`.
- [ ] Add API methods and UI section using Arabic RTL labels.
- [ ] Run `flutter test` and `flutter analyze`.

### Task 4: Driver Batch Detail Payment Entry Point

**Files:**
- Modify: `lib/features/delivery/delivery_batch_list_screen.dart`
- Modify: `test/delivery_batch_screen_test.dart`

- [ ] Write failing test that batch detail shows collect payment action per linked order.
- [ ] Reuse the same `PaymentSection` or compact payment action in batch detail.
- [ ] Run Flutter tests.

### Task 5: Docs, Verification, Deployment

**Files:**
- Modify: `docs/architecture/01-domain-boundaries.md`
- Modify: `docs/architecture/03-mobile-api-rules.md`

- [ ] Document operational payments and explicit ERP/cashbox boundary.
- [ ] Run `python3 -m unittest discover -s madar/tests`.
- [ ] Run `PYTHONPYCACHEPREFIX=/private/tmp/madar_pycache python3 -m compileall -q madar setup.py`.
- [ ] Run `git diff --check`, `flutter analyze`, `flutter test`, and `flutter build web`.
- [ ] Commit, push, deploy to `hrms.localhost`, migrate, restart, and verify no ERPNext Payment Entry/Sales Invoice/cashbox records are created.
