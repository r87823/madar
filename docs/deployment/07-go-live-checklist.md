# قائمة إطلاق الإنتاج

## Release

- [ ] release tag `v0.2.0` أو أحدث موجود.
- [ ] staging tag verified.
- [ ] staging smoke tests مكتملة.
- [ ] production deployment window محددة.
- [ ] rollback tag معروف.

## الاختبارات

- [ ] `python3 -m unittest discover -s madar/tests`
- [ ] `PYTHONPYCACHEPREFIX=/tmp/madar_pycache python3 -m compileall -q madar setup.py scripts/check_security_rules.py`
- [ ] `python3 scripts/check_security_rules.py`
- [ ] `flutter analyze`
- [ ] `flutter test`
- [ ] `flutter build web`

## الأمن

- [ ] only health endpoint guest-accessible.
- [ ] no secrets in repo.
- [ ] no production secrets in staging.
- [ ] no staging secrets in production.
- [ ] Administrator password changed.
- [ ] root SSH password/key rotation plan completed.
- [ ] database passwords reviewed.
- [ ] ERP API keys rotated if ever exposed.
- [ ] dev bootstrap disabled.
- [ ] test users removed or disabled.
- [ ] real users only.

## الإنتاج

- [ ] production site ready.
- [ ] production domain ready.
- [ ] SSL ready.
- [ ] reverse proxy Host routing verified.
- [ ] production backup taken.
- [ ] restore procedure known.
- [ ] disk space sufficient.
- [ ] logs accessible.

## ERPNext / Accounting

- [ ] Company verified.
- [ ] Items verified.
- [ ] Customers process verified.
- [ ] Warehouses/accounts reviewed.
- [ ] Modes of Payment verified.
- [ ] Cashbox policy verified.
- [ ] Sales Order submit policy approved.
- [ ] Sales Invoice draft policy approved.
- [ ] Sales Invoice submit policy approved.
- [ ] Payment Entry draft/submit policy approved.
- [ ] GL impact understood by accounting.

## Roles and Permissions

- [ ] Madar Admin assigned only to trusted admins.
- [ ] Madar Accountant reviewed.
- [ ] Madar Cashier cannot finalize accounting.
- [ ] Drivers scoped correctly.
- [ ] Branch users scoped correctly.
- [ ] Supervisors scoped correctly.
- [ ] Employees have basic permissions only.

## أول يوم تشغيل

- [ ] support owner assigned.
- [ ] accounting owner assigned.
- [ ] technical owner assigned.
- [ ] incident channel ready.
- [ ] monitoring active.
- [ ] backup checked after go-live.
