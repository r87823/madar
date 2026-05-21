# خطة نشر مدار للإنتاج

هذه الحزمة توثق انتقال Madar من staging إلى production. هي وثائق تشغيل فقط ولا
تحتوي على أسرار أو مفاتيح أو كلمات مرور.

## الملفات

- [00-production-architecture.md](00-production-architecture.md): المعمارية الإنتاجية المقترحة.
- [01-environments.md](01-environments.md): فصل البيئات بين staging وproduction.
- [02-secrets-management.md](02-secrets-management.md): إدارة الأسرار والدوران والاستجابة للتسريب.
- [03-deployment-runbook.md](03-deployment-runbook.md): خطوات النشر التشغيلية.
- [04-rollback-plan.md](04-rollback-plan.md): خطة الرجوع عند الفشل.
- [05-backup-restore-plan.md](05-backup-restore-plan.md): النسخ الاحتياطي والاستعادة.
- [06-monitoring-logging.md](06-monitoring-logging.md): المراقبة والسجلات والتنبيهات.
- [07-go-live-checklist.md](07-go-live-checklist.md): قائمة تحقق يوم الإطلاق.
- [08-post-go-live-checklist.md](08-post-go-live-checklist.md): قائمة ما بعد الإطلاق.

## قواعد ثابتة

- لا يتم نشر production من هذه الوثائق تلقائيًا.
- لا تحفظ الأسرار في Git أو Flutter أو ملفات docs.
- لا تستخدم مستخدمي أو كلمات مرور staging في production.
- لا تفعل dev bootstrap في production.
- خذ نسخة احتياطية قبل أي deploy.
- جهز rollback قبل بدء deploy.
- راقب ERP sync وAccounting Finalization من أول ساعة تشغيل.
