# تقرير محاذاة نسخة staging

## الملخص

- التاريخ: 2026-05-21
- البيئة: staging فقط
- المشغل: Codex
- الخادم: `root@46.202.154.140`
- الحاوية: `docker-frappe-1`
- مسار bench: `/home/frappe/frappe-bench`
- مسار التطبيق: `/home/frappe/frappe-bench/apps/madar`
- الموقع النشط: `hrms.localhost`
- الرابط العام: `https://madar-test.r8787m.cc`
- موقع اختبار الاستعادة: `madar-restore-test.localhost`
- النتيجة: تمت محاذاة repository الخاص بتطبيق `madar` على staging مع `upstream/main`.

## سبب المحاذاة

أظهر تمرين الاستعادة R11-T03 أن نسخة `apps/madar` داخل حاوية staging كانت على:

```text
0528ae9 chore: add security hardening checks
```

بينما كان `origin/main` المحلي على:

```text
c2f8854 docs: add restore drill report
```

وكان tag المصقول:

```text
v0.3.0-staging-polished-mvp -> f461ada feat: polish arabic error messages
```

لذلك تمت محاذاة staging إلى رأس `upstream/main` لتصبح نسخة staging موثقة وواضحة قبل أعمال الجاهزية التالية.

## فحص ما قبل التنفيذ

### المستودع المحلي

```bash
git status --short
git log -1 --oneline
git tag --points-at HEAD || true
```

النتيجة:

```text
working tree clean
c2f8854 docs: add restore drill report
no tag points at HEAD
```

### صحة staging النشط

```bash
curl -fsS https://madar-test.r8787m.cc/api/method/madar.api.health.ping
```

النتيجة:

```json
{"ok": true, "app": "madar", "service": "Madar Frappe Backend"}
```

### نسخة التطبيق على staging قبل المحاذاة

```bash
docker exec docker-frappe-1 bash -lc '
  cd /home/frappe/frappe-bench/apps/madar &&
  git status --short &&
  git log -1 --oneline &&
  git remote -v
'
```

النتيجة المختصرة:

```text
?? madar.egg-info/
0528ae9 chore: add security hardening checks
upstream https://github.com/r87823/madar.git (fetch)
upstream https://github.com/r87823/madar.git (push)
```

ملاحظة: `madar.egg-info/` ملف مولد وغير متتبع كان موجودًا قبل المحاذاة. لم يتم حذفه أو تعديله.

### عدادات ERP الحساسة قبل المحاذاة

| DocType | العدد قبل |
| --- | ---: |
| GL Entry | 4 |
| Delivery Note | 0 |
| Stock Entry | 0 |
| Sales Invoice | 3 |
| Payment Entry | 2 |

تم التحقق كذلك أن موقع الاستعادة `madar-restore-test.localhost` موجود قبل التنفيذ.

## تحديد الحاجة إلى migrate أو restart

تم فحص الفرق بين commit الموجود سابقًا على staging وcommit الهدف:

```bash
git diff --name-only 0528ae9..c2f8854
```

الملفات المتغيرة بين النسختين كانت ضمن:

- `docs/`
- `lib/`
- `test/`

ولم تظهر تغييرات في:

- `madar/`
- ملفات Python
- `setup.py`
- `pyproject.toml`
- ملفات JSON/DocType runtime

بناءً على ذلك:

- لم يتم تشغيل `bench migrate`.
- لم يتم تشغيل `bench restart`.
- لا يوجد تغيير backend runtime مطلوب لهذا التحديث.

ملاحظة تشغيلية: تغييرات Flutter قد تحتاج آلية نشر assets منفصلة إذا كان Flutter web مستضافًا من عملية مستقلة، لكن ذلك خارج نطاق هذه المحاذاة ولم يتم تغيير خادم staging العام أو Nginx Proxy Manager.

## أمر المحاذاة المنفذ

تم تنفيذ المحاذاة داخل مسار التطبيق فقط:

```bash
cd /home/frappe/frappe-bench/apps/madar
git fetch upstream main
git reset --hard upstream/main
git log -1 --oneline
git status --short
```

النتيجة:

```text
HEAD is now at c2f8854 docs: add restore drill report
c2f8854 docs: add restore drill report
?? madar.egg-info/
```

لم يتم حذف `madar.egg-info/` لأنها غير متتبعة ومولدة على الخادم، ولم يكن cleanup ضمن نطاق المهمة.

## فحص ما بعد التنفيذ

### نسخة التطبيق بعد المحاذاة

```text
c2f8854 docs: add restore drill report
```

لا يوجد tag يشير إلى هذا commit على staging. هذا متوقع لأن `v0.3.0-staging-polished-mvp` يشير إلى `f461ada`، بينما `c2f8854` يحتوي لاحقًا على توثيق restore drill.

### صحة staging النشط بعد المحاذاة

```json
{"ok": true, "app": "madar", "service": "Madar Frappe Backend"}
```

### عدادات ERP الحساسة بعد المحاذاة

| DocType | العدد قبل | العدد بعد |
| --- | ---: | ---: |
| GL Entry | 4 | 4 |
| Delivery Note | 0 | 0 |
| Stock Entry | 0 | 0 |
| Sales Invoice | 3 | 3 |
| Payment Entry | 2 | 2 |

لم تتغير عدادات ERP الحساسة نتيجة هذه المهمة.

### حالة موقع الاستعادة

```text
madar-restore-test.localhost: EXISTS
```

لم يتم حذف موقع الاستعادة أو تعديله.

## ما لم يتم تنفيذه

- لم يتم تشغيل `bench migrate` على `hrms.localhost`.
- لم يتم تشغيل `bench restart`.
- لم يتم تغيير Nginx Proxy Manager.
- لم يتم لمس production.
- لم يتم إنشاء أو تعديل أو إرسال أي مستند ERP.
- لم يتم حذف `madar-restore-test.localhost`.
- لم يتم حذف الملفات غير المتتبعة على staging.

## المخاطر المتبقية

- `madar.egg-info/` لا يزال موجودًا كملف مولد غير متتبع داخل repository على staging. لا يؤثر ذلك على commit المتتبع، لكن يمكن تنظيفه لاحقًا في نافذة صيانة إذا تمت الموافقة.
- tag `v0.3.0-staging-polished-mvp` لا يشير إلى آخر commit موثق `c2f8854`; الفرق بعد `f461ada` توثيقي، لذلك runtime backend لا يتغير، لكن يجب اختيار سياسة واضحة للعلامات القادمة: إما tag لكل checkpoint توثيقي أو tag للنسخ runtime فقط.
- إذا كان Flutter web يتم نشره كـ assets منفصلة، فمحاذاة Git داخل Frappe container لا تعني بالضرورة أن واجهة Flutter المنشورة تغيرت. يلزم توثيق مسار نشر Flutter web قبل الإنتاج.

## خلاصة الجاهزية

تمت محاذاة تطبيق `madar` على staging إلى `c2f8854 docs: add restore drill report` بدون migrate أو restart، وبقي الموقع النشط سليمًا، وبقيت عدادات ERP الحساسة دون تغيير، وبقي موقع الاستعادة متاحًا للفحص.
