# R4-T01 Production Department Mapping Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the production master-data foundation that maps catalog items to Madar production departments and validates approved orders before future work order creation.

**Architecture:** Add three Frappe DocTypes for centers, departments, and item mappings. Keep all behavior in `madar.services.production_mapping_service`; whitelisted API wrappers authenticate and delegate only. Flutter adds a permission-gated Arabic production settings screen that uses Madar APIs and the existing catalog bridge.

**Tech Stack:** Frappe DocTypes and whitelisted methods, Python unittest with injectable fake Frappe modules, Flutter Material 3, Dart API/widget tests.

---

### Task 1: Backend Permissions and Service

**Files:**
- Modify: `madar/permissions/registry.py`
- Create: `madar/services/production_mapping_service.py`
- Test: `madar/tests/test_production_mapping_service.py`

- [x] Write failing tests for `production.manage_mappings`, view/manage permission behavior, idempotent item mapping, inactive mapping treated as missing, and approved order validation.
- [x] Run targeted tests and confirm they fail.
- [x] Implement the permission key and production mapping service with safe response envelopes.
- [x] Run targeted tests and confirm they pass.

### Task 2: DocTypes and API Wrappers

**Files:**
- Create: `madar/madar/doctype/madar_production_center/*`
- Create: `madar/madar/doctype/madar_production_department/*`
- Create: `madar/madar/doctype/madar_item_department_mapping/*`
- Create: `madar/api/production_mapping.py`
- Test: `madar/tests/test_production_mapping_api.py`

- [x] Write failing API tests for authentication, whitelisting, and delegation.
- [x] Run targeted API tests and confirm they fail.
- [x] Add DocType JSON/controllers and authenticated API wrappers.
- [x] Run targeted tests and confirm they pass.

### Task 3: Flutter Production Mapping Screen

**Files:**
- Modify: `lib/core/api/frappe_api_client.dart`
- Modify: `lib/core/permissions/dashboard_cards.dart`
- Modify: `lib/features/dashboard/dashboard_screen.dart`
- Modify: `lib/app/madar_app.dart`
- Create: `lib/features/production/production_mapping_models.dart`
- Create: `lib/features/production/production_mapping_screen.dart`
- Test: `test/production_mapping_api_client_test.dart`
- Test: `test/production_mapping_screen_test.dart`

- [x] Write failing tests for Madar-only endpoints, dashboard visibility/navigation, list rendering, and save action.
- [x] Run targeted Flutter tests and confirm they fail.
- [x] Implement models, API methods, dashboard route, and the Arabic RTL mapping screen.
- [x] Run targeted Flutter tests and confirm they pass.

### Task 4: Docs, Verification, Deployment

**Files:**
- Modify: `docs/architecture/02-permissions.md`
- Modify: `docs/architecture/03-mobile-api-rules.md`
- Create/modify: `docs/architecture/05-production-services.md`

- [x] Document permissions, endpoints, safe fields, and the no-work-order boundary.
- [x] Run backend verification: `python3 -m unittest discover -s madar/tests`, compileall, `git diff --check`.
- [x] Run Flutter verification: `flutter analyze`, `flutter test`, `flutter build web`.
- [x] Deploy to staging, migrate/restart, and live verify center/department creation, item mapping, validation success/missing mapping, branch-user denial, production-user department viewing, and existing health/attendance/order/ERP sync flows.
