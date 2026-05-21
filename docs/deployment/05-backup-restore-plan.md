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

## التحقق بعد الاستعادة

- [ ] site يعمل.
- [ ] users موجودون.
- [ ] roles صحيحة.
- [ ] Madar doctypes موجودة.
- [ ] ERPNext documents موجودة.
- [ ] private files قابلة للوصول للمصرح لهم.
- [ ] health endpoint يعمل.
- [ ] لا يوجد dev bootstrap في production restore.
