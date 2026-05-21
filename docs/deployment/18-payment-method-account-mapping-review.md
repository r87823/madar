# مراجعة ربط حسابات طرق الدفع في ERP

## الملخص

- التاريخ: 2026-05-21
- البيئة: staging فقط
- الموقع: `hrms.localhost`
- النطاق: read-only review فقط
- السبب: `MADAR-PAY-2026-00012` ما زال غير قابل للمزامنة بسبب `ERP_PAYMENT_ACCOUNT_UNRESOLVED`.
- النتيجة: فجوة account mapping مؤكدة لـ `Card`, `Bank Transfer`, و`Online`. لا يوجد حساب Bank واضح في شركة staging يمكن اختياره بأمان.

## حدود المراجعة

لم يتم:

- إنشاء أو تعديل `Mode of Payment Account`.
- إنشاء Payment Entry.
- إرسال Payment Entry.
- إنشاء GL Entry.
- retry لأي payment sync.
- لمس production.
- تخمين أي حساب محاسبي.

## الصحة العامة

تم تشغيل health check:

```text
OK health_check ok=true app=madar
```

## الشركة والعملات

| Company | Default currency |
| --- | --- |
| `test` | `SAR` |

## طرق الدفع الحالية

| Mode of Payment | enabled | type | الحالة |
| --- | ---: | --- | --- |
| `Bank Transfer` | 1 | Bank | موجود |
| `Card` | 1 | Bank | موجود |
| `Cash` | 1 | Cash | موجود |
| `Online` | 1 | Bank | موجود |

## ربط الحسابات الحالي

| Mode of Payment | Company | Default account |
| --- | --- | --- |
| `Cash` | `test` | `1110 - نقد - T` |

لا توجد صفوف `Mode of Payment Account` للطرق التالية:

- `Card`
- `Bank Transfer`
- `Online`

## الحسابات المرشحة المتاحة

تم فحص الحسابات غير المجموعة في الشركة `test` من الأنواع:

- Cash
- Bank
- Receivable

النتيجة:

| Account | Account type | Currency | ملاحظة |
| --- | --- | --- | --- |
| `1110 - نقد - T` | Cash | SAR | مستخدم حاليًا لـ `Cash`. |
| `1310 - مدينون - T` | Receivable | SAR | حساب ذمم/عملاء، وليس حساب تحصيل بطاقة أو بنك. |

لا يوجد حساب من نوع `Bank` في الشركة `test`.

## حالة الدفع المتأثر

| Payment | Order | Method | ERP sync status | Safe error |
| --- | --- | --- | --- | --- |
| `MADAR-PAY-2026-00012` | `MADAR-ORD-2026-00066` | card | failed | `سعر الصرف المستهدف إلزامي` |

بعد R11-T10، أصبح كود Madar قادرًا على إرجاع blocker أدق قبل إنشاء Payment Entry:

```text
ERP_PAYMENT_ACCOUNT_UNRESOLVED
تعذر تحديد حسابات سند الدفع في ERP. راجع إعدادات الحسابات وطرق الدفع.
```

لكن لم يتم تحديث هذا السجل أو retry في هذه المراجعة لأنها read-only.

## فجوة الإعداد

مطلوب من المحاسب تحديد حسابات التحصيل الافتراضية لكل طريقة دفع بنوع `Bank`:

| Mode of Payment | الوضع الحالي | القرار المطلوب |
| --- | --- | --- |
| `Card` | لا يوجد default account | تحديد/إنشاء حساب Bank مناسب لتحصيل البطاقة وربطه. |
| `Bank Transfer` | لا يوجد default account | تحديد/إنشاء حساب Bank مناسب للتحويلات وربطه. |
| `Online` | لا يوجد default account | تحديد/إنشاء حساب Bank/online settlement مناسب وربطه. |

## لماذا لا يجب التخمين؟

- `Payment Entry` يؤثر على accounting representation حتى لو بقي Draft.
- اختيار حساب خاطئ قد يسبب قيودًا خاطئة عند submit لاحقًا.
- staging لا يحتوي حساب `Bank` واضح يمكن استخدامه كمرشح آمن.
- الحساب `1310 - مدينون - T` هو receivable وليس حساب تحصيل.

## خيارات الإصلاح اللاحق

### الخيار A: إنشاء حسابات Bank واضحة

ينفذ فقط بموافقة المحاسب:

- إنشاء حساب Bank/settlement لكل طريقة دفع أو حساب واحد مشترك حسب سياسة الشركة.
- ربطه في `Mode of Payment Account`.
- إعادة فحص payload.
- retry `MADAR-PAY-2026-00012`.

### الخيار B: ربط الطرق بحساب Bank موجود

غير متاح حاليًا على staging لأن الفحص لم يجد حساب `Bank`.

### الخيار C: ترك السجل كاستثناء staging

مقبول فقط إذا بقي `MADAR-PAY-2026-00012` artifact اختبار، لكنه لا يحل readiness لفحص payment sync بالبطاقات.

## نقاط الموافقة المطلوبة قبل أي تعديل

قبل تنفيذ mapping في R11-T12 أو مهمة لاحقة:

- موافقة المحاسب على أسماء الحسابات.
- موافقة على إنشاء أي Account جديد إذا لم يوجد حساب Bank.
- موافقة على ربط `Mode of Payment Account`.
- موافقة قبل retry `MADAR-PAY-2026-00012`.
- تسجيل ERP counts قبل/بعد.

## التوصية

لا تنفذ retry جديد لـ `MADAR-PAY-2026-00012` قبل أحد القرارين:

1. إنشاء/اعتماد حساب Bank في الشركة `test` وربطه بـ `Card`.
2. توثيق أن payment card sync لن يختبر على staging الحالي، وهذا غير مفضل قبل production readiness.

لـ production:

- يجب تكرار هذه المراجعة على production قبل go-live.
- لا تنسخ حسابات staging تلقائيًا.
- يجب أن يراجع المحاسب الحسابات قبل أي final submit أو go-live.

## الخلاصة

الفجوة الحالية ليست في كود exchange rate بعد R11-T10، بل في إعدادات ERP account mapping. `Cash` فقط مربوط بحساب. طرق `Card`, `Bank Transfer`, و`Online` تحتاج قرارًا محاسبيًا لحساب Bank/settlement قبل retry آمن أو قبل اعتبار payment sync جاهزًا للإنتاج.
