# قائمة ما بعد الإطلاق

## أول ساعة

- [ ] health endpoint يعمل.
- [ ] login يعمل لمستخدم حقيقي.
- [ ] dashboard يفتح.
- [ ] reports تفتح حسب الصلاحيات.
- [ ] لا توجد 5xx errors متكررة.
- [ ] reverse proxy logs طبيعية.

## أول يوم

- [ ] أول طلب حقيقي تم إنشاؤه.
- [ ] أول approval تم.
- [ ] أول production work order تم.
- [ ] أول delivery/branch pickup تم.
- [ ] أول payment تم.
- [ ] أول cashbox تم إرساله ومراجعته.
- [ ] أول ERP Sales Order sync تم.
- [ ] أول Sales Invoice draft تم.
- [ ] أول Payment Entry draft تم.
- [ ] accounting finalization تم فقط بموافقة المحاسبة.

## أول أسبوع

- [ ] مراجعة logs يوميًا.
- [ ] مراجعة ERP sync failures يوميًا.
- [ ] مراجعة cashbox backlog يوميًا.
- [ ] مراجعة accounting finalization errors يوميًا.
- [ ] مراجعة user feedback.
- [ ] تسجيل UI/UX fixes المطلوبة.
- [ ] مراجعة performance للدashboard/reports.
- [ ] مراجعة backup success.
- [ ] تنفيذ restore drill إذا لم ينفذ قبل الإطلاق.

## مؤشرات يجب تصعيدها

- أي permission issue يسمح برؤية بيانات خارج النطاق.
- أي ERP posting غير متوقع.
- أي فشل متكرر في Payment Entry أو Sales Invoice submit.
- أي فقدان أو تضارب في cashbox.
- أي انقطاع health endpoint.
- أي تسريب محتمل لكلمة مرور أو مفتاح.

## تحسينات لاحقة مقترحة

- Alerting رسمي.
- Rate limiting.
- Audit export.
- Centralized logs.
- Secret manager integration.
- CI gate للفحص الأمني.
- User activity review.
