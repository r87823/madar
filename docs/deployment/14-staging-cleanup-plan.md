# خطة تنظيف staging وإعدادات ERP

## الملخص

- التاريخ: 2026-05-21
- البيئة: staging فقط
- النطاق: planning/documentation فقط
- المصدر الأساسي: `docs/deployment/13-staging-backlog-review.md`
- الهدف: تحديد ما يجب تنظيفه أو مراجعته قبل production readiness، بدون تعديل أي بيانات.

## حدود هذه الخطة

هذه الوثيقة لا تنفذ أي إجراء. لم يتم:

- حذف أي سجل.
- إعادة محاولة أي ERP sync.
- اعتماد أي cashbox.
- تعليم أي notification كمقروء.
- إنشاء `Mode of Payment` في ERPNext.
- إنشاء أو إرسال أي مستند ERP.
- تشغيل migrate أو restart.
- لمس production.

أي تنفيذ لاحق يجب أن يكون في مهمة منفصلة، بموافقة صريحة، وبعد أخذ backup.

## 1. ملخص النتائج الحالية

مراجعة R11-T06 وجدت backlog staging التالي:

| الفئة | العدد | الملخص |
| --- | ---: | --- |
| failed Madar Order ERP sync | 4 | أغلبها سجلات اختبار R3T05/R6T05. |
| failed Madar Payment ERP sync | 1 | `MADAR-PAY-2026-00012` فشل بسبب غياب `Mode of Payment: Card`. |
| accounting needs_attention | 1 | مرتبط بـ `MADAR-ORD-2026-00062` كسجل اختبار R6T05. |
| submitted cashbox | 1 | `MADAR-CASHBOX-2026-00004` لمستخدم test. |
| unread high-priority notifications | 2 | إشعارات test مرتبطة بإرجاع صناديق. |
| restore test site | 1 | `madar-restore-test.localhost` ما زال موجودًا للفحص. |

## 2. التصنيف التفصيلي

| العنصر | التصنيف | هل يحتاج تنظيف قبل production؟ | هل يحتاج مراجعة يدوية؟ | التوصية |
| --- | --- | --- | --- | --- |
| أوامر R3T05 بفشل customer lookup | test artifact | نعم، إذا كان staging يجب أن يكون نظيفًا | منخفضة | عزلها أو حذفها ضمن cleanup معتمد، أو توثيقها كاستثناء staging. |
| `MADAR-ORD-2026-00062` | test artifact + accounting attention | نعم | متوسطة | راجعه كسجل R6T05 ثم نظفه أو اتركه كاستثناء موثق. |
| `MADAR-PAY-2026-00012` | ERP configuration issue | نعم بعد إصلاح الإعداد | عالية | أصلح `Mode of Payment: Card` ثم قرر هل retry مناسب. |
| `MADAR-CASHBOX-2026-00004` | test artifact | نعم | منخفضة | الأفضل حله عبر UI/workflow أو تنظيف staging المعتمد. |
| high-priority unread notifications | test artifact | نعم، إذا كانت monitoring thresholds تتطلب صفر | منخفضة | تعليمها كمقروءة عبر UI أو تنظيفها ضمن خطة معتمدة. |
| `madar-restore-test.localhost` | restore drill artifact | ليس blocker إذا موثق | منخفضة | أبقه حتى انتهاء production readiness review، ولا تحذفه إلا بموافقة صريحة. |

## 3. مشكلة إعداد ERP

يجب أن تحتوي ERPNext على `Mode of Payment` مطابق للطرق التي يرسلها Madar عند مزامنة Payment Entry.

الطرق المطلوبة:

- `Cash`
- `Card`
- `Bank Transfer`
- `Online`

المشكلة الحالية في staging:

```text
لا يمكن أن تجد طريقة الدفع: Card
```

هذا يعني أن `Card` غير موجودة أو أن mapping بين Madar وERPNext لا يطابق الاسم الموجود في ERP.

### التوصية

قبل الإنتاج:

1. راجع `Mode of Payment` في ERPNext على staging.
2. أنشئ أو فعّل القيم المطلوبة إذا كانت غير موجودة.
3. وثق mapping النهائي بين Madar payment methods وERPNext Mode of Payment.
4. كرر نفس التحقق في production قبل go-live.

لا تنشئ أي `Mode of Payment` ضمن هذه المهمة.

## 4. خيارات cleanup

### Option A: ترك بيانات staging كما هي

مناسب لـ:

- بيئة dev/staging النشطة التي تحتوي اختبارات مقصودة.
- حفظ آثار اختبارات workflows.

غير مناسب لـ:

- اعتبار staging إشارة production readiness نظيفة.
- مراقبة تعتمد على thresholds صفرية لأخطاء sync/backlog.

المخاطر:

- التنبيهات ستبقى `CRITICAL`.
- قد تختلط مشاكل حقيقية لاحقة مع artifacts قديمة.

### Option B: التنظيف عبر UI/workflows

أمثلة:

- مراجعة/اعتماد/إرجاع cashbox عبر شاشة Madar.
- تعليم notifications كمقروءة عبر واجهة Madar.
- retry failed sync فقط بعد إصلاح إعداد ERP.
- حل accounting needs_attention عبر workflow المناسب أو توثيق الاستثناء.

المزايا:

- يحافظ على audit trail.
- يختبر workflows نفسها.
- أقل خطرًا من direct DB operations.

القيود:

- قد يتطلب مستخدمين وصلاحيات تشغيلية.
- قد يخلق مستندات ERP عند retry sync أو finalization، لذلك يحتاج موافقة صريحة.

### Option C: cleanup script مخصص لـ staging

مسموح فقط إذا تمت الموافقة عليه كمهمة لاحقة.

الشروط:

- staging-only guard واضح.
- dry-run mode إلزامي.
- idempotent.
- لا يعمل على production.
- لا direct DB deletes.
- لا حذف accounting documents.
- يسجل before/after counts.
- لا يطبع أسرار أو raw tracebacks.

الاستخدام المناسب:

- تنظيف notifications test.
- تعليم artifacts كـ resolved إن كان workflow يسمح بذلك.
- أرشفة test-only records إذا كان ذلك مدعومًا.

غير مناسب:

- حذف ERP documents.
- تعديل GL Entry أو Sales Invoice أو Payment Entry مباشرة.
- تجاوز state machines أو audit trail.

## 5. التسلسل المقترح للتنظيف المستقبلي

1. أخذ backup جديد قبل أي cleanup.
2. تشغيل health check.
3. تسجيل ERP document count baseline:
   - `GL Entry`
   - `Delivery Note`
   - `Stock Entry`
   - `Sales Invoice`
   - `Payment Entry`
4. إصلاح إعداد ERP أولًا:
   - verify/create `Cash`
   - verify/create `Card`
   - verify/create `Bank Transfer`
   - verify/create `Online`
5. إعادة فحص `MADAR-PAY-2026-00012`.
6. إذا كان الدفع لا يزال relevant، نفذ retry payment sync بموافقة صريحة.
7. راجع أو وثق failed order sync artifacts:
   - إما cleanup staging.
   - أو keep as documented exceptions.
8. راجع `MADAR-CASHBOX-2026-00004` عبر workflow أو قرر تنظيفه.
9. علّم high-priority test notifications كمقروءة عبر UI أو workflow.
10. أعد تشغيل:

```bash
scripts/monitoring/check_staging_health.sh
python3 scripts/monitoring/check_erp_sync_status.py --bench-path /home/frappe/frappe-bench --site hrms.localhost
```

11. سجل before/after counts في تقرير R11-T08.
12. لا تعتبر cleanup مكتملًا إلا إذا أصبحت critical counts صفرية أو موثقة كاستثناءات مقبولة.

## 6. نقاط الموافقة المطلوبة

قبل R11-T08 أو أي تنفيذ:

- موافقة على أخذ backup جديد.
- موافقة على إنشاء/تعديل ERPNext `Mode of Payment` في staging.
- موافقة قبل أي retry ERP sync.
- موافقة قبل أي mutation على cashbox.
- موافقة قبل تعليم notifications كمقروءة.
- موافقة قبل أي cleanup script.
- موافقة صريحة قبل حذف أو إسقاط `madar-restore-test.localhost`.

## 7. Guardrails

- لا cleanup على production.
- لا destructive delete بدون موافقة صريحة.
- لا direct DB deletes.
- تفضيل UI/API/workflow actions على أي scripts.
- backup قبل cleanup.
- تسجيل before/after counts.
- عدم طباعة raw errors أو أسرار.
- عدم تعديل مستندات ERP المحاسبية مباشرة.
- عدم إرسال Sales Invoice أو Payment Entry ضمن cleanup إلا إذا كانت مهمة لاحقة صريحة.
- أي script يجب أن يحتوي dry-run وstaging guard.

## 8. Checklist تنفيذ مستقبلي لـ R11-T08

- [ ] تأكيد أن المهمة execution وليست planning.
- [ ] أخذ backup جديد.
- [ ] فحص health endpoint.
- [ ] تسجيل ERP count baseline.
- [ ] تسجيل backlog baseline.
- [ ] إصلاح ERP payment methods بعد الموافقة.
- [ ] تنفيذ الإجراءات المعتمدة فقط.
- [ ] تشغيل monitoring scripts.
- [ ] التحقق أن ERP counts لم تتغير إلا إذا كان التغيير متوقعًا ومصرحًا.
- [ ] توثيق before/after.
- [ ] توثيق أي سجلات بقيت كاستثناءات.
- [ ] commit تقرير cleanup فقط.

## 9. موقع اختبار الاستعادة

الحالة الحالية:

```text
madar-restore-test.localhost: exists
```

الخيارات:

1. إبقاؤه حتى اكتمال production readiness review.
2. إسقاطه لاحقًا بعد موافقة صريحة.
3. إنشاء backup أو snapshot إضافي قبل إسقاطه إذا كان مطلوبًا للتدقيق.

ملاحظة: إسقاط الموقع destructive ويجب ألا يحدث ضمن هذه الخطة.

## 10. خلاصة القرار المقترح

المسار الأكثر أمانًا:

1. إبقاء staging كما هو حتى R11-T08.
2. في R11-T08، ابدأ بإصلاح إعدادات `Mode of Payment` في ERPNext على staging.
3. بعد إصلاح الإعداد، أعد تقييم payment sync failure.
4. عالج artifacts عبر workflows حيث أمكن.
5. لا تستخدم cleanup scripts إلا إذا كانت الواجهة/workflows غير كافية، وبعد dry-run وموافقة صريحة.

هذه الخطة تترك التنفيذ واضحًا ومؤجلًا، وتمنع خلط cleanup مع التخطيط.
