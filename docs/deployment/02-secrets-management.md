# إدارة الأسرار

## القاعدة

لا تحفظ الأسرار في:

- Git repository.
- `AGENTS.md` أو `PLANS.md`.
- `docs/`.
- scripts داخل repo.
- Flutter.
- screenshots.
- shell history.
- logs.

## أنواع الأسرار

أسرار يجب أن تبقى خارج repo:

- root/server passwords.
- SSH private keys.
- ERP API keys/API secrets.
- Administrator password.
- database passwords.
- email passwords.
- WhatsApp/SMS tokens.
- payment gateway secrets.
- backup storage credentials.

## أماكن التخزين الموصى بها

استخدم واحدًا من:

- Frappe `site_config.json` للقيم التي يحتاجها site، مع حماية صلاحيات الملف.
- environment variables على الخادم.
- secret manager خارجي إذا توفر.
- SSH agent أو keychain خارج repo لمفاتيح SSH.

مثال قالب، بدون قيمة حقيقية:

```bash
export MADAR_EXAMPLE_SECRET="<managed-outside-repo>"
```

## ERP Credentials

- Flutter لا يحصل على ERP credentials.
- Madar server-side فقط قد يستخدم أي credentials لازمة مستقبلًا.
- لا تضف ERP API keys إلى Admin Settings.
- لا تطبع credentials في errors أو logs.

## دوران الأسرار قبل الإنتاج

- [ ] root password.
- [ ] SSH keys.
- [ ] Frappe Administrator password.
- [ ] database passwords.
- [ ] ERP API keys إن وجدت.
- [ ] backup storage credentials.
- [ ] any shared staging password.

## استجابة تسريب سر

إذا تم تسريب سر:

1. أوقف استخدام السر فورًا.
2. دوّر السر في المصدر الأصلي.
3. راجع logs للوصول غير المعتاد.
4. احذف السر من الملفات المحلية غير الملتزمة.
5. إذا وصل السر إلى Git history، اعتبره مكشوفًا حتى بعد الحذف.
6. وثق وقت التسريب والدوران.
7. راقب الحساب أو الخدمة المرتبطة لمدة مناسبة.

## مراجعة قبل كل Release

نفذ:

```bash
python3 scripts/check_security_rules.py
rg -n "MADAR_SSH_PASSWORD|sshpass|BEGIN .*PRIVATE KEY|api_secret|api_key|password|token" .
```

راجع النتائج يدويًا. وجود كلمات مثل `password` في tests أو auth UI ليس وحده
تسريبًا، لكن أي قيمة حقيقية يجب التعامل معها كتسريب.
