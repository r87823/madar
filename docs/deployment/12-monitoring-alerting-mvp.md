# مراقبة وتنبيهات Madar MVP

## الملخص

هذه الوثيقة تحدد أساسًا خفيفًا للمراقبة والتنبيهات قبل الإنتاج. النطاق الحالي read-only فقط:

- لا توجد خدمات مراقبة خارجية.
- لا يوجد cron مفعل من هذه المهمة.
- لا توجد مزودات بريد أو WhatsApp أو SMS.
- لا توجد تغييرات على سير العمل أو ERP.
- لا توجد أسرار داخل السكربتات أو الوثائق.

## أهداف المراقبة

- اكتشاف توقف الخدمة مبكرًا.
- اكتشاف تعطل الحاويات الأساسية.
- اكتشاف امتلاء القرص قبل أن يؤثر على Frappe أو MariaDB.
- التأكد من حداثة النسخ الاحتياطية.
- قياس أخطاء ERP sync وaccounting finalization.
- إبراز backlog الصناديق والتنبيهات المهمة.
- توفير أوامر يمكن تشغيلها يدويًا الآن أو ربطها لاحقًا بـ cron أو أداة مراقبة.

## السكربتات المتاحة

### فحص health endpoint

الملف:

```bash
scripts/monitoring/check_staging_health.sh
```

الاستخدام:

```bash
scripts/monitoring/check_staging_health.sh
```

متغيرات اختيارية:

```bash
MADAR_HEALTH_URL="https://madar-test.r8787m.cc/api/method/madar.api.health.ping"
MADAR_HEALTH_TIMEOUT_SECONDS=10
```

التوقع:

```text
OK health_check ok=true app=madar
```

Exit codes:

| الكود | المعنى |
| ---: | --- |
| 0 | health سليم |
| 2 | health فشل أو response غير متوقع |

### فحص حداثة النسخ الاحتياطية

الملف:

```bash
scripts/monitoring/check_backup_freshness.sh
```

يفضل تشغيله من داخل خادم/حاوية Frappe حيث يوجد مسار النسخ:

```bash
MADAR_BACKUP_DIR="/home/frappe/frappe-bench/sites/hrms.localhost/private/backups" \
MADAR_BACKUP_MAX_AGE_HOURS=24 \
scripts/monitoring/check_backup_freshness.sh
```

التوقع:

```text
OK backup_fresh latest=<file> age_hours=<n> max_age_hours=24 size_bytes=<n>
```

Exit codes:

| الكود | المعنى |
| ---: | --- |
| 0 | آخر backup ضمن الحد المقبول |
| 2 | لا يوجد backup أو backup قديم أو المسار غير موجود |

ملاحظة مهمة: النسخ الحالية على نفس الخادم. قبل الإنتاج يجب إضافة نسخة خارجية encrypted/off-site.

### فحص ERP sync وbacklogs

الملف:

```bash
scripts/monitoring/check_erp_sync_status.py
```

يشغل read-only count queries عبر `bench execute`، ويطبع counts فقط بدون raw ERP errors:

```bash
cd /home/frappe/frappe-bench
python3 /path/to/madar/scripts/monitoring/check_erp_sync_status.py \
  --bench-path /home/frappe/frappe-bench \
  --site hrms.localhost
```

يفحص:

- `Madar Order.erp_sync_status = failed`
- `Madar Order.erp_invoice_sync_status = failed`
- `Madar Payment.erp_sync_status = failed`
- `Madar Order.accounting_status = needs_attention`
- `Madar Cashbox.status = submitted`
- unread high-priority `Madar Notification`

Exit codes:

| الكود | المعنى |
| ---: | --- |
| 0 | لا توجد أخطاء sync حرجة |
| 1 | backlog غير حرج عند استخدام `--warn-on-backlog` |
| 2 | يوجد ERP/payment/invoice sync failure |
| 3 | فشل تشغيل query أو إعدادات bench غير صحيحة |

مثال output:

```text
OK order_erp_sync_failed=0 order_invoice_sync_failed=0 payment_erp_sync_failed=0 accounting_needs_attention=0 cashboxes_waiting_review=0 high_priority_unread_notifications=0
```

## فحوصات يدوية موصى بها على staging

### الصحة العامة

```bash
curl -fsS https://madar-test.r8787m.cc/api/method/madar.api.health.ping
```

التوقع:

```json
{"message":{"ok":true,"app":"madar","service":"Madar Frappe Backend"}}
```

### الحاويات الأساسية

```bash
docker ps --format '{{.Names}} {{.Status}}'
```

يجب أن تكون الحاويات التالية running:

- `docker-frappe-1`
- `docker-mariadb-1`
- `docker-redis-1`
- `nginx-proxy-manager-app-1`

### استخدام القرص

```bash
df -h /
docker system df
du -sh /home/frappe/frappe-bench/sites/hrms.localhost/private/backups
```

الحدود المقترحة:

| الحالة | الشرط |
| --- | --- |
| Warning | disk usage > 80% |
| Critical | disk usage > 90% |

## مستويات التنبيه

### Critical

- health endpoint down أو لا يرجع `ok=true`.
- `docker-mariadb-1` أو `docker-frappe-1` down.
- disk usage أكبر من 90%.
- لا يوجد backup أحدث من 48 ساعة.
- فشل واسع في accounting finalization.
- أخطاء ERP sync متراكمة تمنع العمليات المالية.

### Warning

- backup age أكبر من 24 ساعة.
- disk usage أكبر من 80%.
- أي ERP sync failure أكبر من صفر.
- cashboxes waiting review أكبر من الحد التشغيلي.
- unread high-priority notifications قديمة.
- reports أو dashboard بطيئة بشكل ملحوظ.

## السجلات التي يجب مراقبتها

### Frappe/Bench

```bash
tail -f /home/frappe/frappe-bench/logs/web.log
tail -f /home/frappe/frappe-bench/logs/worker.log
tail -f /home/frappe/frappe-bench/logs/scheduler.log
tail -f /home/frappe/frappe-bench/logs/error.log
```

### Docker

```bash
docker logs --tail=200 docker-frappe-1
docker logs --tail=200 docker-mariadb-1
docker logs --tail=200 docker-redis-1
docker logs --tail=200 nginx-proxy-manager-app-1
```

### Nginx Proxy Manager

راقب:

- 5xx errors.
- upstream timeouts.
- SSL renewal failures.
- routing إلى site غير صحيح.

### حقول Madar التشغيلية

راقب من التقارير أو عبر سكربت `check_erp_sync_status.py`:

- `erp_sync_status`
- `erp_invoice_sync_status`
- `erp_payment_entry`
- `accounting_status`
- `accounting_finalization_error`
- `Madar Cashbox.status`
- high-priority unread notifications

## قواعد الأمان في المراقبة

- لا تطبع passwords أو API keys أو tokens.
- لا تحفظ credentials داخل docs أو scripts.
- لا تعرض raw ERP tracebacks في تنبيه للمستخدم.
- مخرجات السكربتات تعرض counts وحالات عامة فقط.
- أي تكامل alerting مستقبلي يجب أن يستخدم secrets خارج المستودع.

## خطة تشغيل يومية مقترحة

تشغيل يدوي أو عبر cron مستقبلي، بدون تفعيل cron في هذه المهمة:

```bash
scripts/monitoring/check_staging_health.sh
scripts/monitoring/check_backup_freshness.sh
python3 scripts/monitoring/check_erp_sync_status.py --bench-path /home/frappe/frappe-bench --site hrms.localhost
```

مراجعة يومية:

- health.
- backup freshness.
- ERP sync failures.
- accounting needs_attention.
- cashbox submitted backlog.
- disk usage.
- container status.

## تكاملات مستقبلية مقترحة

لم يتم تنفيذ أي منها الآن:

- cron + email.
- Uptime Kuma.
- Grafana/Prometheus.
- Sentry.
- Slack أو Telegram.
- WhatsApp alerts.
- centralized log shipping.

## الفجوات المعروفة

- لا توجد نسخة backup خارجية encrypted/off-site بعد.
- لا يوجد alerting آلي مفعّل.
- لا يوجد مراقبة SSL expiry آلية في السكربتات.
- لا يوجد مراقبة تفصيلية لاستهلاك MariaDB أو query latency.
- لا يوجد تتبع client-side errors من Flutter.

## نتيجة فحص staging أثناء إنشاء هذه الوثيقة

التاريخ: 2026-05-21

تم تنفيذ فحوصات read-only فقط، بدون migrate أو restart أو أي تعديل على بيانات staging.

| الفحص | النتيجة |
| --- | --- |
| public health endpoint | `OK health_check ok=true app=madar` |
| `docker-frappe-1` | running |
| `docker-mariadb-1` | running |
| `docker-redis-1` | running |
| `nginx-proxy-manager-app-1` | running |
| root disk usage | 17% |
| Docker images size | 13.3GB |
| Docker containers size | 7.166GB |
| Docker local volumes size | 592.2MB |
| backup freshness | `OK`, latest backup age ضمن 24 ساعة |

فحص ERP/backlog أعاد حالة `CRITICAL` بسبب counts فعلية غير صفرية على staging:

```text
order_erp_sync_failed=4
order_invoice_sync_failed=0
payment_erp_sync_failed=1
accounting_needs_attention=1
cashboxes_waiting_review=1
high_priority_unread_notifications=2
```

هذه النتيجة لا تعني أن السكربت غيّر البيانات؛ السكربت read-only. لكنها تعني أن staging يحتوي عناصر تحتاج مراجعة تشغيلية قبل اعتباره نظيفًا للإطلاق.

## الخطوة التالية المقترحة

قبل الإنتاج:

1. تشغيل هذه الفحوصات يدويًا لمدة أسبوع على staging.
2. تحديد thresholds تشغيلية لكل backlog.
3. إضافة off-site encrypted backups.
4. اختيار قناة تنبيه رسمية.
5. تفعيل cron أو أداة monitoring بعد مراجعة الأمان.
