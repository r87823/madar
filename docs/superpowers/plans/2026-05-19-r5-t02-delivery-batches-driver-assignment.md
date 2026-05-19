# R5-T02 Delivery Batches + Driver Assignment

## Goal

Create Madar delivery batches, assign drivers to batches, let drivers see their assigned batches, and cascade batch lifecycle status to linked orders without ERPNext delivery, stock, payment, cashbox, GPS, or route optimization.

## Backend Steps

1. Add failing tests for batch creation, validation, driver assignment, driver-scoped listing, lifecycle cascades, return behavior, and ERP non-mutation.
2. Add `Madar Delivery Batch` and `Madar Delivery Batch Order` DocTypes.
3. Extend `madar.services.delivery_service` with batch creation, assignment, listing, get, and lifecycle methods.
4. Add `madar.api.delivery_batches` authenticated whitelisted API methods.
5. Keep order delivery transitions centralized in service layer and reuse safe order mutation behavior.
6. Update architecture docs for batch lifecycle and permissions.

## Flutter Steps

1. Add delivery batch models and API methods.
2. Add dispatch queue selection and create-batch action.
3. Add assigned batch list/detail screens with driver actions.
4. Route dashboard `مهام التوصيل` to the batch experience while preserving dispatch queue access.
5. Add tests for batch creation, assigned batch visibility, labels, and action visibility.

## Verification

- `python3 -m unittest discover -s madar/tests`
- `PYTHONPYCACHEPREFIX=/private/tmp/madar_pycache python3 -m compileall -q madar setup.py`
- `git diff --check`
- `flutter analyze`
- `flutter test`
- `flutter build web`

