# Madar Staging Cleanup

This checklist is for staging only. Do not delete existing business documents
as part of R10-T01.

## Credentials

- Keep SSH credentials outside the repository.
- Do not commit `.env` files, shell history, scripts with passwords, API keys,
  ERP credentials, or payment gateway credentials.
- Rotate any credential that was ever pasted into an unsafe location.
- Use local protected environment files only for temporary deployment secrets.

## Dev User Bootstrap

Development users are opt-in only.

Enable only on staging/dev with one of:

- `MADAR_ENABLE_DEV_BOOTSTRAP=1`
- legacy compatibility: `MADAR_ENABLE_DEV_USER_BOOTSTRAP=1`
- site config: `enable_madar_dev_user_bootstrap`

The bootstrap password must come from:

- `MADAR_DEV_USER_PASSWORD`, or
- protected site config `madar_dev_user_password`.

Never commit dev user passwords. Never enable dev bootstrap on production.

## Data Cleanup Rules

Allowed during staging cleanup:

- Disable dev bootstrap after users are created.
- Review test users and confirm they are clearly development users.
- Review settings and restore safe defaults where needed.
- Review failed sync rows and leave them for accounting diagnosis.

Not allowed during this task:

- Deleting business documents.
- Deleting ERPNext documents.
- Submitting Sales Invoices or Payment Entries.
- Creating Delivery Notes or Stock Entries.
- Resetting accounting data.

## Staging Verification

After hardening deployment:

- Health endpoint returns ok.
- Protected APIs reject unauthenticated requests.
- Admin can login and read settings.
- Non-admin users cannot update settings.
- Existing branch, driver, cashier, accountant, and employee test users still
  follow their permission boundaries.
- GL Entry, Delivery Note, Stock Entry, Sales Invoice, and Payment Entry counts
  do not change during this hardening task.

## Post-cleanup Record

Record in the release notes:

- Commit hash deployed to staging.
- Security scan result.
- Test command results.
- Whether any staging data was changed.
- ERP document count deltas for this task.
