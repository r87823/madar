# خطة الرجوع

## متى نرجع

ابدأ rollback إذا حدث واحد من التالي:

- فشل `bench migrate` ولا يوجد fix آمن سريع.
- تعطل login.
- تعطل health endpoint بعد restart.
- خطأ صلاحيات شديد يسمح بوصول غير مصرح.
- تعطل accounting flow الحرج.
- ERP sync failures واسعة بعد النشر.
- خطأ بيانات لا يمكن احتواؤه بتعطيل ميزة.

## خيارات الرجوع

### 1. Rollback للكود فقط

مناسب عندما لا توجد migration غير قابلة للعكس أو data corruption.

```bash
cd /home/frappe/frappe-bench/apps/madar
git fetch --tags origin
git checkout <previous-production-tag>
cd /home/frappe/frappe-bench
bench --site <production-site> migrate
bench restart
```

ثم تحقق:

```bash
curl -fsS https://<production-domain>/api/method/madar.api.health.ping
bench --site <production-site> list-apps
```

### 2. Restore database/files

مطلوب إذا migration أو تشغيل تسبب بمشكلة بيانات.

```bash
bench --site <production-site> restore <database-backup-file>
bench --site <production-site> restore <database-backup-file> --with-public-files <public-files> --with-private-files <private-files>
bench --site <production-site> migrate
bench restart
```

استخدم الأمر المناسب لإصدار bench الحالي، وتحقق منه على staging قبل production.

## معايير القرار

- إذا المشكلة UI فقط ولا تؤثر على accounting/security: يمكن hotfix أو rollback code.
- إذا المشكلة permissions/security: rollback فورًا أو تعطيل الوصول المتأثر.
- إذا المشكلة ERP postings: أوقف finalization فورًا وراجع accounting قبل أي إجراء.
- إذا حدثت GL Entries خاطئة: لا تحذفها من قاعدة البيانات. اتبع إجراءات ERPNext
  المحاسبية الرسمية للتصحيح.

## تواصل أثناء rollback

- [ ] إبلاغ فريق التشغيل.
- [ ] إبلاغ المحاسبة إذا تأثرت ERP documents.
- [ ] إبلاغ المستخدمين إذا كانت هناك نافذة توقف.
- [ ] توثيق وقت بداية المشكلة.
- [ ] توثيق commit/tag قبل وبعد rollback.
- [ ] توثيق backup المستخدم إن وجد.

## بعد rollback

- تحقق من login.
- تحقق من health.
- تحقق من permissions.
- تحقق من أول flow حرج متأثر.
- راجع logs.
- افتح incident notes مع السبب والإجراء القادم.
