# تقرير إصلاح إعدادات طرق الدفع في ERP على staging

## الملخص

- التاريخ: 2026-05-21
- البيئة: staging فقط
- الموقع: `hrms.localhost`
- الخادم: `root@46.202.154.140`
- الحاوية: `docker-frappe-1`
- النطاق: ERP configuration فقط
- الهدف: التأكد من وجود `Mode of Payment` المطلوبة لمزامنة مدفوعات Madar.

## حدود التنفيذ

تم تعديل إعدادات ERPNext المرجعية فقط عبر DocType `Mode of Payment`.

لم يتم:

- retry لأي Madar Payment sync.
- إنشاء أو إرسال Payment Entry.
- إنشاء أو إرسال Sales Invoice.
- إنشاء GL Entry.
- إنشاء Delivery Note أو Stock Entry.
- تعديل workflows في Madar.
- تشغيل migrate أو restart.
- لمس production.
- حذف أي بيانات.
- اعتماد cashbox أو تعليم notifications كمقروءة.

## نسخة staging أثناء التنفيذ

داخل `/home/frappe/frappe-bench/apps/madar`:

```text
c2f8854 docs: add restore drill report
```

ملاحظة: بقي الملف المولد غير المتتبع كما هو:

```text
?? madar.egg-info/
```

لم يتم حذفه أو تعديله.

## Health check قبل/بعد

تم تشغيل:

```bash
scripts/monitoring/check_staging_health.sh
```

النتيجة بعد التنفيذ:

```text
OK health_check ok=true app=madar
```

## طرق الدفع المطلوبة

Madar mapping الحالي يتوقع وجود ERPNext `Mode of Payment` التالية:

| Madar method | ERPNext Mode of Payment |
| --- | --- |
| `cash` | `Cash` |
| `card` | `Card` |
| `transfer` | `Bank Transfer` |
| `online` | `Online` |

## حالة ما قبل التنفيذ

تم فحص السجلات المطلوبة في `Mode of Payment`.

| Mode of Payment | الحالة قبل |
| --- | --- |
| `Cash` | موجود |
| `Card` | مفقود |
| `Bank Transfer` | مفقود |
| `Online` | مفقود |

تم فحص metadata لـ DocType `Mode of Payment` قبل الإنشاء. الحقل الإلزامي الوحيد كان:

| fieldname | fieldtype | reqd |
| --- | --- | ---: |
| `mode_of_payment` | Data | 1 |

لذلك كان الإنشاء آمنًا بدون تخمين حسابات محاسبية أو account mappings.

## التنفيذ

تم استخدام Frappe ORM داخل `bench --site hrms.localhost console` بمنطق idempotent:

- إذا كان السجل موجودًا: لا يتم تعديله.
- إذا كان مفقودًا: يتم إنشاؤه بـ `enabled=1`.
- لا يتم إنشاء duplicates.
- لا يتم ضبط account mappings.

السجلات التي كانت موجودة:

- `Cash`

السجلات التي تم إنشاؤها:

- `Card`
- `Bank Transfer`
- `Online`

أنواع السجلات بعد الإنشاء:

| Mode of Payment | enabled | type |
| --- | ---: | --- |
| `Bank Transfer` | 1 | Bank |
| `Card` | 1 | Bank |
| `Cash` | 1 | Cash |
| `Online` | 1 | Bank |

## حالة ما بعد التنفيذ

| Mode of Payment | الحالة بعد |
| --- | --- |
| `Cash` | موجود |
| `Card` | موجود |
| `Bank Transfer` | موجود |
| `Online` | موجود |

## عدادات ERP الحساسة قبل/بعد

| DocType | قبل | بعد |
| --- | ---: | ---: |
| GL Entry | 4 | 4 |
| Delivery Note | 0 | 0 |
| Stock Entry | 0 | 0 |
| Sales Invoice | 3 | 3 |
| Payment Entry | 2 | 2 |

لم يتم إنشاء أي مستندات محاسبية أو مخزنية نتيجة هذا التغيير.

## ملاحظات تنفيذية

- محاولة تشغيل Python مباشرة داخل bench env فشلت قبل أي mutation بسبب مسار logging خارج سياق bench المناسب.
- تم تنفيذ الإنشاء بعد ذلك عبر `bench --site hrms.localhost console`، وهو السياق الصحيح لـ Frappe.
- لا توجد أسرار أو كلمات مرور في هذا التقرير.
- لم يتم توثيق raw tracebacks.

## أثر ذلك على backlog

هذا التغيير يعالج سبب فشل payment sync المرتبط برسالة:

```text
لا يمكن أن تجد طريقة الدفع: Card
```

لكن لم يتم retry لـ `MADAR-PAY-2026-00012` ضمن هذه المهمة. لذلك قد يبقى `payment_erp_sync_failed=1` حتى تنفيذ مهمة لاحقة توافق صراحة على retry.

## توصيات production

قبل go-live:

1. تحقق من وجود السجلات التالية في production ERPNext:
   - `Cash`
   - `Card`
   - `Bank Transfer`
   - `Online`
2. راجع `type` وaccount mappings مع المحاسب إذا كانت سياسة ERPNext أو إعدادات الشركة تتطلب حسابات افتراضية.
3. لا تعتمد على staging كمصدر تلقائي لإعداد production؛ كرر الفحص على production بدون نسخ أسرار.
4. وثق mapping النهائي بين Madar payment methods وERPNext Mode of Payment في runbook الإنتاج.

## الخلاصة

تم إنشاء سجلات `Mode of Payment` المفقودة على staging بشكل idempotent وآمن:

- `Card`
- `Bank Transfer`
- `Online`

وبقيت عدادات ERP الحساسة دون تغيير. لم يتم retry لأي sync، ولم يتم إنشاء Payment Entry أو Sales Invoice أو GL Entry.
