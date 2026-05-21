# Runbook نشر الإنتاج

## قبل البدء

لا تبدأ النشر إلا إذا:

- [ ] release tag معتمد ومجرب على staging.
- [ ] tests تمر محليًا أو في CI.
- [ ] security scan يمر.
- [ ] production backup مأخوذ ومتحقق منه.
- [ ] rollback plan جاهز.
- [ ] نافذة الصيانة أو خطة التواصل جاهزة.
- [ ] production credentials متاحة للمشغلين المصرح لهم فقط.

## أوامر تحقق قبل النشر

```bash
git status --short
git tag --list
python3 scripts/check_security_rules.py
python3 -m unittest discover -s madar/tests
PYTHONPYCACHEPREFIX=/tmp/madar_pycache python3 -m compileall -q madar setup.py scripts/check_security_rules.py
flutter analyze
flutter test
flutter build web
```

## خطوات النشر

1. Confirm target production site:

```bash
bench list-sites
bench --site <production-site> list-apps
```

2. Take production backup:

```bash
bench --site <production-site> backup --with-files
```

3. Record current release:

```bash
cd /home/frappe/frappe-bench/apps/madar
git rev-parse HEAD
git describe --tags --always
```

4. Pull approved release tag:

```bash
cd /home/frappe/frappe-bench/apps/madar
git fetch --tags origin
git checkout <approved-production-tag>
```

5. Run migrate:

```bash
cd /home/frappe/frappe-bench
bench --site <production-site> migrate
```

6. Restart services:

```bash
bench restart
```

7. Health check:

```bash
curl -fsS https://<production-domain>/api/method/madar.api.health.ping
```

8. Smoke tests:

- Login as a real admin user.
- Open current user context.
- Open follow-up dashboard.
- Open reports read-only.
- Confirm settings screen is admin-only.
- Confirm unauthorized protected endpoint returns 403.

9. Permission verification:

- Branch user sees own branch only.
- Driver sees assigned batches only.
- Accountant sees accounting review.
- Cashier cannot finalize accounting.
- Employee cannot access admin/accounting screens.

10. Dev bootstrap verification:

```bash
bench --site <production-site> console
```

Check that dev bootstrap flags are not enabled in site config/environment.

11. Monitor logs for the first hour:

```bash
tail -f logs/web.log
tail -f logs/worker.log
tail -f logs/scheduler.log
```

## ممنوع أثناء النشر

- لا تستخدم `git reset --hard` على production إلا ضمن rollback واضح.
- لا تحذف business documents.
- لا تنشئ ERP documents يدويًا لاختبار النشر.
- لا تفعل dev bootstrap.
- لا تطبع secrets في terminal أو tickets.
