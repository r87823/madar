# تقرير فحص وإصلاح حقول سعر الصرف في Payment Entry

## الملخص

- التاريخ: 2026-05-21
- البيئة: staging فقط
- الموقع: `hrms.localhost`
- الخادم: `root@46.202.154.140`
- الحاوية: `docker-frappe-1`
- الهدف: فحص خطأ `سعر الصرف المستهدف إلزامي` عند مزامنة `MADAR-PAY-2026-00012`.
- النتيجة: تم إصلاح payload في كود Madar ليضيف حقول العملات وسعر الصرف عندما تكون آمنة، لكن الدفع لم تتم مزامنته لأن حساب الدفع لـ `Card` غير محسوم في ERPNext.

## حدود التنفيذ

لم يتم:

- لمس production.
- إرسال Payment Entry.
- إنشاء Sales Invoice.
- إنشاء GL Entry.
- إنشاء Delivery Note أو Stock Entry.
- تغيير accounting finalization behavior.
- تخمين أي account mapping محاسبي.
- تنفيذ cleanup أو حذف بيانات.

تم تشغيل `bench restart` على staging فقط بعد نشر تعديل Python runtime.

## نسخة الكود

تم نشر commit التالي على staging:

```text
445387c fix: add payment entry exchange rates
```

## الخطأ قبل التحقيق

بعد R11-T09، كان retry الدفع يفشل برسالة آمنة:

```text
سعر الصرف المستهدف إلزامي
```

الدفع المتأثر:

| Payment | Order | Method | Amount | Status |
| --- | --- | --- | ---: | --- |
| `MADAR-PAY-2026-00012` | `MADAR-ORD-2026-00066` | card | 100.0 | failed |

## التحقيق

تم فحص payload الحالي قبل التعديل، وكانت الحقول التالية مفقودة:

- `paid_from_account_currency`
- `paid_to_account_currency`
- `source_exchange_rate`
- `target_exchange_rate`

كما أظهر فحص `Payment Entry` metadata في staging أن الحقول التالية required:

- `company`
- `paid_from`
- `paid_from_account_currency`
- `paid_to`
- `paid_to_account_currency`
- `source_exchange_rate`
- `target_exchange_rate`

سياق العملة:

| الحقل | القيمة |
| --- | --- |
| Company | `test` |
| Company currency | `SAR` |
| Sales Order | `SAL-ORD-2026-00004` |
| Sales Order currency | `SAR` |
| Sales Order conversion rate | 1.0 |

فحص الحسابات أظهر:

- يوجد حساب receivable: `1310 - مدينون - T`
- يوجد حساب cash: `1110 - نقد - T`
- لا يوجد Bank account واضح أو `Mode of Payment Account` لـ `Card`
- `Mode of Payment Account` الموجود كان لـ `Cash` فقط

## السبب الجذري

السبب المباشر لخطأ exchange rate:

- Madar كان ينشئ payload لـ `Payment Entry` بدون حقول exchange rate/account currency المطلوبة في ERPNext v17 staging.

السبب المتبقي بعد إصلاح exchange fields:

- طريقة الدفع `Card` تحتاج حساب receiving account (`paid_to`) أو Mode of Payment Account مناسب.
- لا يوجد حساب Bank آمن يمكن اختياره تلقائيًا على staging.
- لذلك لا يجوز لـ Madar تخمين حساب محاسبي.

## التعديل المطبق في الكود

تم تحديث:

- `madar/services/payment_erp_sync_service.py`
- `madar/tests/test_payment_erp_sync_service.py`

السلوك الجديد:

1. عند تحضير Payment Entry payload، يحاول Madar تحديد:
   - `paid_from_account_currency`
   - `paid_to_account_currency`
   - `source_exchange_rate`
   - `target_exchange_rate`
2. إذا كانت عملة الحسابين تساوي عملة الشركة، يضبط:

```text
source_exchange_rate = 1.0
target_exchange_rate = 1.0
```

3. إذا لم يتم تحديد حسابات الدفع بأمان، يرجع خطأ آمن:

```text
ERP_PAYMENT_ACCOUNT_UNRESOLVED
تعذر تحديد حسابات سند الدفع في ERP. راجع إعدادات الحسابات وطرق الدفع.
```

4. إذا كانت العملة غير محسومة أو مختلفة عن عملة الشركة، يرجع خطأ آمن:

```text
ERP_PAYMENT_CURRENCY_UNRESOLVED
```

## نتيجة التحقق على staging

بعد نشر الكود الجديد، تم فحص payload لـ `MADAR-PAY-2026-00012`.

النتيجة:

```json
{
  "ok": false,
  "error": {
    "code": "ERP_PAYMENT_ACCOUNT_UNRESOLVED",
    "message": "تعذر تحديد حسابات سند الدفع في ERP. راجع إعدادات الحسابات وطرق الدفع."
  }
}
```

لم يتم تنفيذ retry فعلي بعد هذا الفحص، لأن الإنشاء غير آمن بدون account mapping.

حالة الدفع في قاعدة بيانات staging بقيت:

| Payment | erp_sync_status | erp_payment_entry | safe stored error |
| --- | --- | --- | --- |
| `MADAR-PAY-2026-00012` | failed | empty | `سعر الصرف المستهدف إلزامي` |

ملاحظة: لم يتم تحديث الخطأ المخزن حتى لا ننشئ إشعارات فشل جديدة أو mutations إضافية بعد اكتشاف blocker غير آمن.

## عدادات ERP قبل/بعد

| DocType | قبل | بعد |
| --- | ---: | ---: |
| GL Entry | 4 | 4 |
| Delivery Note | 0 | 0 |
| Stock Entry | 0 | 0 |
| Sales Invoice | 3 | 3 |
| Payment Entry | 2 | 2 |

لم يتم إنشاء أي Payment Entry جديد. ولم يتم إرسال أي مستند ERP.

## الاختبارات

تمت إضافة/تحديث اختبارات تغطي:

- same-currency payment payload includes exchange rate fields.
- missing payment account returns safe error before creating Payment Entry.
- sync creates Draft Payment Entry only when accounts/currencies are safe.
- raw ERP errors are not exposed.

أوامر التحقق المحلية التي نجحت:

```bash
python3 -m unittest discover -s madar/tests
PYTHONPYCACHEPREFIX=/private/tmp/madar_pycache python3 -m compileall -q madar setup.py scripts/check_security_rules.py scripts/monitoring/check_erp_sync_status.py
git diff --check
python3 scripts/check_security_rules.py
```

## التوصية قبل production

قبل إعادة محاولة `MADAR-PAY-2026-00012` أو أي payment sync بالبطاقات:

1. على staging، راجع مع المحاسب إعدادات `Mode of Payment Account` لـ:
   - `Card`
   - `Bank Transfer`
   - `Online`
2. أنشئ أو اربط حساب Bank مناسب لكل طريقة دفع حسب سياسة الشركة.
3. تأكد أن حسابات `paid_to` لها `account_currency = SAR` أو تعامل مع exchange rate رسمي إذا اختلفت العملة.
4. بعد ذلك فقط نفذ retry payment sync في مهمة منفصلة.
5. كرر نفس التحقق على production قبل go-live.

## الخلاصة

تم حل جزء exchange-rate في كود Madar بشكل آمن ومختبر. لم تتم مزامنة `MADAR-PAY-2026-00012` لأن blocker الحقيقي التالي هو غياب account mapping آمن لـ `Card`. لم يتم إنشاء Payment Entry أو GL Entry، ولم يتم لمس production.
