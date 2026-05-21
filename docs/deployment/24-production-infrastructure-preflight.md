# تقرير فحص البنية التحتية قبل الإنتاج

## الملخص التنفيذي

- التاريخ: 2026-05-21 18:02:32 +03
- المراجع: Codex
- نوع المهمة: production infrastructure preflight / read-only فقط
- النتيجة العامة: **NEEDS DECISION**
- لم يتم إنشاء production site.
- لم يتم deploy.
- لم يتم لمس production.
- لم يتم تعديل staging data.
- لم يتم تشغيل migrate أو restart.
- لم يتم إنشاء أو إرسال أي ERP documents.

السبب: release candidate موجود ومثبت، وstaging/server baseline سليم للاستخدام الحالي، لكن الإنتاج يحتاج قرارات وتنفيذًا قبل R12-T03: domain/SSL، production site، secrets، ERP accounting configuration، real users، external backups، وmonitoring/alerting.

## 1. Release Candidate Verification

### أوامر محلية منفذة

```bash
git status --short
git log -1 --oneline
git tag --list
git show-ref --tags | grep v0.4.0-production-readiness-candidate
git rev-parse HEAD
git rev-list -n 1 v0.4.0-production-readiness-candidate
git rev-parse v0.4.0-production-readiness-candidate^{}
git log --oneline v0.4.0-production-readiness-candidate..HEAD
```

### النتائج

| البند | القيمة |
| --- | --- |
| local working tree | clean وقت الفحص |
| current local HEAD | `f71c0da docs: add production environment setup plan` |
| target release candidate tag | `v0.4.0-production-readiness-candidate` |
| target tag commit | `4b641fc docs: add production readiness review` |
| current branch vs tag | local `main` ahead by one docs-only commit: `f71c0da` |

ملاحظة: `git show-ref --tags` يعرض annotated tag object hash:

```text
5686beb33ecde9dd6ccd3a1ab00c810758656460 refs/tags/v0.4.0-production-readiness-candidate
```

والـ dereferenced commit هو:

```text
4b641fc0a1c0ef33c11612d205c29af58ee01195
```

قرار مطلوب: production يجب أن ينشر tag معتمدًا، وليس `main` عشوائيًا. إذا كانت وثائق R12 مطلوبة داخل release source، أنشئ tag أحدث منفصل. إذا كان المطلوب runtime فقط، يبقى `v0.4.0-production-readiness-candidate` هو المرشح الحالي.

## 2. Current Staging Baseline

### Health endpoint

```bash
curl -fsS https://madar-test.r8787m.cc/api/method/madar.api.health.ping
```

النتيجة:

```json
{"message":{"ok":true,"app":"madar","service":"Madar Frappe Backend"}}
```

### Staging app commit

داخل `docker-frappe-1`:

```text
445387c fix: add payment entry exchange rates
?? madar.egg-info/
```

ملاحظة: staging runtime يحتوي إصلاح payment entry exchange rates. الملف `madar.egg-info/` غير متتبع وموجود سابقًا، ولم يتم تعديله أو حذفه.

### Container status

تم تنفيذ read-only:

```bash
docker ps --format '{{.Names}} {{.Status}}'
```

النتيجة:

| Container | Status |
| --- | --- |
| `docker-redis-1` | Up 2 days |
| `docker-frappe-1` | Up 2 days |
| `docker-mariadb-1` | Up 2 days |
| `nginx-proxy-manager-app-1` | Up 2 days |

### Server baseline

| البند | القيمة |
| --- | --- |
| uptime | up 2 days, 22:16 وقت الفحص |
| OS/kernel | Linux `6.8.0-111-generic` x86_64 |
| RAM | 7.8Gi total, 5.8Gi available |
| Swap | 0B |
| root disk | 96G total, 16G used, 81G available, 17% used |
| timezone | UTC |
| NTP | active / synchronized |

### Docker storage

| Type | Total | Active | Size |
| --- | ---: | ---: | ---: |
| Images | 4 | 4 | 13.3GB |
| Containers | 4 | 4 | 7.168GB |
| Local Volumes | 1 | 1 | 592.2MB |
| Build Cache | 0 | 0 | 0B |

### Backup freshness

آخر ملفات backup على staging:

| File | Size | Age at check |
| --- | ---: | ---: |
| `20260521_144809-hrms_localhost-private-files.tar` | 10,240 bytes | 3.24h |
| `20260521_144809-hrms_localhost-files.tar` | 10,240 bytes | 3.24h |
| `20260521_144809-hrms_localhost-site_config_backup.json` | 149 bytes | 3.24h |
| `20260521_144809-hrms_localhost-database.sql.gz` | 1,173,467 bytes | 3.24h |

هذه backups موجودة على نفس الخادم، ولا تكفي وحدها للإنتاج بدون external encrypted copy.

### Monitoring result

تم تشغيل monitoring read-only:

```text
CRITICAL order_erp_sync_failed=4 order_invoice_sync_failed=0 payment_erp_sync_failed=0 accounting_needs_attention=1 cashboxes_waiting_review=0 high_priority_unread_notifications=2
```

التصنيف: CRITICAL بسبب staging residues معروفة من R11، وليس بسبب payment sync blocker جديد.

## 3. Production Domain Readiness

الحالة: **NEEDS DECISION**

قرارات مطلوبة:

- final production domain.
- DNS provider.
- DNS record type:
  - A record.
  - AAAA record إذا كان IPv6 مستخدمًا.
  - CNAME إذا كان خلف hostname آخر.
- DNS target:
  - نفس خادم staging؟
  - أم production server منفصل؟
- SSL certificate source:
  - Nginx Proxy Manager / Let's Encrypt.
  - certificate خارجي.
- HTTPS redirect policy.
- Nginx Proxy Manager proxy host:
  - domain.
  - upstream host/port.
  - SSL certificate.
  - WebSocket/proxy headers عند الحاجة.
- Frappe site domain mapping:

```bash
bench --site <production-site> add-domain <production-domain>
```

لم يتم تكوين DNS أو SSL أو Nginx Proxy Manager في هذه المهمة.

## 4. Production Server Readiness

الحالة: **NEEDS DECISION**

الحد الأدنى المقترح قبل الإنتاج:

| البند | التوصية |
| --- | --- |
| CPU | 2 vCPU أو أكثر للبداية، حسب عدد المستخدمين |
| RAM | 8GB أو أكثر؛ staging الحالي 7.8Gi |
| Disk | SSD/NVMe، مع مساحة تكفي database/files/backups/logs |
| OS | Linux LTS مدعوم |
| Docker/Compose | متاح ومدار بإصدارات واضحة |
| Backup storage | external encrypted storage |
| Time sync | NTP active |
| Firewall | 80/443 مفتوحة، SSH restricted |
| Logs | retention policy |
| Monitoring | health/disk/backup/ERP sync alerts |

ما تم فحصه على الخادم الحالي read-only:

- uptime.
- memory.
- root disk.
- Docker containers.
- Docker storage.
- OS/kernel.
- time sync.

قرار مطلوب: هل production سيعمل على نفس الخادم مع site منفصل، أم خادم production منفصل؟ يفضل production منفصل إذا أمكن لتقليل مخاطر staging/test data والتداخل التشغيلي.

## 5. Production Frappe/ERPNext Readiness

الحالة: **NOT READY**

لم يتم إنشاء production site بعد. المطلوب في R12-T03 أو مهمة تنفيذ منفصلة:

- تحديد production site name.
- إنشاء site folder منفصل.
- إنشاء database منفصلة.
- تثبيت التطبيقات:
  - `frappe`
  - `erpnext`
  - `hrms`
  - `madar`
- نشر Madar من tag:

```text
v0.4.0-production-readiness-candidate
```

أو tag أحدث معتمد.

- تشغيل migrate على production site فقط.
- التحقق من:

```bash
bench --site <production-site> list-apps
bench --site <production-site> execute madar.api.health.ping
```

قيود مهمة:

- لا dev bootstrap.
- لا test users.
- لا staging data.
- لا staging domain.
- لا staging credentials.

## 6. Secrets Readiness

الحالة: **NOT READY / NEEDS OWNER DECISION**

لا توجد secret values في هذا التقرير. المطلوب تحديد owner ومكان حفظ لكل secret:

| Secret | Status | Owner | Storage class |
| --- | --- | --- | --- |
| SSH credentials | needs decision | technical owner | password manager / managed SSH keys |
| root/admin password rotation | needs decision | technical owner | password manager |
| Frappe Administrator password | not ready | production admin owner | password manager |
| database passwords | not ready | technical owner | site config / password manager |
| ERP API keys if any | not ready unless needed | ERP/accounting owner | secret manager/password manager |
| site_config secrets | not ready | technical owner | production site_config only, never docs |
| backup encryption key | not ready | operations owner | password manager / KMS |
| monitoring credentials if any | not ready | operations owner | monitoring secret store |

قواعد:

- لا secrets في Git.
- لا secrets في Flutter.
- لا secrets في docs.
- لا طباعة secrets في terminal output.
- لا نسخ `site_config` كامل إلى tickets أو docs.

## 7. Backup/Storage Readiness

الحالة: **NEEDS DECISION**

المتوفر حاليًا:

- staging backup موجود وحديث وقت الفحص.
- restore drill نجح سابقًا على `madar-restore-test.localhost`.

المطلوب قبل production:

- external encrypted backup destination.
- retention policy:
  - daily backups.
  - pre-deploy backups.
  - weekly retained backups.
- pre-deploy backup procedure.
- restore drill على production-like site بعد إنشاء production.
- تأكيد أن backups لا تبقى فقط على نفس الخادم.

قالب تحقق backup:

```bash
bench --site <production-site> backup --with-files
ls -lah sites/<production-site>/private/backups
```

قالب restore drill:

```bash
bench new-site <production-restore-test-site>
bench --site <production-restore-test-site> restore <database-backup-file> \
  --with-public-files <public-files-backup> \
  --with-private-files <private-files-backup>
bench --site <production-restore-test-site> migrate
bench --site <production-restore-test-site> execute madar.api.health.ping
```

استخدم `bench restore --help` للتأكد من الصيغة المناسبة للإصدار.

## 8. ERP Accounting Readiness

الحالة: **NEEDS ACCOUNTANT DECISION**

قرارات production المطلوبة:

- company name.
- company currency.
- chart of accounts.
- production cash account.
- production card/bank settlement account.
- production bank transfer account.
- production online/gateway account.
- customers setup/process.
- items.
- item prices.
- UOMs.
- tax/pricing behavior إذا كان مطلوبًا.

Modes of Payment المطلوبة:

- `Cash`
- `Card`
- `Bank Transfer`
- `Online`

Production mapping يجب أن يكون معتمدًا من المحاسب:

| Mode of Payment | Required production decision |
| --- | --- |
| `Cash` | accountant-approved cash account |
| `Card` | accountant-approved bank/settlement account |
| `Bank Transfer` | accountant-approved bank account |
| `Online` | accountant-approved gateway/bank account |

لا تنسخ حساب staging:

```text
1120 - حساب تسوية المدفوعات الإلكترونية - T
```

إلا إذا كان المحاسب اعتمده صراحة في production chart.

لم يتم تعديل ERP في هذه المهمة.

## 9. User/Role Readiness

الحالة: **NOT READY**

مطلوب إنشاء real users وربطهم بـ Employee records:

- Admin.
- Accountant.
- Branch Supervisor.
- Branch User.
- Production User.
- Driver.
- Cashier.
- Employee.

مطلوب قبل go-live:

- real Employee linking.
- branch scopes.
- department scopes.
- driver assignment policy.
- no dev users.
- no default passwords.
- password reset policy.
- مراجعة أن `accounting.finalize` فقط للمحاسب أو admin/full access.
- تأكيد أن cashier/driver/branch users/supervisors/employees لا يملكون finalization.

## 10. Security Readiness

الحالة: **NEEDS DECISION**

الفحوصات الحالية:

- `python3 scripts/check_security_rules.py`: passed.
- only health endpoint guest-accessible حسب hardening docs/security scan.
- no obvious committed secrets حسب security scan.
- dev bootstrap guarded.

مطلوب production:

- عدم ضبط `MADAR_ENABLE_DEV_BOOTSTRAP`.
- عدم ضبط `MADAR_ENABLE_DEV_USER_BOOTSTRAP`.
- التأكد أن `enable_madar_dev_user_bootstrap` غير مفعل في site config.
- SSH hardening:
  - restrict access.
  - prefer keys.
  - rotate credentials.
- firewall:
  - 80/443 public.
  - SSH restricted.
  - database غير مكشوفة للعامة.
- backup encryption.
- monitoring alerts.
- review production role assignments.

## 11. Go / No-Go Evaluation

| Area | Status | Reason |
| --- | --- | --- |
| Release candidate | READY | tag موجود ويشير إلى `4b641fc`; local main ahead by docs-only commit. |
| Domain/SSL | NEEDS DECISION | production domain/DNS/SSL/NPM لم تُحدد. |
| Server | NEEDS DECISION | الخادم الحالي سليم read-only، لكن قرار same server vs separate production server مطلوب. |
| Frappe site | NOT READY | production site لم يُنشأ بعد. |
| Secrets | NOT READY | لا توجد خطة تخزين/owners مؤكدة لكل secret. |
| ERP accounting | NEEDS DECISION | production company/accounts/payment mappings تحتاج اعتماد محاسب. |
| Users/roles | NOT READY | real users/scopes لم تُنشأ بعد. |
| Backups | NEEDS DECISION | staging backup موجود، لكن production external encrypted backup غير مجهز. |
| Monitoring | NEEDS DECISION | scripts موجودة، لكن production alerting/owner غير مفعل. |
| Security | NEEDS DECISION | scan يمر، لكن production SSH/firewall/dev-bootstrap/credentials تحتاج تنفيذ. |

### التقييم النهائي

**NEEDS DECISION**

لا يوجد blocker تقني مثبت يمنع التخطيط، لكن الإنتاج غير جاهز للتنفيذ حتى تُحسم القرارات التشغيلية والمحاسبية وتُجهز الأسرار والنسخ الاحتياطية والمراقبة.

## 12. Risks

- نشر `main` بدل tag قد يدخل تغييرات غير مقصودة. استخدم tag معتمدًا.
- production على نفس خادم staging يزيد خطر التداخل التشغيلي.
- عدم وجود external encrypted backup يجعل restore readiness غير كافية للإنتاج.
- نسخ حسابات staging المحاسبية إلى production بدون اعتماد محاسب قد يسبب قيودًا خاطئة.
- عدم تفعيل monitoring فعلي يعني أن أخطاء ERP sync/finalization قد لا تُكتشف مبكرًا.
- وجود staging residues لا يؤثر على production clean site، لكنه قد يربك قراءات monitoring إذا استُخدمت staging كدليل نهائي بدون استثناءات.

## 13. Required Decisions Before R12-T03

- [ ] اختيار production domain.
- [ ] تحديد DNS provider وrecord target.
- [ ] اختيار same server أو production server منفصل.
- [ ] تحديد production site name.
- [ ] تحديد secret storage/owners.
- [ ] اعتماد production ERP company/chart/accounts.
- [ ] اعتماد Mode of Payment mappings للإنتاج.
- [ ] تحديد real user list والroles/scopes.
- [ ] تحديد external encrypted backup destination.
- [ ] تحديد monitoring owner وطريقة alerting.
- [ ] تحديد release tag النهائي:
  - `v0.4.0-production-readiness-candidate`
  - أو tag أحدث إذا أُريد تضمين وثائق R12 في release source.

## 14. Read-Only Commands Run

محليًا:

```bash
git status --short
git log -1 --oneline
git tag --list
git show-ref --tags | grep v0.4.0-production-readiness-candidate
git rev-parse HEAD
git rev-list -n 1 v0.4.0-production-readiness-candidate
git rev-parse v0.4.0-production-readiness-candidate^{}
git log --oneline v0.4.0-production-readiness-candidate..HEAD
python3 scripts/check_security_rules.py
```

Staging/server read-only:

```bash
curl -fsS https://madar-test.r8787m.cc/api/method/madar.api.health.ping
uptime
uname -a
free -h
df -h /
timedatectl
docker ps --format '{{.Names}} {{.Status}}'
docker system df
docker exec docker-frappe-1 bash -lc 'cd /home/frappe/frappe-bench/apps/madar && git log -1 --oneline && git status --short'
docker exec docker-frappe-1 bash -lc 'ls -1t /home/frappe/frappe-bench/sites/hrms.localhost/private/backups | sed -n "1,8p"'
docker exec docker-frappe-1 bash -lc 'cd /home/frappe/frappe-bench && python3 apps/madar/scripts/monitoring/check_erp_sync_status.py --bench-path /home/frappe/frappe-bench --site hrms.localhost || true'
```

## 15. Statement of Non-Mutation

هذا الفحص كان read-only. لم يتم:

- إنشاء production site.
- نشر production.
- تعديل staging data.
- تعديل production server.
- تشغيل migrate.
- تشغيل restart.
- إنشاء ERP documents.
- إرسال ERP documents.
- تخزين secrets.
- تغيير كود التطبيق.

## الخلاصة

البنية الحالية كافية للاستمرار إلى مرحلة قرارات الإنتاج، لكنها ليست جاهزة لتنفيذ production setup بعد. الحالة الأنسب: **NEEDS DECISION**. الخطوة التالية قبل R12-T03 هي حسم domain/server/secrets/accounting/users/backup/monitoring، ثم تنفيذ production setup في مهمة منفصلة مع backup وrollback gate واضح.
