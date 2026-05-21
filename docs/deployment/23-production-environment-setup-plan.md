# خطة إعداد بيئة الإنتاج

## الملخص

هذه الوثيقة هي خطة إعداد فقط لبيئة production الخاصة بـ Madar MVP. لا تنفذ أي أوامر إنتاجية من هذه الوثيقة إلا ضمن مهمة تنفيذ منفصلة ومعتمدة.

النطاق الحالي:

- تخطيط production فقط.
- لا إنشاء production site في هذه المهمة.
- لا deploy إلى production.
- لا لمس production server إن وجد.
- لا تعديل بيانات staging.
- لا حذف موقع restore test.
- لا إنشاء أو إرسال ERP documents.
- لا تخزين secrets في المستودع أو الوثائق.

## 1. ملخص هدف الإنتاج

| البند | القيمة |
| --- | --- |
| التطبيق | `madar` |
| release candidate tag | `v0.4.0-production-readiness-candidate` |
| source commit | `4b641fc docs: add production readiness review` |
| توصية الجاهزية الحالية | `CONDITIONAL GO` |
| مبدأ الفصل | production منفصل تمامًا عن staging |

يجب أن تكون production environment مستقلة عن staging في:

- الموقع Frappe site.
- قاعدة البيانات.
- مجلد الملفات.
- domain وSSL.
- credentials.
- المستخدمين.
- ERP company/accounting configuration.

ممنوع في production:

- إعادة استخدام staging test data.
- تفعيل dev bootstrap.
- استخدام test users أو default passwords.
- نسخ `site_config` من staging.
- الاعتماد على حسابات staging المحاسبية بدون اعتماد محاسب.

## 2. Production Domain and SSL

قرارات مطلوبة قبل التنفيذ:

- اختيار production domain النهائي، مثل:

```text
https://<production-domain>
```

- تحديد مصدر SSL:
  - Nginx Proxy Manager Let's Encrypt.
  - أو certificate managed خارج NPM.
- إعداد reverse proxy mapping:
  - host: `<production-domain>`
  - upstream: production Frappe/bench endpoint.
  - HTTP -> HTTPS redirect enabled.
  - WebSocket/proxy headers حسب إعداد Frappe إن احتاجت.
- ربط host header مع production site domain:

```bash
bench --site <production-site> add-domain <production-domain>
```

- اختبار health العام بعد الإعداد:

```bash
curl -fsS https://<production-domain>/api/method/madar.api.health.ping
```

التوقع:

```json
{"message":{"ok":true,"app":"madar","service":"Madar Frappe Backend"}}
```

لا تقم بإعداد Nginx Proxy Manager أو SSL ضمن هذه المهمة.

## 3. Production Frappe Site

الخطة العامة:

1. اختر production site name واضحًا، مثل:

```text
<production-site>
```

2. أنشئ site منفصلًا بقاعدة بيانات منفصلة ومجلد site منفصل:

```bash
cd /home/frappe/frappe-bench
bench new-site <production-site>
```

ملاحظة: مرر كلمات المرور عبر prompt أو secret manager. لا تكتبها في docs أو scripts.

3. ثبت التطبيقات المطلوبة:

```bash
bench --site <production-site> install-app erpnext
bench --site <production-site> install-app hrms
bench --site <production-site> install-app madar
```

4. انشر Madar من tag معتمد، وليس من `main` عشوائي:

```bash
cd /home/frappe/frappe-bench/apps/madar
git fetch --tags origin
git checkout v0.4.0-production-readiness-candidate
```

5. شغل migrate على production site فقط:

```bash
cd /home/frappe/frappe-bench
bench --site <production-site> migrate
```

6. تحقق من التطبيقات:

```bash
bench --site <production-site> list-apps
```

يجب أن تظهر:

- `frappe`
- `erpnext`
- `hrms`
- `madar`

7. تحقق من health:

```bash
bench --site <production-site> execute madar.api.health.ping
curl -fsS https://<production-domain>/api/method/madar.api.health.ping
```

## 4. Environment Separation

production يجب أن يكون منفصلًا عن staging:

- staging site يبقى منفصلًا.
- production site لا يشارك قاعدة بيانات staging.
- production site لا يشارك مجلد `sites/hrms.localhost`.
- production domain لا يشير إلى staging.
- production لا يستخدم staging credentials.
- production لا يحتوي test users من staging.
- production لا يحتوي staging orders/payments/cashboxes/notifications.

تأكد أن هذه المتغيرات غير مفعلة في production:

```text
MADAR_ENABLE_DEV_BOOTSTRAP
MADAR_ENABLE_DEV_USER_BOOTSTRAP
```

وتأكد أن site config لا يحتوي:

```text
enable_madar_dev_user_bootstrap = 1
```

أمر تحقق مقترح بدون طباعة secrets:

```bash
bench --site <production-site> console
```

ثم افحص المفاتيح المطلوبة فقط، ولا تطبع كامل `site_config`.

## 5. Secrets Management

قواعد أساسية:

- لا secrets في Git.
- لا secrets في Flutter.
- لا secrets في docs.
- لا SSH keys أو passwords داخل المستودع.
- لا ERP API keys أو API secrets داخل settings UI.
- لا نسخ محتوى `site_config` إلى tickets أو docs.

الأسرار المطلوبة يجب حفظها خارج repo:

- SSH credentials.
- Frappe Administrator password.
- database root/user passwords.
- ERP API keys إن وجدت.
- أي email/SMS/WhatsApp/payment gateway secrets مستقبلية.

قائمة rotation قبل go-live:

- [ ] root SSH credentials.
- [ ] Frappe Administrator password.
- [ ] database passwords.
- [ ] ERP API keys if any.
- [ ] أي staging/test credentials تم استخدامها أثناء التطوير.
- [ ] أي credentials ظهرت في terminal history أو screenshots أو chat.

في حال تسريب secret:

1. أوقف استخدامه فورًا.
2. دوّره في مصدره.
3. راجع logs للوصول المشبوه.
4. تحقق أن المستودع لا يحتوي السر.
5. وثق incident بدون كتابة السر.

## 6. Production Users and Roles

أنشئ real users فقط. لا تنقل مستخدمي staging التجريبيين.

الأدوار المتوقعة:

- `Madar Admin`
- `Madar Accountant`
- `Madar Branch Supervisor`
- `Madar Branch User`
- `Madar Production User`
- `Madar Driver`
- `Madar Cashier`
- `Madar Employee`

خطة الإعداد:

1. أنشئ Employee records الحقيقية أو اربطها من HRMS.
2. أنشئ User records الحقيقية.
3. اربط كل User بـ Employee المناسب.
4. عيّن الدور الأقل صلاحية حسب وظيفة المستخدم.
5. تحقق من branch scopes:
   - branch users.
   - branch supervisors.
   - cashiers إن كانوا branch-scoped.
6. تحقق من department scopes:
   - production users.
7. تحقق من driver visibility:
   - driver يرى assigned batches فقط.
8. لا تستخدم default passwords.
9. فعّل force password reset إن كان مناسبًا.

تحقق مهم:

- `Madar Cashier` لا يحصل على `accounting.finalize`.
- `Madar Driver` لا يحصل على `accounting.finalize`.
- branch users/supervisors لا يحصلون على `accounting.finalize`.
- `Madar Accountant` فقط، أو admin/full access، يمكنه final submit.

## 7. ERP Accounting Configuration

هذه الخطوة تحتاج اعتماد محاسب قبل go-live.

يجب إعداد أو التحقق من:

- Company.
- Company currency.
- Chart of Accounts.
- Receivable accounts.
- Cash/bank/settlement accounts.
- Customers process.
- Items.
- Item prices.
- UOMs.
- Taxes/pricing behavior إذا كان ERPNext يتطلبها.

Modes of Payment المطلوبة:

- `Cash`
- `Card`
- `Bank Transfer`
- `Online`

Mode of Payment account mappings يجب أن تعتمد على production chart:

| Mode of Payment | Production mapping |
| --- | --- |
| `Cash` | accountant-approved cash account |
| `Card` | accountant-approved bank/settlement account |
| `Bank Transfer` | accountant-approved bank account |
| `Online` | accountant-approved gateway/bank account |

لا تنسخ staging account names تلقائيًا. على staging تم استخدام:

```text
1120 - حساب تسوية المدفوعات الإلكترونية - T
```

هذا مثال staging فقط، وليس قرارًا محاسبيًا للإنتاج.

قبل أول payment sync في production:

```bash
bench --site <production-site> console
```

تحقق read-only من mappings بدون طباعة أسرار.

## 8. Madar Operational Configuration

جهز master/operational data الآتية:

- Branches.
- Production centers.
- Production departments.
- Item department mappings.
- Real employee links.
- Branch scopes.
- Department scopes.

راجع Admin Settings:

| Setting key | قرار مطلوب |
| --- | --- |
| `attendance.duplicate_window_seconds` | مدة منع تكرار الحضور. |
| `payments.allow_overpayment` | غالبًا `false` إلا بقرار محاسبي. |
| `payments.enabled_methods` | الطرق المعتمدة فعليًا في production. |
| `cashbox.require_review` | غالبًا `true`. |
| `notifications.enabled` | غالبًا `true`. |
| `erp.auto_sync_sales_order` | يوصى `false` في البداية. |
| `erp.auto_create_sales_invoice` | يوصى `false` في البداية. |

تحقق من أن settings UI لا يعرض secrets ولا يحتوي ERP credentials.

## 9. Data Migration Policy

السياسة الافتراضية:

- لا يتم استيراد staging data إلى production.
- production يبدأ clean إلا إذا وافق business على migration منفصلة.
- لا تنسخ test orders.
- لا تنسخ test payments.
- لا تنسخ test cashboxes.
- لا تنسخ test notifications.
- لا تنسخ بيانات `madar-restore-test.localhost`.

إذا احتاج business إلى master data:

1. أنشئ import plan منفصل.
2. حدد source of truth.
3. نظف البيانات قبل import.
4. شغل import على test site أولًا.
5. راجع النتائج مع business/accounting.
6. خذ backup قبل production import.

## 10. Backup and Restore Before Go-Live

بعد إنشاء production site وإكمال الإعداد الأساسي:

1. خذ backup أولي:

```bash
bench --site <production-site> backup --with-files
```

2. تحقق من الملفات:

```bash
ls -lah sites/<production-site>/private/backups
```

3. انسخ backup إلى external encrypted storage.

4. نفذ restore drill على site منفصل production-like إن أمكن:

```bash
bench new-site <production-restore-test-site>
bench --site <production-restore-test-site> restore <database-backup-file> \
  --with-public-files <public-files-backup> \
  --with-private-files <private-files-backup>
bench --site <production-restore-test-site> migrate
bench --site <production-restore-test-site> execute madar.api.health.ping
```

استخدم صيغة `bench restore --help` المناسبة للإصدار الحالي.

Retention مقترح:

- daily full backup.
- pre-deploy backup قبل كل release.
- weekly retained backups.
- monthly archive إذا كان مطلوبًا تنظيميًا.

لا تعتمد على backup موجود على نفس الخادم فقط.

## 11. Monitoring and Alerting

الحد الأدنى قبل go-live:

- health endpoint monitoring:

```bash
curl -fsS https://<production-domain>/api/method/madar.api.health.ping
```

- container health:
  - Frappe.
  - MariaDB.
  - Redis.
  - reverse proxy.
- disk usage alerts:
  - warning > 80%.
  - critical > 90%.
- backup freshness:
  - warning > 24h.
  - critical > 48h.
- ERP sync failures:
  - `Madar Order.erp_sync_status=failed`.
  - `Madar Order.erp_invoice_sync_status=failed`.
  - `Madar Payment.erp_sync_status=failed`.
- accounting finalization errors.
- cashbox review backlog.
- high-priority unread notification backlog.
- logs review schedule:
  - first day: multiple checks.
  - first week: daily review.
  - after stabilization: scheduled operational review.

Future options:

- Uptime Kuma.
- Sentry.
- Grafana/Prometheus.
- cron + email.
- Slack/Telegram/WhatsApp alerts.

لا تركب external monitoring provider ضمن هذه الخطة إلا بمهمة منفصلة.

## 12. Go-Live Smoke Test Checklist

نفذ smoke tests على production فقط بعد backup وبعد موافقة go-live owner.

Read-only/basic checks:

- [ ] health endpoint returns `ok=true`.
- [ ] login as admin.
- [ ] login as branch user.
- [ ] login as driver.
- [ ] login as accountant.
- [ ] `get_context` returns expected roles/permissions/scopes.
- [ ] dashboard opens.
- [ ] follow-up dashboard opens.
- [ ] reports open for authorized users.
- [ ] settings visible only to admin.
- [ ] unauthorized user cannot access protected screens.

Workflow smoke tests، فقط إذا وافق business/accounting على test transaction في production:

- [ ] create test order.
- [ ] add item.
- [ ] submit for approval.
- [ ] approve.
- [ ] create ERP Sales Order draft.
- [ ] run production flow.
- [ ] run delivery/branch pickup flow.
- [ ] collect payment.
- [ ] verify cashbox entry if cash.
- [ ] create Payment Entry draft.
- [ ] create Sales Invoice draft.
- [ ] accounting finalization only if accountant approves real ERP posting impact.
- [ ] verify dashboard/reports/notifications.

ERP safety checks:

- [ ] no unexpected Delivery Note.
- [ ] no unexpected Stock Entry.
- [ ] no unexpected GL Entry outside approved finalization.
- [ ] Payment Entry remains draft unless accountant explicitly submits.
- [ ] Sales Invoice remains draft unless accountant explicitly submits.

## 13. Rollback Plan

Rollback code-only:

```bash
cd /home/frappe/frappe-bench/apps/madar
git fetch --tags origin
git checkout <previous-production-tag>
cd /home/frappe/frappe-bench
bench --site <production-site> migrate
bench restart
```

Restore backup عند مشكلة بيانات أو migration:

```bash
bench --site <production-site> restore <database-backup-file>
bench --site <production-site> restore <database-backup-file> \
  --with-public-files <public-files-backup> \
  --with-private-files <private-files-backup>
bench --site <production-site> migrate
bench restart
```

استخدم صيغة restore المناسبة لإصدار bench الحالي.

معايير rollback:

- login broken.
- health endpoint broken.
- permissions broken.
- accounting flow broken.
- ERP sync broken broadly.
- serious security issue.
- migration failure without safe immediate fix.

خطوات التواصل:

- [ ] إبلاغ technical owner.
- [ ] إبلاغ operations.
- [ ] إبلاغ accounting إذا تأثرت ERP documents.
- [ ] توثيق وقت بداية المشكلة.
- [ ] توثيق tag قبل وبعد rollback.
- [ ] توثيق backup المستخدم إن وجد.
- [ ] فتح incident notes.

## 14. Production Setup Checklist

- [ ] production domain decided.
- [ ] SSL ready.
- [ ] reverse proxy mapping ready.
- [ ] production site created.
- [ ] separate database confirmed.
- [ ] required apps installed.
- [ ] Madar tag `v0.4.0-production-readiness-candidate` deployed or newer approved tag selected.
- [ ] migrate completed.
- [ ] health check passed.
- [ ] real users created.
- [ ] dev bootstrap disabled.
- [ ] dev/test users absent.
- [ ] roles verified.
- [ ] branch scopes verified.
- [ ] department scopes verified.
- [ ] ERP company verified.
- [ ] ERP accounts verified.
- [ ] payment method records verified.
- [ ] payment method mappings verified by accountant.
- [ ] operational branches configured.
- [ ] production centers/departments configured.
- [ ] item department mappings configured.
- [ ] settings reviewed.
- [ ] initial backup created.
- [ ] external encrypted backup copy exists.
- [ ] restore procedure tested or scheduled.
- [ ] monitoring configured.
- [ ] alert owner assigned.
- [ ] smoke tests passed.
- [ ] rollback plan ready.
- [ ] first-day support owner assigned.

## 15. Conditional Go Blockers

هذه الشروط يجب إغلاقها قبل go-live:

- اختيار production domain.
- إنشاء production site.
- إعداد secrets خارج repo.
- تعطيل dev bootstrap في production.
- إنشاء real users وربط Employee records.
- اعتماد ERP company/chart/accounts مع المحاسب.
- إعداد production payment method account mappings.
- تجهيز branches/production departments/item mappings.
- إنشاء backup production ونسخة خارجية encrypted.
- تفعيل monitoring/alerts.
- تشغيل full verification suite.
- تنفيذ smoke test نهائي.
- اختيار release tag النهائي للإنتاج.
- اتخاذ قرار بخصوص staging artifacts:
  - تنظيفها في staging، أو
  - توثيقها كـ staging-only residue لا يؤثر على production.

## ما لا تنفذه هذه الخطة

- لا تنشر production.
- لا تنشئ production site.
- لا تنشئ ERP documents.
- لا ترسل Sales Invoice أو Payment Entry.
- لا تنشئ GL Entry.
- لا تنقل staging data.
- لا تخزن secrets.
- لا تغير workflows.

## الخلاصة

هذه الخطة تحول توصية **CONDITIONAL GO** إلى checklist تشغيلية لإنشاء production environment بشكل منفصل وآمن. الخطوة التالية يجب أن تكون مهمة تنفيذ production setup مع موافقات واضحة على domain، secrets، ERP accounts، real users، backup/restore، وmonitoring قبل أي go-live.
