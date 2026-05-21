# خطة النسخ الاحتياطي والاستعادة

## ما يجب نسخه

- قاعدة بيانات production site.
- public files.
- private files.
- site configuration، مع عدم نشر الأسرار في tickets/docs.
- نسخة من release tag المستخدم.
- إعدادات reverse proxy المهمة، بدون أسرار.

## تكرار النسخ

- Daily full backup.
- Pre-deploy backup قبل كل production deploy.
- Retention مقترح:
  - يومي آخر 7 أيام.
  - أسبوعي آخر 4 أسابيع.
  - شهري حسب سياسة الشركة.

## أمر backup

```bash
bench --site <production-site> backup --with-files
```

انقل النسخة إلى تخزين آمن خارج نفس الخادم إذا أمكن.

## حماية backup

- تشفير التخزين إن توفر.
- صلاحيات وصول محدودة.
- لا ترسل backup عبر قنوات غير آمنة.
- site_config قد يحتوي أسرارًا؛ تعامل معه كسر.

## Restore drill

نفذ اختبار استعادة دوريًا على staging أو بيئة restore منفصلة:

1. أنشئ site اختبار.
2. استعد database/files.
3. شغل migrate.
4. تحقق من login.
5. تحقق من health.
6. تحقق من عينة orders/payments/cashbox/reports.
7. وثق زمن الاستعادة والمشاكل.

قالب:

```bash
bench new-site <restore-test-site>
bench --site <restore-test-site> restore <backup-file>
bench --site <restore-test-site> migrate
bench restart
```

## ضوابط تمرين staging

- لا تستعد فوق staging site الحالي إلا بموافقة صريحة وخطة rollback.
- الأفضل إنشاء site اختبار منفصل مثل `<restore-test-site>` داخل bench أو داخل bench معزول.
- إذا كان site الاختبار داخل نفس bench، وثق أنه سيضيف قاعدة بيانات ومجلد site جديدين.
- حذف site الاختبار بعد التمرين عملية destructive وتحتاج موافقة منفصلة.
- لا تضع backup files داخل repo.
- لا تنسخ محتوى `site_config` إلى docs أو tickets لأنه قد يحتوي أسرارًا.
- قبل وبعد التمرين، تحقق من health endpoint وأعداد مستندات ERP الحساسة:
  - `GL Entry`
  - `Delivery Note`
  - `Stock Entry`
  - `Sales Invoice`
  - `Payment Entry`

## نتائج التمارين

- 2026-05-21: تم تنفيذ backup staging بنجاح للموقع `hrms.localhost` ولم يتم تنفيذ restore فوق الموقع الحالي. راجع:
  `docs/deployment/09-backup-restore-drill-report.md`
- 2026-05-21: تم تنفيذ restore drill بنجاح على site منفصل باسم `madar-restore-test.localhost`. راجع:
  `docs/deployment/10-restore-drill-report.md`

## صيغة restore المجربة على staging

الصيغة التالية نجحت على Frappe/Docker staging الحالي:

```bash
bench new-site madar-restore-test.localhost \
  --mariadb-root-password "$DB_ROOT_PASSWORD" \
  --admin-password "$ADMIN_TMP" \
  --no-mariadb-socket

bench --site madar-restore-test.localhost restore \
  sites/hrms.localhost/private/backups/<timestamp>-hrms_localhost-database.sql.gz \
  --mariadb-root-password "$DB_ROOT_PASSWORD" \
  --with-public-files sites/hrms.localhost/private/backups/<timestamp>-hrms_localhost-files.tar \
  --with-private-files sites/hrms.localhost/private/backups/<timestamp>-hrms_localhost-private-files.tar

bench --site madar-restore-test.localhost migrate
bench --site madar-restore-test.localhost clear-cache
```

ملاحظة: `--no-mariadb-socket` ظهر كخيار deprecated. للجولات القادمة راجع الخيار الأحدث المناسب قبل التنفيذ.

## التحقق بعد الاستعادة

- [ ] site يعمل.
- [ ] users موجودون.
- [ ] roles صحيحة.
- [ ] Madar doctypes موجودة.
- [ ] ERPNext documents موجودة.
- [ ] private files قابلة للوصول للمصرح لهم.
- [ ] health endpoint يعمل.
- [ ] لا يوجد dev bootstrap في production restore.
