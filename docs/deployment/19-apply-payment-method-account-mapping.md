# تقرير تطبيق ربط حسابات طرق الدفع على staging

## الملخص

- التاريخ: 2026-05-21
- البيئة: staging فقط
- الموقع: `hrms.localhost`
- الشركة: `test`
- عملة الشركة: `SAR`
- النطاق: ERPNext configuration فقط
- القرار المعتمد: إنشاء حساب تسوية إلكترونية وربط طرق الدفع الإلكترونية به.

## حدود التنفيذ

لم يتم:

- لمس production.
- إنشاء Payment Entry.
- إرسال Payment Entry.
- إنشاء Sales Invoice.
- إرسال Sales Invoice.
- إنشاء GL Entry.
- إنشاء Delivery Note أو Stock Entry.
- retry لـ `MADAR-PAY-2026-00012`.
- تشغيل migrate أو restart.
- تعديل كود Madar أو workflow.

## صحة الموقع

قبل وبعد التنفيذ:

```text
OK health_check ok=true app=madar
```

## نسخة تطبيق Madar على staging

داخل `/home/frappe/frappe-bench/apps/madar`:

```text
445387c fix: add payment entry exchange rates
?? madar.egg-info/
```

لم يتم حذف أو تعديل `madar.egg-info/`.

## عدادات ERP قبل/بعد

| DocType | قبل | بعد |
| --- | ---: | ---: |
| GL Entry | 4 | 4 |
| Delivery Note | 0 | 0 |
| Stock Entry | 0 | 0 |
| Sales Invoice | 3 | 3 |
| Payment Entry | 2 | 2 |

لم يتم إنشاء أي مستندات ERP transaction.

## حالة ما قبل التنفيذ

### الحساب المطلوب

الحساب التالي لم يكن موجودًا قبل التنفيذ:

```text
1120 - حساب تسوية المدفوعات الإلكترونية - T
```

### حساب Cash الحالي

| Account | Parent | Type | Currency |
| --- | --- | --- | --- |
| `1110 - نقد - T` | `1100 - النقدية الحاضرة - T` | Cash | SAR |

### parent account المعتمد

تم اختيار parent آمن وواضح تحت الأصول:

| Parent account | Type | Root | Is group |
| --- | --- | --- | ---: |
| `1200 - حسابات مصرفية - T` | Bank | Asset | 1 |

هذا parent هو group للحسابات المصرفية ضمن الأصول المتداولة في شركة `test`.

### الربط قبل التنفيذ

| Mode of Payment | Company | Default account |
| --- | --- | --- |
| `Cash` | `test` | `1110 - نقد - T` |

لم تكن هناك mappings لـ:

- `Card`
- `Bank Transfer`
- `Online`

## التنفيذ

تم التنفيذ عبر Frappe ORM داخل `bench --site hrms.localhost console` بمنطق idempotent:

1. التحقق من أن parent account آمن:
   - الشركة `test`
   - root type = `Asset`
   - is group = 1
2. إنشاء الحساب فقط إذا كان مفقودًا.
3. إضافة صفوف `Mode of Payment Account` فقط إذا لم تكن موجودة.
4. التوقف لو وجد mapping مختلف، بدون overwrite.

## الحساب الذي تم إنشاؤه

| Field | Value |
| --- | --- |
| Account | `1120 - حساب تسوية المدفوعات الإلكترونية - T` |
| account_name | `حساب تسوية المدفوعات الإلكترونية` |
| account_number | `1120` |
| company | `test` |
| parent_account | `1200 - حسابات مصرفية - T` |
| account_type | `Bank` |
| root_type | `Asset` |
| report_type | `Balance Sheet` |
| is_group | 0 |
| account_currency | `SAR` |

## الربط بعد التنفيذ

| Mode of Payment | Company | Default account |
| --- | --- | --- |
| `Bank Transfer` | `test` | `1120 - حساب تسوية المدفوعات الإلكترونية - T` |
| `Card` | `test` | `1120 - حساب تسوية المدفوعات الإلكترونية - T` |
| `Cash` | `test` | `1110 - نقد - T` |
| `Online` | `test` | `1120 - حساب تسوية المدفوعات الإلكترونية - T` |

## أثر ذلك على payment sync

هذا التغيير يزيل blocker الخاص بـ `ERP_PAYMENT_ACCOUNT_UNRESOLVED` لطرق الدفع:

- `Card`
- `Bank Transfer`
- `Online`

لكن لم يتم retry لـ `MADAR-PAY-2026-00012` ضمن هذه المهمة حسب التعليمات. يجب تنفيذ retry في مهمة منفصلة مع baseline واضح للعدادات.

## توصية الإنتاج

- لا تنسخ حساب staging تلقائيًا إلى production.
- يجب على المحاسب إنشاء أو اعتماد الحسابات الحقيقية في production حسب chart of accounts الإنتاجي.
- يجب ربط `Card`, `Bank Transfer`, و`Online` بحسابات production المناسبة قبل go-live.
- يجب تسجيل before/after counts عند تنفيذ نفس الإعداد في production.

## الخلاصة

تم إنشاء الحساب المعتمد على staging وربط طرق الدفع الإلكترونية به:

- `Card`
- `Bank Transfer`
- `Online`

وبقي `Cash` مربوطًا بالحساب السابق. لم تتغير عدادات ERP transaction، ولم يتم إنشاء Payment Entry أو GL Entry أو أي مستندات ERP أخرى.
