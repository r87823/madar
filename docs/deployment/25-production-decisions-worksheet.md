# ورقة قرارات الإنتاج

> تحذير مهم: لا تكتب كلمات مرور أو مفاتيح API أو tokens أو SSH secrets داخل هذا الملف. استخدم مدير كلمات مرور أو secret manager، واكتب هنا اسم المالك وحالة القرار فقط.

## الغرض

هذه الورقة تجمع القرارات المطلوبة قبل R12-T03. املأها من قبل مالكي العمل والتقنية والمحاسبة قبل إنشاء production site أو تنفيذ أي deployment.

الحالة العامة:

- [ ] Pending
- [ ] Approved
- [ ] Blocked

## 1. قرار الاستضافة

| الحقل | القيمة |
| --- | --- |
| Production server | [ ] نفس خادم staging  [ ] خادم منفصل |
| Server IP/hostname |  |
| Owner |  |
| SSH access owner |  |
| Decision status | [ ] pending  [ ] approved |

ملاحظات:

```text

```

## 2. نطاق الإنتاج وSSL

| الحقل | القيمة |
| --- | --- |
| Production domain |  |
| DNS provider |  |
| SSL method | [ ] Nginx Proxy Manager / Let's Encrypt  [ ] شهادة خارجية  [ ] آخر |
| Reverse proxy | [ ] Nginx Proxy Manager  [ ] آخر |
| Owner |  |
| Decision status | [ ] pending  [ ] approved |

ملاحظات:

```text

```

## 3. موقع Frappe للإنتاج

| الحقل | القيمة |
| --- | --- |
| Production site name |  |
| Bench path |  |
| Release tag | `v0.4.0-production-readiness-candidate` |
| Decision status | [ ] pending  [ ] approved |

Apps المطلوبة:

- [ ] `frappe`
- [ ] `erpnext`
- [ ] `hrms`
- [ ] `madar`

ملاحظات:

```text

```

## 4. إدارة الأسرار

لا تكتب القيم السرية هنا. اكتب فقط المالك ومكان التخزين العام.

| الحقل | القرار |
| --- | --- |
| Password manager/tool |  |
| SSH key owner |  |
| Frappe Administrator password owner |  |
| DB password owner |  |
| Backup encryption key owner |  |
| ERP API keys needed? | [ ] yes  [ ] no |
| Decision status | [ ] pending  [ ] approved |

ملاحظات:

```text

```

## 5. إعداد ERP المحاسبي

| الحقل | القيمة |
| --- | --- |
| Production company name |  |
| Currency |  |
| Cash account |  |
| Card settlement/bank account |  |
| Bank Transfer account |  |
| Online/gateway account |  |
| Accountant approver |  |
| Decision status | [ ] pending  [ ] approved |

ملاحظات المحاسب:

```text

```

## 6. طرق الدفع

| Mode of Payment | Mode exists? | Account mapping approved? | Account name | Approved by |
| --- | --- | --- | --- | --- |
| Cash | [ ] yes  [ ] no | [ ] yes  [ ] no |  |  |
| Card | [ ] yes  [ ] no | [ ] yes  [ ] no |  |  |
| Bank Transfer | [ ] yes  [ ] no | [ ] yes  [ ] no |  |  |
| Online | [ ] yes  [ ] no | [ ] yes  [ ] no |  |  |

ملاحظات:

```text

```

## 7. المستخدمون الحقيقيون والأدوار

| Role | User owner | Employee linked? | Branch scope? | Department scope? | Password reset required? |
| --- | --- | --- | --- | --- | --- |
| Madar Admin |  | [ ] yes  [ ] no | [ ] yes  [ ] no  [ ] n/a | [ ] yes  [ ] no  [ ] n/a | [ ] yes  [ ] no |
| Madar Accountant |  | [ ] yes  [ ] no | [ ] yes  [ ] no  [ ] n/a | [ ] yes  [ ] no  [ ] n/a | [ ] yes  [ ] no |
| Madar Branch Supervisor |  | [ ] yes  [ ] no | [ ] yes  [ ] no  [ ] n/a | [ ] yes  [ ] no  [ ] n/a | [ ] yes  [ ] no |
| Madar Branch User |  | [ ] yes  [ ] no | [ ] yes  [ ] no  [ ] n/a | [ ] yes  [ ] no  [ ] n/a | [ ] yes  [ ] no |
| Madar Production User |  | [ ] yes  [ ] no | [ ] yes  [ ] no  [ ] n/a | [ ] yes  [ ] no  [ ] n/a | [ ] yes  [ ] no |
| Madar Driver |  | [ ] yes  [ ] no | [ ] yes  [ ] no  [ ] n/a | [ ] yes  [ ] no  [ ] n/a | [ ] yes  [ ] no |
| Madar Cashier |  | [ ] yes  [ ] no | [ ] yes  [ ] no  [ ] n/a | [ ] yes  [ ] no  [ ] n/a | [ ] yes  [ ] no |
| Madar Employee |  | [ ] yes  [ ] no | [ ] yes  [ ] no  [ ] n/a | [ ] yes  [ ] no  [ ] n/a | [ ] yes  [ ] no |

ملاحظات:

```text

```

## 8. النسخ الاحتياطي والاستعادة

| الحقل | القرار |
| --- | --- |
| External encrypted backup location |  |
| Backup frequency |  |
| Retention |  |
| Restore drill owner |  |
| Production restore test required? | [ ] yes  [ ] no |
| Decision status | [ ] pending  [ ] approved |

ملاحظات:

```text

```

## 9. المراقبة والتنبيهات

| الحقل | القرار |
| --- | --- |
| Health monitor owner |  |
| Backup alert owner |  |
| ERP sync failure alert owner |  |
| Disk usage alert owner |  |
| Alert channel |  |
| Decision status | [ ] pending  [ ] approved |

قنوات مقترحة:

- [ ] Email
- [ ] Slack/Teams
- [ ] Telegram
- [ ] WhatsApp
- [ ] Uptime Kuma
- [ ] أخرى:

ملاحظات:

```text

```

## 10. اعتماد go-live

| الحقل | القيمة |
| --- | --- |
| Technical approver |  |
| Accounting approver |  |
| Operations approver |  |
| Go-live date candidate |  |
| Final decision | [ ] pending  [ ] approved  [ ] blocked |

شروط قبل اعتماد go-live:

- [ ] production domain approved.
- [ ] SSL approved.
- [ ] production site name approved.
- [ ] secret storage approved.
- [ ] ERP accounting mappings approved.
- [ ] real users/scopes approved.
- [ ] external encrypted backup approved.
- [ ] monitoring/alerts approved.
- [ ] rollback owner approved.
- [ ] smoke test owner approved.

ملاحظات الاعتماد:

```text

```

## سجل التوقيعات

| الاسم | الدور | القرار | التاريخ |
| --- | --- | --- | --- |
|  | Technical | [ ] pending  [ ] approved  [ ] blocked |  |
|  | Accounting | [ ] pending  [ ] approved  [ ] blocked |  |
|  | Operations | [ ] pending  [ ] approved  [ ] blocked |  |

## تذكير أخير

- لا تكتب أي secret داخل هذه الورقة.
- لا تستخدم بيانات staging في production.
- لا تفعل dev bootstrap في production.
- لا تبدأ R12-T03 قبل اكتمال القرارات الأساسية أو توثيق الاستثناءات صراحة.
