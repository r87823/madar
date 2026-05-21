# تقرير مراجعة جاهزية الإنتاج

## الملخص التنفيذي

- التاريخ: 2026-05-21 17:45:05 +03
- البيئة التي تمت مراجعتها: staging
- الموقع النشط: `hrms.localhost`
- الرابط العام: `https://madar-test.r8787m.cc`
- الخادم: `root@46.202.154.140`
- الحاوية: `docker-frappe-1`
- نوع المهمة: review/report فقط
- التوصية: **CONDITIONAL GO**

يمكن الانتقال نحو production بعد تنفيذ قائمة الشروط قبل الإطلاق أدناه. لا توجد حاليًا مشكلة payment sync حرجة بعد R11-T13، لكن staging ما زال يحتوي test artifacts/backlog، كما أن production secrets/users/domain/monitoring/release tag النهائي تحتاج اعتمادًا صريحًا قبل go-live.

## حدود المراجعة

لم يتم:

- تعديل بيانات staging.
- تنظيف test artifacts.
- retry لأي sync.
- إرسال Payment Entry أو Sales Invoice.
- إنشاء GL Entry.
- تشغيل migrate أو restart.
- لمس production.
- حذف موقع restore test.

تم تنفيذ فحوصات read-only فقط.

## نسخة Git والوسوم

### المستودع المحلي

| البند | القيمة |
| --- | --- |
| الفرع | `main` |
| الحالة | clean, aligned with `origin/main` |
| commit وقت المراجعة | `65602c8 docs: add production readiness backlog recheck` |

الوسوم المتاحة:

| Tag | الغرض |
| --- | --- |
| `v0.3.0-staging-polished-mvp` | polished MVP checkpoint |
| `v0.2.0-staging-hardened-mvp` | hardened MVP checkpoint |
| `v0.1.0-staging-accounting-complete` | accounting complete checkpoint |

### staging runtime

داخل `/home/frappe/frappe-bench/apps/madar`:

```text
445387c fix: add payment entry exchange rates
?? madar.egg-info/
```

ملاحظة جاهزية: `445387c` يحتوي إصلاح backend مطلوب لمزامنة Payment Entry، بينما `v0.3.0-staging-polished-mvp` أقدم منه. قبل production يجب إنشاء tag نهائي جديد من commit معتمد بعد هذه المراجعة، أو توثيق release source بدقة. لا يُنصح بالإطلاق من `v0.3.0` وحده إذا كان payment sync draft مطلوبًا.

## صحة staging

Health endpoint:

```json
{"ok": true, "app": "madar", "service": "Madar Frappe Backend"}
```

موقع restore test ما زال موجودًا:

```text
madar-restore-test.localhost
```

لم يتم حذفه أو تعديله في هذه المراجعة.

## ملخص الاختبارات والتحقق

فحوصات هذه المراجعة:

| الفحص | النتيجة |
| --- | --- |
| `python3 scripts/check_security_rules.py` | passed |
| health endpoint | passed |
| monitoring/backlog check | ran read-only; returned CRITICAL due to known staging residues |
| local git status | clean قبل إنشاء هذا التقرير |

ملاحظة: لم يتم تشغيل full backend/flutter test suite في هذه المهمة لأنها مراجعة وثائق وفحوصات read-only. يجب تشغيلها ضمن final pre-production release gate:

```bash
python3 -m unittest discover -s madar/tests
PYTHONPYCACHEPREFIX=/tmp/madar_pycache python3 -m compileall -q madar setup.py scripts/check_security_rules.py
python3 scripts/check_security_rules.py
flutter analyze
flutter test
flutter build web
```

## ملخص الأمان

### Guest endpoint

الفحص المحلي أظهر أن endpoint الوحيد المسموح له بـ `allow_guest=True` هو:

```text
madar/api/health.py
```

وهذا متوافق مع hardening checklist.

### Security scan

```text
Security scan passed: no issues found.
```

الـ scan يغطي بشكل خفيف:

- unsafe `allow_guest=True`.
- Flutter direct ERP/resource access.
- direct Madar role checks في service/API logic.
- obvious committed credential patterns.

### Dev bootstrap

Dev bootstrap موثق ومحصور خلف guard:

- environment: `MADAR_ENABLE_DEV_BOOTSTRAP=1`
- site config: `enable_madar_dev_user_bootstrap`

قبل production يجب التأكد من تعطيله، وعدم وجود test users أو default passwords في production.

### حدود Flutter

القاعدة المعتمدة ما زالت:

- Flutter يستدعي Madar/Frappe whitelisted APIs فقط.
- لا يوجد direct ERPNext DocType/API access من Flutter.
- لا توجد ERP credentials في Flutter.

## Backup وRestore

### Backup

آخر backup موثق وموجود على staging:

| النوع | الملف |
| --- | --- |
| Database | `20260521_144809-hrms_localhost-database.sql.gz` |
| Public files | `20260521_144809-hrms_localhost-files.tar` |
| Private files | `20260521_144809-hrms_localhost-private-files.tar` |
| Site config | `20260521_144809-hrms_localhost-site_config_backup.json` |

المسار:

```text
/home/frappe/frappe-bench/sites/hrms.localhost/private/backups
```

### Restore drill

تم restore drill بنجاح على موقع منفصل:

```text
madar-restore-test.localhost
```

تم التحقق من:

- نجاح restore database/files.
- تشغيل migrate على موقع restore فقط.
- health الداخلي يعمل.
- وجود DocTypes الأساسية.
- عدم restore فوق `hrms.localhost`.

### فجوة متبقية

النسخ الحالية موجودة على نفس الخادم. قبل production يجب توفير external encrypted/off-site backup copy مع retention واضح، وتنفيذ restore drill نهائي من نسخة production pre-launch أو نسخة staging النهائية بعد release tag النهائي.

## Monitoring

تم إنشاء Monitoring MVP وسكربتات read-only:

- `scripts/monitoring/check_staging_health.sh`
- `scripts/monitoring/check_backup_freshness.sh`
- `scripts/monitoring/check_erp_sync_status.py`

نتيجة monitoring الحالية:

```text
CRITICAL order_erp_sync_failed=4 order_invoice_sync_failed=0 payment_erp_sync_failed=0 accounting_needs_attention=1 cashboxes_waiting_review=0 high_priority_unread_notifications=2
```

سبب CRITICAL الحالي هو staging residues، وليس payment sync blocker جديد.

قبل production يجب:

- تثبيت آلية تشغيل دورية للفحوصات أو أداة monitoring خارجية.
- تحديد alert owner.
- مراقبة backups, ERP sync, accounting finalization, disk usage, container health.

## ERP وAccounting Readiness

### Sales Order

- ERP Sales Order sync موجود.
- Sales Order submit موجود ومقيد accounting/admin.
- لا يوجد ERP Sales Order blocker جديد في هذه المراجعة، لكن توجد 4 failed order sync staging artifacts تاريخية.

### Sales Invoice

- Sales Invoice draft sync موجود.
- Sales Invoice submit/finalization موجود ومقيد بـ `accounting.finalize` أو `system.full_access`.
- `invoice_erp_sync_failed = 0`.

### Payment Entry

- Payment Entry draft sync موجود.
- Payment Entry submit/finalization موجود ومقيد بـ `accounting.finalize` أو `system.full_access`.
- `payment_erp_sync_failed = 0`.
- `MADAR-PAY-2026-00012` تم حله:
  - `erp_sync_status = synced`
  - `erp_payment_entry = ACC-PAY-2026-00006`
  - `Payment Entry docstatus = 0`

### Payment method mappings

تم إصلاح mapping على staging:

| Mode of Payment | Account |
| --- | --- |
| `Cash` | `1110 - نقد - T` |
| `Card` | `1120 - حساب تسوية المدفوعات الإلكترونية - T` |
| `Bank Transfer` | `1120 - حساب تسوية المدفوعات الإلكترونية - T` |
| `Online` | `1120 - حساب تسوية المدفوعات الإلكترونية - T` |

تحذير production: لا تنسخ حساب staging تلقائيًا. يجب أن يعتمد المحاسب حسابات production الحقيقية حسب chart of accounts الإنتاجي.

### ERP document counts on staging

| DocType | Count |
| --- | ---: |
| GL Entry | 4 |
| Delivery Note | 0 |
| Stock Entry | 0 |
| Sales Invoice | 3 |
| Payment Entry | 3 |

هذه أعداد قراءة فقط وقت المراجعة.

## Operational Workflow Readiness

| المجال | الحالة | الملاحظات |
| --- | --- | --- |
| Auth / Roles / Permissions | Ready with production review | راجع real users/scopes قبل الإطلاق. |
| Attendance | Ready | يعتمد HRMS Employee/Employee Checkin. |
| Orders / Approval | Ready with cleanup note | توجد failed order sync artifacts على staging. |
| ERP Sales Order Sync | Ready with accounting config review | production customers/accounts/items must be verified. |
| Production Work Orders | Ready | لا يوجد ERPNext Work Order integration. |
| Delivery / Branch Pickup | Ready | لا يوجد Delivery Note/Stock Entry. |
| Driver Batches | Ready | Driver visibility يعتمد assigned batches. |
| Payments | Ready after R11-T13 | payment sync blocker resolved on staging. |
| Cashbox | Ready with policy review | `cashboxes_waiting_review=0` حاليًا. |
| ERP Payment Entry | Ready with production account mapping | Draft/submit flows موجودة ومقيدة. |
| Sales Invoice / Accounting Finalization | Ready with accountant sign-off | final submit يخلق GL محتملًا ويحتاج owner واضح. |
| Notifications + Deep Links | Ready with stale staging notifications | يوجد إشعاران high priority قديمان. |
| Follow-up Dashboard | Ready | read-only. |
| Reports | Ready | read-only. |
| Admin Settings | Ready | non-secret settings only. |

## Remaining Backlog

| Finding | Count | Classification | Recommendation |
| --- | ---: | --- | --- |
| Failed order ERP sync artifacts | 4 | staging cleanup required / acceptable staging residue | لا تطلق production من staging data؛ نظف أو وثق كاستثناء staging فقط. |
| Invoice sync failures | 0 | clear | لا إجراء. |
| Payment sync failures | 0 | clear | لا blocker بعد R11-T13. |
| Accounting needs attention | 1 | staging cleanup required / business-accounting decision | مرتبط بسجل test failure `MADAR-ORD-2026-00062`. راجعه أو وثقه كاستثناء. |
| Cashboxes waiting review | 0 | clear | لا إجراء. |
| High-priority unread notifications | 2 | acceptable staging residue / cleanup optional | إشعارات قديمة لفشل `MADAR-PAY-2026-00012` قبل الحل. يمكن تعليمها كمقروءة بموافقة. |

## Risk Assessment

### مخاطر عالية قبل الإنتاج

- Production secrets/users/domain/SSL لم يتم تنفيذها ضمن هذه المهمة.
- Production chart of accounts وMode of Payment mappings تحتاج اعتماد محاسب.
- External encrypted backup غير مؤكد.
- Monitoring/alerting لم يتم تركيبه كخدمة دورية أو أداة خارجية.
- Release tag النهائي بعد R11 fixes/docs لم يتم إنشاؤه بعد.

### مخاطر متوسطة

- Staging يحتوي artifacts تاريخية تؤدي إلى CRITICAL في monitoring.
- `madar-restore-test.localhost` ما زال موجودًا ويحتاج قرار keep/drop.
- Flutter web deployment path يحتاج توثيق نهائي إذا كان منفصلًا عن Frappe app checkout.

### مخاطر منخفضة

- `madar.egg-info/` غير متتبع على staging. لا يؤثر على tracked commit، لكنه يستحق cleanup لاحقًا في نافذة صيانة.

## التوصية

**CONDITIONAL GO**

الإطلاق ممكن فقط بعد تنفيذ الشروط التالية وتوثيق نتيجتها:

1. إنشاء release tag نهائي من commit معتمد يتضمن:
   - backend payment entry exchange-rate fix.
   - documentation/readiness reports أو قرار واضح أن tag runtime فقط.
2. تجهيز production environment:
   - domain وSSL.
   - site/database منفصلان.
   - no staging credentials.
   - no dev bootstrap.
3. تعطيل أو حذف test/dev users في production.
4. تدوير/تعيين credentials production:
   - Administrator.
   - SSH/root access.
   - database.
   - ERP API keys إن وجدت.
5. اعتماد production ERP configuration مع المحاسب:
   - Company.
   - customers/items/accounts.
   - Modes of Payment accounts.
   - Sales Invoice/Payment Entry submit policy.
6. توفير external encrypted backups وrestore procedure.
7. تفعيل monitoring/alert ownership.
8. تشغيل full backend/flutter verification suite قبل tag/deploy.
9. تنفيذ smoke test production بعد deploy وقبل فتح النظام للمستخدمين.
10. اتخاذ قرار بشأن staging residues:
    - cleanup workflow منفصل، أو
    - توثيقها كاستثناءات staging فقط.

## No-Go Conditions

يجب اعتبار الإنتاج **NO-GO** إذا تحقق أي مما يلي قبل الإطلاق:

- production payment method mappings غير معتمدة محاسبيًا.
- dev bootstrap مفعل في production.
- production backup/restore غير جاهز.
- security scan يفشل.
- full test/build gate يفشل.
- accounting.finalize ممنوحة لمستخدمين غير مصرح لهم.
- health endpoint لا يعمل.
- توجد ERP sync failures غير مفسرة في production trial.

## الخلاصة

Madar MVP جاهز وظيفيًا على مستوى staging، وتم حل blocker مزامنة الدفع الأخير. لكن الجاهزية الإنتاجية ليست GO مطلقًا بعد؛ هي **CONDITIONAL GO** مرتبطة بإكمال خطوات production operationalization: release tag النهائي، secrets/users/domain/SSL، backup خارجي، monitoring فعلي، اعتماد الحسابات الإنتاجية، وتنظيف أو توثيق staging artifacts.

تمت هذه المراجعة بدون أي تعديل بيانات، وبدون إنشاء أو إرسال ERP documents، وبدون لمس production.
