# R6-T02 Cashbox Daily Custody Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Madar-owned daily cashbox custody for cash payments, including submission and review, without ERPNext Payment Entry, Sales Invoice, GL, refunds, or bank reconciliation.

**Architecture:** Cash payment collection will call a cashbox service hook that creates/finds the owner's daily open/returned cashbox and inserts a linked cashbox entry. Expected cash is calculated from entries, never trusted as editable state. Cashbox APIs authenticate and delegate to service methods that enforce owner/reviewer permissions.

**Tech Stack:** Frappe DocTypes and whitelisted methods, Python unittest with Frappe fakes, existing Madar permission registry, Flutter Material 3 RTL widgets and existing API envelope parsing.

---

### Task 1: Backend Cashbox Service TDD

**Files:**
- Create: `madar/services/cashbox_service.py`
- Modify: `madar/services/payment_service.py`
- Create: `madar/tests/test_cashbox_service.py`
- Modify: `madar/tests/test_payment_service.py`

- [ ] Write failing tests for cash payment entry creation, non-cash skip, unique user/date cashbox, calculated expected cash, submit difference, own access, reviewer approve/return, returned resubmit, approved immutability, and no ERP documents.
- [ ] Run `python3 -m unittest madar.tests.test_cashbox_service madar.tests.test_payment_service` and confirm missing service/hook failures.
- [ ] Implement minimal service and payment hook.
- [ ] Re-run the focused tests until green.

### Task 2: DocTypes, Permissions, and API

**Files:**
- Create: `madar/madar/doctype/madar_cashbox/*`
- Create: `madar/madar/doctype/madar_cashbox_entry/*`
- Create: `madar/api/cashbox.py`
- Modify: `madar/permissions/registry.py`
- Modify: `madar/tests/test_cashbox_api.py`
- Modify: `madar/tests/test_permissions.py`

- [ ] Add `cashbox.review` and map it to Madar Cashier and Madar Accountant.
- [ ] Add DocTypes and API wrappers.
- [ ] Test API delegates with session user and rejects Guest.

### Task 3: Flutter Cashbox UI

**Files:**
- Create: `lib/features/cashbox/cashbox_models.dart`
- Create: `lib/features/cashbox/cashbox_screen.dart`
- Modify: `lib/core/api/frappe_api_client.dart`
- Modify: `lib/core/permissions/dashboard_cards.dart`
- Modify: `lib/features/dashboard/dashboard_screen.dart`
- Modify: `lib/app/madar_app.dart`
- Create/modify Flutter tests under `test/`

- [ ] Add models/API methods.
- [ ] Dashboard card `الصندوق` opens my cashbox screen.
- [ ] My cashbox screen shows summary, entries, submit form.
- [ ] Reviewer permissions show review list/actions.

### Task 4: Docs, Verification, Deploy

**Files:**
- Modify: `docs/architecture/01-domain-boundaries.md`
- Modify: `docs/architecture/03-mobile-api-rules.md`
- Modify: `docs/architecture/02-permissions.md`

- [ ] Document cash custody boundary and APIs.
- [ ] Run backend and Flutter verification.
- [ ] Commit, push, deploy, migrate, restart.
- [ ] Live verify cash payments create entries, non-cash skips, submit/approve/return works, and ERP Payment Entry/Sales Invoice counts remain unchanged.
