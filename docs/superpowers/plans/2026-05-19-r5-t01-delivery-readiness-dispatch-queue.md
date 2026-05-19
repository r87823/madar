# R5-T01 Delivery Readiness + Branch Pickup Dispatch Queue

## Goal

Add Madar-only delivery readiness and dispatch queue support for branch pickup and direct customer delivery, without ERPNext delivery, stock, invoice, payment, driver assignment, GPS, or cashbox workflows.

## Backend Steps

1. Add failing delivery service tests for default fulfillment, destination branch validation, production readiness, branch pickup transitions, customer delivery transitions, scope checks, and no ERPNext Delivery Note creation.
2. Add delivery fields to `Madar Order`.
3. Extend order create/list/get serialization with fulfillment fields.
4. Add `madar/services/delivery_service.py` with permission/scope checks and service-layer transitions.
5. Add `madar/api/delivery.py` whitelisted authenticated endpoints that only delegate to the service.
6. Call delivery readiness from production aggregation when `production_status` changes.
7. Update docs for delivery API and domain boundaries.

## Flutter Steps

1. Add fulfillment and delivery status models/labels to `MadarOrder`.
2. Update order creation with branch pickup default and customer delivery option.
3. Show fulfillment, destination branch, and delivery status in order details.
4. Add dispatch queue screen under the existing `مهام التوصيل` dashboard card.
5. Add tests for default UI, required branch behavior, queue display, and action visibility.

## Verification

- `python3 -m unittest discover -s madar/tests`
- `PYTHONPYCACHEPREFIX=/private/tmp/madar_pycache python3 -m compileall -q madar setup.py`
- `git diff --check`
- `flutter analyze`
- `flutter test`
- `flutter build web`

