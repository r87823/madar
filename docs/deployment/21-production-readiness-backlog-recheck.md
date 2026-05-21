# تقرير إعادة فحص backlog قبل جاهزية الإنتاج

## الملخص

- التاريخ: 2026-05-21 17:36:10 +03
- البيئة: staging فقط
- الموقع: `hrms.localhost`
- الرابط العام: `https://madar-test.r8787m.cc`
- الخادم: `root@46.202.154.140`
- الحاوية: `docker-frappe-1`
- النطاق: read-only production readiness backlog recheck
- النتيجة الأساسية: backlog الخاص بـ `payment_erp_sync_failed` أصبح صفرًا بعد R11-T13.

## حدود الفحص

لم يتم:

- تنظيف أي بيانات.
- إعادة محاولة sync لأي سجل.
- إرسال Payment Entry.
- إرسال Sales Invoice.
- إنشاء GL Entry.
- اعتماد cashbox.
- تعليم notifications كمقروءة.
- حذف أي سجلات.
- تشغيل migrate أو restart.
- لمس production.

تم تنفيذ فحص read-only فقط عبر health endpoint واستعلامات Frappe/SQL للعدادات والحالة.

## صحة الموقع

```text
OK health_check ok=true app=madar
```

## نسخة تطبيق Madar على staging

داخل `/home/frappe/frappe-bench/apps/madar`:

```text
445387c fix: add payment entry exchange rates
?? madar.egg-info/
```

تم ترك `madar.egg-info/` كما هو، ولم يتم تعديله أو حذفه.

## عدادات monitoring الحالية

| المفتاح | العدد | التصنيف | الملاحظة |
| --- | ---: | --- | --- |
| `order_erp_sync_failed` | 4 | acceptable staging residue / needs manual cleanup | سجلات اختبارية تاريخية موثقة سابقًا. |
| `invoice_erp_sync_failed` | 0 | clear | لا توجد أخطاء invoice sync حاليًا. |
| `payment_erp_sync_failed` | 0 | clear | تم حل backlog الخاص بالدفع بعد R11-T13. |
| `accounting_needs_attention` | 1 | acceptable staging residue / needs manual cleanup | مرتبط بسجل اختبار فشل order sync. |
| `cashboxes_waiting_review` | 0 | clear | لا توجد cashboxes submitted بانتظار المراجعة. |
| `high_priority_unread_notifications` | 2 | acceptable staging residue | إشعارات قديمة لفشل `MADAR-PAY-2026-00012` قبل حل المشكلة. |

## عدادات ERP الحالية

| DocType | العدد |
| --- | ---: |
| GL Entry | 4 |
| Delivery Note | 0 |
| Stock Entry | 0 |
| Sales Invoice | 3 |
| Payment Entry | 3 |

لم ينتج عن هذا الفحص أي تغيير في العدادات، لأنه كان read-only.

## حالة `MADAR-PAY-2026-00012`

| الحقل | القيمة |
| --- | --- |
| Payment | `MADAR-PAY-2026-00012` |
| Madar Order | `MADAR-ORD-2026-00066` |
| Amount | 100.0 |
| Payment method | `card` |
| ERP sync status | `synced` |
| ERP sync error | empty |
| ERP Payment Entry | `ACC-PAY-2026-00006` |
| ERP Payment Entry docstatus on Madar Payment | 0 |

### مستند ERP Payment Entry

| الحقل | القيمة |
| --- | --- |
| Payment Entry | `ACC-PAY-2026-00006` |
| docstatus | 0 |
| mode_of_payment | `Card` |
| paid_amount | 100.0 |
| received_amount | 100.0 |

التأكيد: المستند بقي Draft ولم يتم submit.

## التفاصيل المتبقية

### Failed Madar Order ERP Sync

| Order | Customer | Status | Error summary | التصنيف |
| --- | --- | --- | --- | --- |
| `MADAR-ORD-2026-00062` | `R6T05 Customer FAILED` | approved | `safe failure` | test artifact / needs manual cleanup |
| `MADAR-ORD-2026-00023` | `R3T05 Sync Customer 1779181839` | approved | العميل غير موجود في ERP | test artifact / acceptable staging residue |
| `MADAR-ORD-2026-00021` | `R3T05 Sync Customer 1779181784` | approved | العميل غير موجود في ERP | test artifact / acceptable staging residue |
| `MADAR-ORD-2026-00019` | `R3T05 Sync Customer 1779181734` | approved | العميل غير موجود في ERP | test artifact / acceptable staging residue |

هذه السجلات لا تبدو production blockers للكود، لكنها تمنع monitoring من الوصول إلى حالة نظيفة على staging. تحتاج قرارًا منفصلًا: إما تنظيف workflow/test data أو توثيقها كاستثناء staging.

### Invoice Sync Failures

لا توجد سجلات `erp_invoice_sync_status=failed`.

### Payment Sync Failures

لا توجد سجلات `Madar Payment` بحالة `erp_sync_status=failed`.

### Accounting Needs Attention

| Order | Customer | Payment status | Delivery status | Notes | التصنيف |
| --- | --- | --- | --- | --- | --- |
| `MADAR-ORD-2026-00062` | `R6T05 Customer FAILED` | paid | customer_picked_up | راجع فشل المزامنة | test artifact / needs manual cleanup |

هذا مرتبط بسجل order sync test failure ويحتاج قرار cleanup منفصل قبل اعتبار staging نظيفًا.

### Cashboxes Waiting Review

لا توجد cashboxes بحالة `submitted`.

### High Priority Unread Notifications

| Notification | Recipient | Event | Entity | التصنيف |
| --- | --- | --- | --- | --- |
| `MADAR-NOTIF-2026-00008` | `no.attendance.test@example.com` | `erp_sync_failed` | `Madar Payment` / `MADAR-PAY-2026-00012` | stale test notification |
| `MADAR-NOTIF-2026-00007` | `accountant.test@example.com` | `erp_sync_failed` | `Madar Payment` / `MADAR-PAY-2026-00012` | stale test notification |

هذه الإشعارات مرتبطة بفشل الدفع قبل حله. لم يتم تعليمها كمقروءة في هذا الفحص حسب التعليمات.

## Remaining Blockers

### ليست blockers للكود

- `payment_erp_sync_failed=0` يؤكد أن blocker الخاص بـ `MADAR-PAY-2026-00012` تم حله.
- لا توجد invoice sync failures.
- لا توجد cashboxes waiting review.

### تحتاج cleanup أو استثناء staging قبل go-live readiness

- أربع سجلات `order_erp_sync_failed` تاريخية.
- سجل واحد `accounting_needs_attention` مرتبط بسجل order sync test failure.
- إشعاران high-priority unread قديمان مرتبطان بفشل payment sync الذي تم حله.

## التوصية التالية

1. تنفيذ مهمة منفصلة لتنظيف staging artifacts أو توثيق استثناءاتها:
   - معالجة أو عزل failed order sync test artifacts.
   - مراجعة `MADAR-ORD-2026-00062` وحالة accounting needs attention.
   - تعليم إشعارات `MADAR-PAY-2026-00012` القديمة كمقروءة عبر UI/API إذا تم اعتماد ذلك.
2. إعادة تشغيل monitoring بعد cleanup للتأكد من أن:
   - `order_erp_sync_failed=0` أو موثق كاستثناء.
   - `accounting_needs_attention=0` أو موثق كاستثناء.
   - `high_priority_unread_notifications=0` أو موثق كاستثناء.
3. عدم تنفيذ أي production go-live قبل اعتماد سياسة واضحة للتعامل مع staging residues.

## بيان عدم التعديل

هذا الفحص كان read-only. لم يتم تعديل بيانات staging، ولم يتم إنشاء أو إرسال أي ERP documents، ولم يتم لمس production.
