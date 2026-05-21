# تقرير مراجعة backlog التشغيلي على staging

## الملخص

- التاريخ: 2026-05-21
- البيئة: staging فقط
- المشغل: Codex
- الخادم: `root@46.202.154.140`
- الحاوية: `docker-frappe-1`
- الموقع النشط: `hrms.localhost`
- الرابط العام: `https://madar-test.r8787m.cc`
- مسار bench: `/home/frappe/frappe-bench`
- نطاق المهمة: read-only inspection فقط
- النتيجة: تم توثيق backlog الحالي بدون تعديل أي بيانات.

## نسخة staging أثناء الفحص

داخل `/home/frappe/frappe-bench/apps/madar`:

```text
c2f8854 docs: add restore drill report
```

ملاحظة: يوجد ملف مولد غير متتبع على الخادم:

```text
?? madar.egg-info/
```

لم يتم حذفه أو تعديله.

## صحة الموقع

تم تشغيل:

```bash
scripts/monitoring/check_staging_health.sh
```

النتيجة:

```text
OK health_check ok=true app=madar
```

## ملخص العدادات

تم تشغيل سكربت monitoring read-only:

```bash
python3 scripts/monitoring/check_erp_sync_status.py \
  --bench-path /home/frappe/frappe-bench \
  --site hrms.localhost
```

النتيجة:

```text
CRITICAL order_erp_sync_failed=4 order_invoice_sync_failed=0 payment_erp_sync_failed=1 accounting_needs_attention=1 cashboxes_waiting_review=1 high_priority_unread_notifications=2
```

هذه العدادات موجودة مسبقًا في staging، وليست نتيجة لهذه المراجعة.

## عدادات ERP الحساسة قبل/بعد

| DocType | قبل | بعد |
| --- | ---: | ---: |
| GL Entry | 4 | 4 |
| Delivery Note | 0 | 0 |
| Stock Entry | 0 | 0 |
| Sales Invoice | 3 | 3 |
| Payment Entry | 2 | 2 |

لم تتغير أي عدادات ERP حساسة أثناء المراجعة.

## 1. أوامر Madar بفشل ERP Sales Order sync

العدد: 4

| Madar Order | العميل | الحالة | ERP sync | ملخص الخطأ الآمن | ERP Sales Order | الإنشاء | آخر تعديل | التصنيف | الإجراء المقترح |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `MADAR-ORD-2026-00062` | `R6T05 Customer FAILED` | approved | failed | `safe failure` | `SAL-ORD-R6T05-FAILED` | 2026-05-20 13:05:58 | 2026-05-20 13:05:58 | expected test artifact + needs cleanup before production | تأكيد أنه سجل اختبار R6-T05 ثم تنظيفه أو عزله قبل الإنتاج. |
| `MADAR-ORD-2026-00023` | `R3T05 Sync Customer 1779181839` | approved | failed | `لا يمكن أن تجد العميل: R3T05 Sync Customer 1779181839` | empty | 2026-05-19 12:10:53 | 2026-05-19 12:11:12 | expected test artifact + needs cleanup before production | سجل اختبار ERP sync بعميل غير موجود؛ لا تعيد المزامنة قبل تحديد سياسة تنظيف بيانات staging. |
| `MADAR-ORD-2026-00021` | `R3T05 Sync Customer 1779181784` | approved | failed | `لا يمكن أن تجد العميل: R3T05 Sync Customer 1779181784` | empty | 2026-05-19 12:09:57 | 2026-05-19 12:10:18 | expected test artifact + needs cleanup before production | سجل اختبار ERP sync بعميل غير موجود؛ لا تعيد المزامنة قبل تحديد سياسة تنظيف بيانات staging. |
| `MADAR-ORD-2026-00019` | `R3T05 Sync Customer 1779181734` | approved | failed | `لا يمكن أن تجد العميل: R3T05 Sync Customer 1779181734` | empty | 2026-05-19 12:09:10 | 2026-05-19 12:09:29 | expected test artifact + needs cleanup before production | سجل اختبار ERP sync بعميل غير موجود؛ لا تعيد المزامنة قبل تحديد سياسة تنظيف بيانات staging. |

### ملاحظة

الأخطاء لا تحتوي tracebacks كاملة في التقرير. تم توثيق ملخصات آمنة فقط.

## 2. أوامر Madar بفشل Sales Invoice sync

العدد: 0

لا توجد أوامر بحالة `erp_invoice_sync_status=failed`.

## 3. مدفوعات Madar بفشل ERP Payment Entry sync

العدد: 1

| Payment | Madar Order | المبلغ | الطريقة | ERP sync | ملخص الخطأ الآمن | ERP Payment Entry | التصنيف | الإجراء المقترح |
| --- | --- | ---: | --- | --- | --- | --- | --- | --- |
| `MADAR-PAY-2026-00012` | `MADAR-ORD-2026-00066` | 100.0 | card | failed | `لا يمكن أن تجد طريقة الدفع: Card` | empty | needs manual review + potential configuration issue | راجع إعدادات `Mode of Payment` في ERPNext لبطاقات الدفع قبل الإنتاج، أو وثق mapping مختلف بين Madar وERP. لا تعمل retry في هذه المهمة. |

## 4. أوامر تحتاج انتباه محاسبي

العدد: 1

| Madar Order | العميل | payment_status | delivery_status | ملاحظات المراجعة | المراجع | وقت المراجعة | التصنيف | الإجراء المقترح |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `MADAR-ORD-2026-00062` | `R6T05 Customer FAILED` | paid | customer_picked_up | `راجع فشل المزامنة` | `accountant.test@example.com` | 2026-05-20 13:05:58 | expected test artifact + needs cleanup before production | مرتبط بسجل اختبار R6-T05. قرر هل سيحذف/يعزل ضمن خطة تنظيف staging قبل الإنتاج. |

## 5. صناديق بانتظار المراجعة

العدد: 1

| Cashbox | المستخدم | التاريخ | expected_cash | submitted_cash | الفرق | submitted_at | التصنيف | الإجراء المقترح |
| --- | --- | --- | ---: | ---: | ---: | --- | --- | --- |
| `MADAR-CASHBOX-2026-00004` | `cashier.test@example.com` | 2026-05-20 | 100.0 | 100.0 | 0.0 | 2026-05-20 13:05:58 | expected test artifact + needs cleanup before production | لا تعتمد الصندوق في هذه المهمة. راجعه ضمن تمرين تنظيف staging أو احذف بيانات الاختبار بعد موافقة صريحة. |

## 6. إشعارات عالية الأولوية غير مقروءة

العدد: 2

| Notification | المستلم | العنوان | event_type | entity_type | entity_name | الإنشاء | التصنيف | الإجراء المقترح |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `MADAR-NOTIF-2026-00006` | `cashier.test@example.com` | تم إرجاع الصندوق | cashbox_returned | Madar Cashbox | `MADAR-CASHBOX-2026-00006` | 2026-05-20 18:24:38 | expected test artifact + needs cleanup before production | لا تعمل mark-read في هذه المهمة. نظف أو اترك حسب سياسة بيانات staging. |
| `MADAR-NOTIF-2026-00003` | `cashier.test@example.com` | تم إرجاع الصندوق | cashbox_returned | Madar Cashbox | `MADAR-CASHBOX-2026-00005` | 2026-05-20 17:17:28 | expected test artifact + needs cleanup before production | لا تعمل mark-read في هذه المهمة. نظف أو اترك حسب سياسة بيانات staging. |

لم يتم توثيق `route_params_json` لتجنب إدراج تفاصيل غير ضرورية.

## التصنيف العام

| الفئة | السجلات | التقييم |
| --- | --- | --- |
| expected test artifact | أوامر R3T05/R6T05، cashbox/notification لمستخدمين test | أغلب backlog يبدو ناتجًا عن اختبارات staging المقصودة. |
| needs manual review | `MADAR-PAY-2026-00012` | فشل payment sync بسبب `Mode of Payment: Card` يحتاج مراجعة إعدادات ERP. |
| needs cleanup before production | كل السجلات المذكورة إذا كانت production readiness تقاس على staging نظيف | يجب وضع خطة تنظيف staging منفصلة وبموافقة صريحة. |
| potential bug | لا يوجد دليل حاسم | فشل Card يبدو أقرب إلى إعداد ERP/mapping من كونه bug، لكنه يستحق تحققًا قبل الإنتاج. |

## التوصيات

1. لا تعتبر staging جاهزًا كمؤشر مراقبة نظيف حتى تصبح عدادات sync/backlog صفرية أو موثقة كاستثناءات مقبولة.
2. نفذ مهمة منفصلة لتنظيف بيانات staging الاختبارية، مع موافقة صريحة لأنها ستكون destructive أو mutation.
3. راجع إعدادات ERPNext `Mode of Payment` للتأكد من وجود أو mapping طريقة الدفع `Card`.
4. حدد سياسة واضحة لسجلات الاختبار قبل الإنتاج: حذف، أرشفة، أو إبقاؤها مع thresholds منفصلة.
5. بعد أي تنظيف أو إصلاح إعدادات، أعد تشغيل:

```bash
scripts/monitoring/check_staging_health.sh
python3 scripts/monitoring/check_erp_sync_status.py --bench-path /home/frappe/frappe-bench --site hrms.localhost
```

## ما لم يتم تنفيذه

- لم يتم retry لأي ERP sync.
- لم يتم approve لأي cashbox.
- لم يتم mark-read لأي notification.
- لم يتم submit لأي Sales Invoice أو Payment Entry.
- لم يتم create/modify/delete لأي ERP document.
- لم يتم حذف staging data.
- لم يتم تشغيل migrate.
- لم يتم restart للخدمات.
- لم يتم لمس production.

## حالة موقع الاستعادة

تم التحقق أن موقع الاستعادة ما زال موجودًا:

```text
madar-restore-test.localhost: EXISTS
```

لم يتم حذفه أو تعديله.

## خلاصة

تمت مراجعة backlog التشغيلي على staging بطريقة read-only. لا توجد تغييرات بيانات أو ERP mutations. النتائج الأساسية تبدو مرتبطة ببيانات اختبارات staging، مع نقطة إعداد/مراجعة واضحة لطريقة الدفع `Card` في ERPNext قبل الإنتاج.
