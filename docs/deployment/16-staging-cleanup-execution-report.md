# تقرير تنفيذ تنظيف staging المعتمد

## الملخص

- التاريخ: 2026-05-21
- البيئة: staging فقط
- الموقع: `hrms.localhost`
- الخادم: `root@46.202.154.140`
- الحاوية: `docker-frappe-1`
- النطاق: cleanup معتمد ومحدود عبر خدمات Madar/Frappe
- النتيجة العامة: تم اعتماد cashbox الاختباري وتعليم إشعاري cashbox كمقروءين. فشل retry الدفع بسبب خطأ إعداد ERP إضافي، ولم يتم إنشاء Payment Entry.

## حدود التنفيذ

لم يتم:

- لمس production.
- حذف أي سجلات.
- تنفيذ direct DB delete.
- تشغيل migrate أو restart.
- تعديل منطق التطبيق.
- إنشاء Delivery Note أو Stock Entry.
- إنشاء Sales Invoice.
- إنشاء GL Entry.
- إرسال Payment Entry.
- إسقاط `madar-restore-test.localhost`.

## نسخة التطبيق على staging

داخل `/home/frappe/frappe-bench/apps/madar`:

```text
c2f8854 docs: add restore drill report
?? madar.egg-info/
```

لم يتم تعديل أو حذف `madar.egg-info/`.

## Health check

قبل وبعد التنفيذ:

```text
OK health_check ok=true app=madar
```

## العدادات قبل التنفيذ

### عدادات ERP الحساسة

| DocType | قبل |
| --- | ---: |
| GL Entry | 4 |
| Delivery Note | 0 |
| Stock Entry | 0 |
| Sales Invoice | 3 |
| Payment Entry | 2 |

### monitoring backlog قبل التنفيذ

```text
order_erp_sync_failed=4
order_invoice_sync_failed=0
payment_erp_sync_failed=1
accounting_needs_attention=1
cashboxes_waiting_review=1
high_priority_unread_notifications=2
```

## الإجراءات المعتمدة والمنفذة

### 1. Retry payment sync لـ `MADAR-PAY-2026-00012`

قبل التنفيذ:

| Payment | Order | Amount | Method | Status | ERP sync | ERP Payment Entry | Safe error |
| --- | --- | ---: | --- | --- | --- | --- | --- |
| `MADAR-PAY-2026-00012` | `MADAR-ORD-2026-00066` | 100.0 | card | collected | failed | empty | `لا يمكن أن تجد طريقة الدفع: Card` |

الإجراء:

- تم استدعاء `madar.services.payment_erp_sync_service.retry_payment_sync`.
- المستخدم التشغيلي: `accountant.test@example.com`.
- لم يتم direct DB update.

النتيجة:

| Payment | ERP sync | ERP Payment Entry | docstatus | Safe error after retry |
| --- | --- | --- | ---: | --- |
| `MADAR-PAY-2026-00012` | failed | empty | 0 | `سعر الصرف المستهدف إلزامي` |

لم يتم إنشاء `Payment Entry`. بقيت عدادات `Payment Entry` عند 2.

التصنيف بعد التنفيذ:

- `Mode of Payment: Card` لم يعد blocker.
- يوجد blocker جديد لإعداد ERP/payment entry: `target exchange rate` مطلوب.
- لا يتم retry مرة أخرى بدون مهمة منفصلة ومراجعة إعدادات ERP المحاسبية.

### 2. اعتماد cashbox الاختباري

قبل التنفيذ:

| Cashbox | User | Status | Expected | Submitted | Difference |
| --- | --- | --- | ---: | ---: | ---: |
| `MADAR-CASHBOX-2026-00004` | `cashier.test@example.com` | submitted | 100.0 | 100.0 | 0.0 |

الإجراء:

- تم استدعاء `madar.services.cashbox_service.approve_cashbox`.
- المستخدم التشغيلي: `accountant.test@example.com`.
- لم يتم إنشاء ERP Payment Entry من cashbox.

بعد التنفيذ:

| Cashbox | Status | Reviewed by | Reviewed at | Difference |
| --- | --- | --- | --- | ---: |
| `MADAR-CASHBOX-2026-00004` | approved | `accountant.test@example.com` | 2026-05-21 16:28:04 | 0.0 |

نتيجة monitoring:

```text
cashboxes_waiting_review=0
```

### 3. تعليم إشعارات cashbox الاختبارية كمقروءة

الإشعارات المعتمدة:

| Notification | Recipient | Event | Entity | Before | After |
| --- | --- | --- | --- | --- | --- |
| `MADAR-NOTIF-2026-00003` | `cashier.test@example.com` | cashbox_returned | `MADAR-CASHBOX-2026-00005` | unread | read |
| `MADAR-NOTIF-2026-00006` | `cashier.test@example.com` | cashbox_returned | `MADAR-CASHBOX-2026-00006` | unread | read |

الإجراء:

- تم استدعاء `madar.services.notification_service.mark_read`.
- لم يتم حذف الإشعارات.

ملاحظة:

بعد فشل retry payment sync، أنشأت خدمة Madar إشعارين جديدين لفشل ERP sync:

| Notification | Recipient | Event | Entity |
| --- | --- | --- | --- |
| `MADAR-NOTIF-2026-00007` | `accountant.test@example.com` | erp_sync_failed | `MADAR-PAY-2026-00012` |
| `MADAR-NOTIF-2026-00008` | `no.attendance.test@example.com` | erp_sync_failed | `MADAR-PAY-2026-00012` |

لم يتم تعليم هذين الإشعارين كمقروءين لأنهما ليسا ضمن إشعارات cashbox الاختبارية المعتمدة، ولأنهما يمثلان نتيجة workflow حالية لفشل ERP sync.

## العدادات بعد التنفيذ

### عدادات ERP الحساسة

| DocType | قبل | بعد | النتيجة |
| --- | ---: | ---: | --- |
| GL Entry | 4 | 4 | unchanged |
| Delivery Note | 0 | 0 | unchanged |
| Stock Entry | 0 | 0 | unchanged |
| Sales Invoice | 3 | 3 | unchanged |
| Payment Entry | 2 | 2 | unchanged |

### monitoring backlog بعد التنفيذ

```text
order_erp_sync_failed=4
order_invoice_sync_failed=0
payment_erp_sync_failed=1
accounting_needs_attention=1
cashboxes_waiting_review=0
high_priority_unread_notifications=2
```

التحسن:

- `cashboxes_waiting_review`: من 1 إلى 0.
- إشعارا cashbox الأصليان أصبحا read.

المتبقي:

- `payment_erp_sync_failed=1` بسبب `MADAR-PAY-2026-00012`.
- `high_priority_unread_notifications=2` بسبب إشعارات جديدة لفشل payment sync.
- failed order sync artifacts الأربعة لم يتم لمسها حسب التعليمات.
- `accounting_needs_attention=1` بقي مرتبطًا بسجل اختبار R6T05.

## السجلات غير المحلولة

| العنصر | الحالة | التوصية |
| --- | --- | --- |
| `MADAR-PAY-2026-00012` | ERP payment sync failed | راجع إعدادات ERP الخاصة بسعر الصرف أو العملة وحسابات الدفع قبل retry جديد. |
| `MADAR-NOTIF-2026-00007` | unread high priority | اتركه كمؤشر لفشل sync الحالي أو عالجه بعد حل payment sync. |
| `MADAR-NOTIF-2026-00008` | unread high priority | تحقق لماذا مستخدم `no.attendance.test@example.com` لديه صلاحية accounting sync notification إن لم يكن ذلك مقصودًا. |
| failed order sync artifacts الأربعة | unchanged | موثقة كـ staging test artifacts؛ لا retry بدون موافقة منفصلة. |
| `MADAR-ORD-2026-00062` accounting needs_attention | unchanged | موثق كسجل R6T05 test artifact. |

## حالة موقع الاستعادة

تم التحقق أن موقع الاستعادة ما زال موجودًا:

```text
madar-restore-test.localhost: EXISTS
```

لم يتم حذفه أو تعديله.

## الخلاصة

تم تنفيذ cleanup المعتمد جزئيًا وبأمان:

- تم اعتماد cashbox الاختباري عبر خدمة Madar.
- تم تعليم إشعاري cashbox الاختباريين كمقروءين عبر خدمة Madar.
- لم يتم إنشاء أي مستند ERP أو GL Entry.
- لم ينجح retry payment sync بسبب إعداد ERP إضافي مطلوب، ولم ينشئ Payment Entry.

قبل production readiness، يلزم حل blocker الجديد الخاص بـ `MADAR-PAY-2026-00012`:

```text
سعر الصرف المستهدف إلزامي
```

ويجب مراجعة recipients لإشعارات `erp_sync_failed` لأن أحدها وصل إلى `no.attendance.test@example.com`.
