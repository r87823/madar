# خطة تجربة المستخدم على staging

## الهدف

تشغيل pilot عملي على بيئة staging قبل production لاكتشاف مشاكل workflow وUI والصلاحيات والمحاسبة والتدريب قبل go-live.

## حدود التجربة

- البيئة: staging فقط.
- لا تستخدم production credentials.
- لا تستخدم بيانات عملاء حساسة إلا بموافقة صريحة.
- لا تعتبر مستندات staging المحاسبية مستندات حقيقية.
- لا تبدأ production setup قبل مراجعة feedback.
- لا تغير الكود أثناء جلسة pilot؛ سجل كل ملاحظة أولًا.
- لا تكتب passwords أو API keys أو tokens في ملفات التوثيق.

## المشاركون

| الدور | الهدف من الاختبار |
| --- | --- |
| Admin | الإعدادات، الصلاحيات، dashboard، reports |
| Accountant | ERP sync، invoice/payment entry، accounting review |
| Branch User | إنشاء الطلب، branch pickup، payment collection عند الفرع |
| Branch Supervisor | approval queue، approve/return/reject |
| Production User | work orders، accept/start/ready/delay |
| Driver | delivery batches، pickup/out/delivered/returned |
| Cashier | cashbox review، approve/return |
| Employee | attendance، notifications، صلاحيات محدودة |

## قواعد بيانات الاختبار

- استخدم أسماء واضحة تبدأ بـ `PILOT`.
- لا تستخدم أرقام هواتف أو أسماء عملاء حقيقيين إلا بموافقة.
- ضع ملاحظة داخل الطلب إن أمكن:

```text
PILOT TEST - ليس طلبًا حقيقيًا
```

- لا تنظف بيانات pilot أثناء الجلسة. وثق cleanup في مهمة منفصلة بعد المراجعة.

## نطاق الاختبار

### 1. Login and Permissions

- Admin.
- Accountant.
- Branch User.
- Branch Supervisor.
- Production User.
- Driver.
- Cashier.
- Employee.

المطلوب:

- كل مستخدم يستطيع الدخول.
- كل مستخدم يرى الشاشات المناسبة فقط.
- لا يوجد وصول غير مصرح لشاشات المحاسبة أو الإدارة أو فروع أخرى.

### 2. Attendance

- تسجيل حضور.
- تسجيل انصراف.
- عرض السجل.
- تجربة duplicate/invalid action إن أمكن.

### 3. Order Flow

- إنشاء طلب.
- اختيار fulfillment:
  - استلام من الفرع.
  - توصيل للعميل.
- إضافة أصناف.
- تعديل الكمية.
- إرسال للاعتماد.

### 4. Approval

- اعتماد طلب.
- إرجاع للتعديل مع سبب.
- رفض مع سبب.
- التأكد أن الطلب الفارغ لا يُرسل.

### 5. ERP Sync

- إنشاء ERP Sales Order draft.
- إرسال Sales Order فقط إذا وافق المحاسب على test في staging.
- إنشاء Sales Invoice draft فقط إذا وصل flow إلى completion.
- لا تعتبر أي مستند staging مستندًا حقيقيًا.

### 6. Production

- إنشاء work orders من طلب معتمد.
- قبول أمر الإنتاج.
- بدء الإنتاج.
- التعليم كجاهز.
- التأخير مع سبب.
- التأكد من production status على الطلب.

### 7. Delivery / Branch Pickup

- إنشاء delivery batch.
- إسناد السائق.
- السائق يحدّث batch:
  - استلام الدفعة.
  - خرج إلى الفرع أو خرج للتوصيل.
  - تم التسليم.
  - إرجاع مع سبب عند الحاجة.
- branch receives order.
- ready for customer pickup.
- customer pickup.
- customer delivery.

### 8. Payments

- نقد.
- بطاقة.
- تحويل.
- إلكتروني.
- دفع جزئي.
- دفع كامل.
- رفض الدفع الزائد.
- التأكد من paid/remaining/payment status.

### 9. Cashbox

- cash payment creates cashbox entry.
- submit cashbox.
- cashier/accountant review.
- approve.
- return with reason.

### 10. Accounting Finalization

- مراجعة accounting summary.
- sync payment entries.
- submit invoice/payment entry فقط إذا وافق المحاسب على أثر GL في staging.
- verify GL impact في staging فقط.
- لا تنفذ final submit دون موافقة المحاسب الموجود في الجلسة.

### 11. Notifications

- استلام notifications للأحداث.
- فتح الشاشة المرتبطة.
- mark read.
- التأكد أن المستخدم لا يرى notifications لغيره.

### 12. Dashboard and Reports

- لوحة المتابعة.
- التقارير.
- filters.
- role-based visibility.
- التحقق من وضوح الأرقام والرسائل العربية.

### 13. Settings

- Admin can view/update safe settings.
- Non-admin denied.
- لا تظهر أي secret fields.

## طريقة تسجيل النتائج

لكل test case سجل:

- tester role.
- steps.
- expected result.
- actual result.
- pass/fail.
- notes.
- screenshot/reference إن وجد.
- priority:
  - blocker.
  - high.
  - medium.
  - low.

استخدم:

- [01-user-acceptance-checklist.md](01-user-acceptance-checklist.md)
- [02-feedback-log-template.md](02-feedback-log-template.md)
- [03-pilot-roles-and-accounts.md](03-pilot-roles-and-accounts.md)

## تصنيفات feedback

- bug.
- workflow change.
- UI/UX improvement.
- missing feature.
- permission issue.
- report issue.
- accounting issue.
- performance issue.
- training/documentation issue.

## معايير نجاح pilot

- المستخدمون يكملون full order-to-accounting flow على staging.
- كل دور يرى الشاشات المقصودة فقط.
- لا توجد permission leaks حرجة.
- لا توجد ERP failures غير مفسرة.
- dashboard/reports مفهومة للمستخدمين.
- branch pickup flow يطابق العمليات الفعلية.
- payment/cashbox flow مقبول من cashier/accountant.
- production team تقبل work order flow.
- driver يقبل delivery batch flow.
- الرسائل العربية واضحة.

## قرار الخروج

بعد pilot، صنف النتيجة:

- [ ] GO to production setup
- [ ] NEEDS CHANGES before production
- [ ] NO-GO due to blockers

لا تبدأ production setup حتى تُراجع feedback log ويتم اعتماد قرار الخروج.
