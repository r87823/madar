# تقرير تمرين النسخ الاحتياطي والاستعادة

## الملخص

- التاريخ: 2026-05-21
- البيئة: staging فقط
- الخادم: `root@46.202.154.140`
- الحاوية: `docker-frappe-1`
- الموقع: `hrms.localhost`
- الرابط العام: `https://madar-test.r8787m.cc`
- مسار bench داخل الحاوية: `/home/frappe/frappe-bench`
- release tag: `v0.3.0-staging-polished-mvp`
- commit: `f461ada feat: polish arabic error messages`
- نتيجة النسخ الاحتياطي: نجح
- نتيجة الاستعادة: مؤجلة، ولم يتم تنفيذ restore على الموقع الحالي

## أوامر التحقق قبل النسخ

تم التحقق من health endpoint:

```bash
curl -fsS https://madar-test.r8787m.cc/api/method/madar.api.health.ping
```

النتيجة المختصرة:

```json
{"ok": true, "app": "madar", "service": "Madar Frappe Backend"}
```

تم التحقق من الحاويات ومسار bench:

```bash
docker ps --format '{{.Names}} {{.Status}}'
docker exec docker-frappe-1 bash -lc 'cd /home/frappe/frappe-bench && pwd'
```

تم فحص خيارات backup:

```bash
bench --site hrms.localhost backup --help
```

الخيار `--with-files` متاح في هذا الإصدار.

## أعداد ERP الحساسة قبل النسخ

هذه الأعداد للقراءة فقط، والغرض منها التأكد أن تمرين النسخ لم ينشئ أو يرسل مستندات ERP:

| DocType | قبل النسخ |
| --- | ---: |
| GL Entry | 4 |
| Delivery Note | 0 |
| Stock Entry | 0 |
| Sales Invoice | 3 |
| Payment Entry | 2 |

## أمر النسخ الاحتياطي المستخدم

تم تنفيذ الأمر داخل الحاوية من مسار bench:

```bash
cd /home/frappe/frappe-bench
bench --site hrms.localhost backup --with-files
```

## موقع النسخة الاحتياطية

المسار داخل الحاوية:

```text
/home/frappe/frappe-bench/sites/hrms.localhost/private/backups
```

ملاحظة أمنية: هذا المسار يحتوي نسخة `site_config`، وقد تحتوي ملفات إعدادات المواقع في بيئات أخرى على أسرار. لا تنسخ هذا المسار إلى المستودع ولا تدرج محتويات الملفات في التوثيق.

## ملفات النسخة الاحتياطية

| النوع | الملف | الحجم |
| --- | --- | ---: |
| Database | `20260521_144809-hrms_localhost-database.sql.gz` | 1,173,467 bytes |
| Public files | `20260521_144809-hrms_localhost-files.tar` | 10,240 bytes |
| Private files | `20260521_144809-hrms_localhost-private-files.tar` | 10,240 bytes |
| Site config | `20260521_144809-hrms_localhost-site_config_backup.json` | 149 bytes |

ملخص Frappe أظهر وقت النسخ:

```text
Backup Summary for hrms.localhost at 2026-05-21 14:48:14.549443
Backup for Site hrms.localhost has been successfully completed with files
```

قائمة الملفات في نظام الملفات ظهرت بتوقيت الحاوية كالتالي:

```text
May 21 11:48
```

هذا اختلاف عرض timezone فقط، وليس فشلًا في النسخ.

## التحقق بعد النسخ

تم إعادة فحص health endpoint بعد النسخ:

```json
{"ok": true, "app": "madar", "service": "Madar Frappe Backend"}
```

تم إعادة فحص أعداد ERP الحساسة:

| DocType | قبل النسخ | بعد النسخ | النتيجة |
| --- | ---: | ---: | --- |
| GL Entry | 4 | 4 | لم يتغير |
| Delivery Note | 0 | 0 | لم يتغير |
| Stock Entry | 0 | 0 | لم يتغير |
| Sales Invoice | 3 | 3 | لم يتغير |
| Payment Entry | 2 | 2 | لم يتغير |

## حالة تمرين الاستعادة

لم يتم تنفيذ restore فعلي في هذه الجولة.

الأسباب:

- الشرط الأساسي يمنع الاستعادة فوق `hrms.localhost` بدون موافقة صريحة.
- إنشاء site اختبار داخل نفس bench سيضيف قاعدة بيانات ومجلد site جديدين داخل بيئة staging الحالية.
- حذف site الاختبار بعد التمرين عملية destructive وتحتاج موافقة منفصلة.
- لم يتم تجهيز حاوية/bench معزولة مخصصة لتمارين restore.

القرار الآمن: الاكتفاء بإنشاء backup والتحقق من الملفات والصحة والأعداد، وتوثيق إجراء restore منفصل لنافذة controlled.

## إجراء restore المقترح للجولة القادمة

نفذ هذا فقط في نافذة صيانة staging وبعد موافقة صريحة على إنشاء وحذف site اختبار.

اسم site مقترح:

```text
madar-restore-test.localhost
```

خطوات عالية المستوى:

```bash
cd /home/frappe/frappe-bench

# 1. إنشاء site اختبار منفصل، مع كلمة مرور admin مؤقتة لا تكتب في repo أو docs.
bench new-site madar-restore-test.localhost

# 2. تثبيت التطبيقات اللازمة إن لم تكن مثبتة على site الاختبار.
bench --site madar-restore-test.localhost install-app erpnext
bench --site madar-restore-test.localhost install-app hrms
bench --site madar-restore-test.localhost install-app madar

# 3. استعادة database backup إلى site الاختبار فقط.
bench --site madar-restore-test.localhost restore \
  sites/hrms.localhost/private/backups/20260521_144809-hrms_localhost-database.sql.gz

# 4. استعادة الملفات العامة والخاصة حسب صيغة Frappe المدعومة في هذا الإصدار.
# راجع bench --site madar-restore-test.localhost restore --help قبل التنفيذ.

# 5. تشغيل migrate على site الاختبار فقط.
bench --site madar-restore-test.localhost migrate

# 6. اختبار health داخليًا باستخدام Host مناسب أو add-domain مؤقت عند الحاجة.
```

لا تنفذ:

- لا تستخدم `hrms.localhost` كهدف restore.
- لا تحذف أي site بدون موافقة.
- لا تضف domain عام لsite الاختبار بدون موافقة.
- لا تشغل dev bootstrap على restore production أو restore test إلا إذا كان ذلك مقصودًا ومؤمّنًا.

## المشاكل والملاحظات

- لا توجد نسخة احتياطية سابقة ظاهرة في مجلد backups قبل هذا التمرين.
- حجم public/private files صغير جدًا في staging الحالي، وهذا طبيعي إذا كانت الملفات قليلة.
- `site_config_backup.json` صغير، ومع ذلك يجب التعامل معه كملف حساس.
- لم يتم اختبار restore فعليًا، لذلك readiness للاستعادة ما زال جزئيًا حتى تنفذ جولة restore معزولة.

## المخاطر المتبقية

- backup موجود داخل نفس الخادم/الحاوية؛ يجب نسخه إلى تخزين خارجي آمن ومشفّر.
- لم يتم قياس زمن restore الفعلي.
- لم يتم التحقق من استعادة private files عمليًا.
- لم يتم تنفيذ restore drill على bench معزول.

## توصيات production

- نفذ backup pre-deploy قبل أي production deployment.
- انسخ backups إلى تخزين خارجي، مع retention واضح.
- نفذ restore drill كامل على بيئة منفصلة قبل go-live.
- لا تعتمد على backup موجود على نفس الخادم وحده.
- دوّر كلمات المرور ومفاتيح الوصول قبل go-live حسب خطة secrets.
- راقب نجاح النسخ يوميًا بعد الإطلاق.

## موعد التمرين القادم

التوصية: تنفيذ restore drill كامل خلال 7 أيام أو قبل أول production deployment، أيهما أقرب.
