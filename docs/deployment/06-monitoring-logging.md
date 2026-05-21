# المراقبة والسجلات

## أهداف المراقبة

- اكتشاف توقف الخدمة بسرعة.
- اكتشاف أخطاء ERP sync.
- اكتشاف مشاكل accounting finalization.
- اكتشاف فشل backups.
- اكتشاف امتلاء disk أو تضخم logs.
- دعم التحقيق في مشاكل الصلاحيات.

## Health Monitoring

راقب:

```text
https://<production-domain>/api/method/madar.api.health.ping
```

توقع:

```json
{"message":{"ok":true,"app":"madar","service":"Madar Frappe Backend"}}
```

لـ staging يمكن استخدام السكربت read-only:

```bash
scripts/monitoring/check_staging_health.sh
```

راجع التفاصيل والـ exit codes في:

```text
docs/deployment/12-monitoring-alerting-mvp.md
```

## Frappe/Bench Logs

راجع:

```bash
tail -f /home/frappe/frappe-bench/logs/web.log
tail -f /home/frappe/frappe-bench/logs/worker.log
tail -f /home/frappe/frappe-bench/logs/scheduler.log
tail -f /home/frappe/frappe-bench/logs/error.log
```

## Docker Logs

قوالب:

```bash
docker ps
docker logs --tail=200 <frappe-container>
docker logs --tail=200 <mariadb-container>
docker logs --tail=200 <redis-container>
```

## Reverse Proxy Logs

راقب:

- 4xx spikes.
- 5xx errors.
- SSL renewal failures.
- upstream timeout.
- wrong Host/domain routing.

## مؤشرات Madar المهمة

راقب يوميًا:

- ERP Sales Order sync failures.
- Sales Invoice sync failures.
- ERP Payment Entry sync failures.
- Accounting finalization errors.
- Cashboxes waiting review.
- Cashboxes returned.
- Delivery batches returned/failed.
- Production delayed.
- Unread high-priority notifications.

## مؤشرات البنية

- Disk usage.
- Database size.
- Backup success/failure.
- CPU/RAM.
- Redis availability.
- MariaDB availability.
- SSL certificate expiry.
- Container restarts.

## تنبيهات مقترحة

- Health endpoint fails twice in a row.
- Any 5xx spike.
- Backup failed.
- Disk usage > 80%.
- ERP sync failures > 0 for more than one working hour.
- Accounting finalization failure.
- GL Entry count changes outside expected finalization windows.

## سكربتات monitoring الخفيفة

تمت إضافة أدوات read-only يمكن تشغيلها يدويًا الآن أو ربطها لاحقًا بـ cron/monitoring بعد الموافقة:

```bash
scripts/monitoring/check_staging_health.sh
scripts/monitoring/check_backup_freshness.sh
scripts/monitoring/check_erp_sync_status.py
```

هذه الأدوات لا تحتوي أسرارًا، ولا تنفذ أي mutation، ولا تطبع raw ERP errors. الهدف منها health/freshness/counts فقط.

## سجلات يجب عدم طباعتها

- passwords.
- API keys.
- API secrets.
- SSH keys.
- database credentials.
- payment card details.
- private HR data.

أي raw exception من ERP يجب تنظيفه قبل عرضه للمستخدمين.
