# تقرير تمرين الاستعادة على موقع منفصل

## الملخص

- التاريخ: 2026-05-21
- البيئة: staging فقط
- المشغل: Codex
- الخادم: `root@46.202.154.140`
- الحاوية: `docker-frappe-1`
- مسار bench: `/home/frappe/frappe-bench`
- الموقع المصدر: `hrms.localhost`
- موقع الاستعادة: `madar-restore-test.localhost`
- النسخة المستخدمة: `20260521_144809`
- نتيجة الاستعادة: نجحت
- حالة موقع staging النشط بعد التمرين: سليم
- حالة موقع restore بعد التمرين: موجود ومتاح للفحص

## ملاحظة مهمة عن commit الموجود على staging

الفحص داخل `apps/madar` على الخادم أظهر:

```text
0528ae9 chore: add security hardening checks
```

بينما آخر release tag محليًا هو:

```text
v0.3.0-staging-polished-mvp
f461ada feat: polish arabic error messages
```

لم يتم تغيير ذلك في هذا التمرين لأن النطاق هو restore drill فقط، وليس deployment. يجب توحيد نسخة staging قبل أي مقارنة نهائية مع release tag المصقول.

## ملفات النسخة المستخدمة

المسار:

```text
/home/frappe/frappe-bench/sites/hrms.localhost/private/backups
```

الملفات:

- `20260521_144809-hrms_localhost-database.sql.gz`
- `20260521_144809-hrms_localhost-files.tar`
- `20260521_144809-hrms_localhost-private-files.tar`
- `20260521_144809-hrms_localhost-site_config_backup.json`

لم يتم نسخ أي backup file إلى المستودع.

## Pre-flight

تم التحقق من health endpoint للموقع النشط:

```bash
curl -fsS https://madar-test.r8787m.cc/api/method/madar.api.health.ping
```

النتيجة:

```json
{"ok": true, "app": "madar", "service": "Madar Frappe Backend"}
```

تم التحقق من وجود ملفات backup:

```bash
ls -lah sites/hrms.localhost/private/backups/*20260521_144809*
```

تم التحقق أن موقع الاستعادة غير موجود قبل البدء:

```bash
test -d sites/madar-restore-test.localhost && echo EXISTS || echo MISSING
```

النتيجة قبل التنفيذ:

```text
MISSING
```

## أوامر restore المستخدمة

تم فحص help أولًا:

```bash
bench new-site --help
bench --site madar-restore-test.localhost restore --help
```

ثم تم إنشاء site منفصل. تم تمرير كلمات المرور كمتغيرات بيئة مؤقتة داخل جلسة الخادم، ولم يتم طباعتها أو حفظها في المستودع:

```bash
cd /home/frappe/frappe-bench
bench new-site madar-restore-test.localhost \
  --mariadb-root-password "$DB_ROOT_PASSWORD" \
  --admin-password "$ADMIN_TMP" \
  --no-mariadb-socket
```

ملاحظة: ظهر تحذير أن `--no-mariadb-socket` deprecated. في الجولات القادمة يفضل استبداله بالخيار الأحدث المناسب لبيئة Docker.

تمت الاستعادة على موقع الاختبار فقط:

```bash
bench --site madar-restore-test.localhost restore \
  sites/hrms.localhost/private/backups/20260521_144809-hrms_localhost-database.sql.gz \
  --mariadb-root-password "$DB_ROOT_PASSWORD" \
  --with-public-files sites/hrms.localhost/private/backups/20260521_144809-hrms_localhost-files.tar \
  --with-private-files sites/hrms.localhost/private/backups/20260521_144809-hrms_localhost-private-files.tar
```

نتيجة restore:

```text
Site madar-restore-test.localhost has been restored with files
```

ثم تم تشغيل migrate وclear-cache على موقع الاستعادة فقط:

```bash
bench --site madar-restore-test.localhost migrate
bench --site madar-restore-test.localhost clear-cache
```

النتيجة: migrate نجح، وظهر تحديث تطبيقات `frappe`, `erpnext`, `hrms`, و`madar`.

## التطبيقات بعد الاستعادة

```text
frappe  17.x.x-develop (97f792a) develop
erpnext 17.x.x-develop (21a9eed) develop
hrms    17.0.0-dev               develop
madar   0.0.1                    main
```

## health الداخلي لموقع الاستعادة

تم تنفيذ:

```bash
bench --site madar-restore-test.localhost execute madar.api.health.ping
```

النتيجة:

```json
{"ok": true, "app": "madar", "service": "Madar Frappe Backend"}
```

## DocTypes الأساسية

تم التحقق من وجود DocTypes التالية على موقع الاستعادة:

| DocType | النتيجة |
| --- | --- |
| Madar Order | موجود |
| Madar Payment | موجود |
| Madar Cashbox | موجود |
| Madar Notification | موجود |
| Madar Setting | موجود |

## أعداد المستندات على موقع الاستعادة

| DocType | العدد |
| --- | ---: |
| Madar Order | 71 |
| Madar Payment | 13 |
| Madar Cashbox | 6 |
| Madar Notification | 6 |
| Madar Setting | 9 |
| Sales Invoice | 3 |
| Payment Entry | 2 |
| GL Entry | 4 |

هذه الأعداد من موقع `madar-restore-test.localhost`، وليست من الموقع النشط.

## التحقق من سلامة موقع staging النشط

بعد الاستعادة، تم التحقق من health endpoint للموقع النشط `hrms.localhost` عبر الرابط العام:

```json
{"ok": true, "app": "madar", "service": "Madar Frappe Backend"}
```

تم التحقق من أعداد ERP الحساسة على الموقع النشط:

| DocType | العدد بعد restore drill |
| --- | ---: |
| GL Entry | 4 |
| Delivery Note | 0 |
| Stock Entry | 0 |
| Sales Invoice | 3 |
| Payment Entry | 2 |

لم يتم تنفيذ restore فوق `hrms.localhost`، ولم يتم تعديل routing العام أو Nginx Proxy Manager.

## المشاكل والملاحظات

- staging code داخل container ليس على tag `v0.3.0-staging-polished-mvp`، بل على `0528ae9`.
- أمر `bench new-site` استخدم `--no-mariadb-socket` وظهر أنه deprecated.
- لم يتم تعريض restore site عبر public domain، وهذا مقصود لتجنب أي routing غير ضروري.
- لم يتم حذف restore site لأن المهمة تمنع cleanup destructive بدون موافقة صريحة.

## حالة cleanup

موقع الاستعادة لا يزال موجودًا:

```text
madar-restore-test.localhost
```

لا تحذفه إلا بعد الموافقة. أمر cleanup المقترح، غير منفذ:

```bash
bench drop-site madar-restore-test.localhost
```

قبل تشغيل cleanup، خذ قرارًا هل تريد الاحتفاظ بالموقع للفحص اليدوي أو حذفه لتقليل استهلاك الموارد.

## خلاصة جاهزية الإنتاج

تم إثبات أن backup من staging يمكن استعادته إلى site منفصل وأن تطبيق Madar يعمل داخليًا بعد restore وmigrate. هذا يرفع ثقة الاستعادة، لكن قبل production go-live يجب:

- توحيد staging deployment مع release tag المقصود.
- تنفيذ restore drill آخر بعد نشر نفس release tag على staging.
- نقل backups إلى تخزين خارجي آمن.
- توثيق زمن الاستعادة الكامل من بداية إنشاء site حتى health OK.
