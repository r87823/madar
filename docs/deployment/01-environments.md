# فصل البيئات

## القاعدة

staging وproduction بيئتان منفصلتان تمامًا. أي مشاركة في البيانات أو الأسرار
بينهما تعتبر خطرًا تشغيليًا.

## Staging

مسموح في staging:

- dev/test users مع guard صريح.
- بيانات اختبار.
- ERP documents اختبارية.
- كلمات مرور مؤقتة محمية خارج repo.
- تجارب migration قبل production.

ممنوع في staging:

- أسرار production.
- بيانات عملاء production الحقيقية إلا بموافقة صريحة وخطة إخفاء بيانات.
- استخدام staging كنسخة backup وحيدة.

## Production

ممنوع في production:

- dev bootstrap.
- test users.
- default passwords.
- staging credentials.
- staging domain callbacks/config.
- أي مفاتيح أو كلمات مرور داخل repo أو docs أو Flutter.

مطلوب في production:

- production site مستقل.
- production database مستقلة.
- production Redis/files مستقلة.
- production domain وSSL.
- production ERP company/settings verified.
- real users فقط.
- roles reviewed قبل الإطلاق.

## Dev Bootstrap Guard

Dev bootstrap لا يعمل افتراضيًا. لا تفعله في production.

مفاتيح التفعيل المسموحة للـ staging/dev فقط:

```bash
MADAR_ENABLE_DEV_BOOTSTRAP=1
MADAR_DEV_USER_PASSWORD=<set outside repo>
```

يوجد دعم legacy للاسم:

```bash
MADAR_ENABLE_DEV_USER_BOOTSTRAP=1
```

استخدمه فقط للتوافق، وفضل الاسم الجديد في أي بيئة جديدة.

## إعدادات Flutter

- staging build يشير إلى staging domain.
- production build يشير إلى production domain.
- لا تحفظ ERP credentials أو admin passwords في Flutter.
- لا تخلط ملفات config بين buildين.

## قائمة تحقق فصل البيئة

- [ ] production domain مختلف عن staging.
- [ ] production site name موثق داخليًا.
- [ ] production database منفصلة.
- [ ] production file storage منفصل.
- [ ] production site_config مستقل.
- [ ] production secrets مختلفة.
- [ ] dev bootstrap disabled.
- [ ] test users غير موجودين أو disabled.
- [ ] roles production مراجعة.
- [ ] payment methods production مراجعة.
- [ ] accounting settings production مراجعة.
