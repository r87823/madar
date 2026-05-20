# R6-T06 ERP Final Submit: Sales Invoice + Payment Entry

## Goal

Allow accounting users to submit already prepared ERPNext Sales Invoice and Payment Entry draft documents through Madar, then mark the Madar Order accounting finalization metadata.

## Scope

- Submit existing draft ERPNext Sales Invoice.
- Submit existing draft ERPNext Payment Entries linked to Madar Payments.
- Track finalization metadata and safe errors on Madar records.
- Add Flutter review actions with confirmation.
- Do not create Delivery Notes, Stock Entries, refunds, credit notes, cancellations, or automatic background submit jobs.

## Permission Model

- `accounting.view_sync_logs`: read-only finalization status.
- `accounting.finalize`: submit Sales Invoice, submit Payment Entries, and finalize accounting.
- `system.full_access`: all finalization capabilities.
- `Madar Accountant` receives `accounting.finalize`.
- `Madar Cashier`, branch, driver, and employee roles do not receive `accounting.finalize`.

## Backend Plan

1. Add tests for permission mapping, finalization service behavior, and whitelisted API wrappers.
2. Add finalization metadata fields to `Madar Order` and `Madar Payment`.
3. Implement `madar.services.accounting_finalization_service`.
4. Implement `madar.api.accounting_finalization` as thin authenticated wrappers.
5. Extend accounting review and ERP sync serializers with final docstatus/error fields.

## Flutter Plan

1. Extend API client with finalization endpoints.
2. Extend accounting models with invoice/payment docstatus and finalization fields.
3. Show final submit buttons only for `accounting.finalize` or `system.full_access`.
4. Require confirmation before submit/finalize actions.
5. Keep ERPNext details read-only and route all actions through Madar APIs.

## Verification

- `python3 -m unittest discover -s madar/tests`
- `PYTHONPYCACHEPREFIX=/private/tmp/madar_pycache python3 -m compileall -q madar setup.py`
- `git diff --check`
- `flutter analyze`
- `flutter test`
- `flutter build web`
