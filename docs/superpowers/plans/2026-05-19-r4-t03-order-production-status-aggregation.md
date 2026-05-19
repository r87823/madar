# R4-T03 Order Production Status Aggregation

## Goal

Aggregate `Madar Work Order` statuses into read-only production status fields on the parent `Madar Order`, and expose the result in Flutter order details.

## Scope

- Add `production_status` and `production_ready_at` to `Madar Order`.
- Recalculate parent production status after work order creation and every work order transition.
- Keep aggregation inside the production service layer.
- Display production status in Flutter order details.
- Do not add delivery, payments, cashbox, ERPNext Work Orders, stock, BOM, or manufacturing integration.

## Backend Steps

1. Add failing tests for aggregation rules and timestamp idempotency.
2. Add DocType fields on `Madar Order`.
3. Include production fields in order serialization.
4. Add a `recalculate_order_production_status` helper in `work_order_service`.
5. Call aggregation after work order creation and transitions.
6. Update production architecture docs.

## Flutter Steps

1. Add production status parsing and Arabic labels to `MadarOrder`.
2. Add a production status row to order detail.
3. Add widget/model tests for the new display behavior.

## Verification

- `python3 -m unittest discover -s madar/tests`
- `PYTHONPYCACHEPREFIX=/private/tmp/madar_pycache python3 -m compileall -q madar setup.py`
- `git diff --check`
- `flutter analyze`
- `flutter test`
- `flutter build web`

