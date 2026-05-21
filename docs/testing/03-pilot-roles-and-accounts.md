# أدوار وحسابات تجربة staging pilot

> لا تكتب كلمات مرور أو مفاتيح API داخل هذا الملف. استخدم مدير كلمات مرور أو قناة آمنة لتوزيع بيانات الدخول.

## قواعد الحسابات

- staging فقط.
- لا تستخدم production credentials.
- لا تستخدم حسابات شخصية إن لم تكن مطلوبة.
- لا تشارك passwords في Slack أو docs أو screenshots.
- اربط كل tester بدور واضح.
- تأكد أن كل tester يعرف أن بيانات staging ليست محاسبة حقيقية.

## حسابات الاختبار المقترحة

| Role | Tester name | User/email | Employee linked? | Branch scope | Department scope | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| Madar Admin |  |  | [ ] yes  [ ] no |  |  |  |
| Madar Accountant |  |  | [ ] yes  [ ] no |  |  |  |
| Madar Branch Supervisor |  |  | [ ] yes  [ ] no |  |  |  |
| Madar Branch User |  |  | [ ] yes  [ ] no |  |  |  |
| Madar Production User |  |  | [ ] yes  [ ] no |  |  |  |
| Madar Driver |  |  | [ ] yes  [ ] no |  |  |  |
| Madar Cashier |  |  | [ ] yes  [ ] no |  |  |  |
| Madar Employee |  |  | [ ] yes  [ ] no |  |  |  |

## مصفوفة صلاحيات pilot المتوقعة

| Role | Expected access | Must not access |
| --- | --- | --- |
| Madar Admin | settings, reports, dashboard, admin review screens | secrets, direct ERP credentials |
| Madar Accountant | ERP sync, accounting review, finalization when approved | branch-only mutations outside accounting scope |
| Madar Branch Supervisor | approval queue for scoped branch | accounting final submit, other branches |
| Madar Branch User | create orders, branch pickup, scoped payments | approval actions, accounting final submit, other branches |
| Madar Production User | work order list/detail/actions | order approval, cashbox, accounting final submit |
| Madar Driver | assigned delivery batches | unassigned batches, branch cashbox review, accounting |
| Madar Cashier | cashbox review and permitted payment/cashbox screens | accounting final submit |
| Madar Employee | attendance, notifications, basic dashboard | orders/admin/accounting/delivery management |

## إعداد بيانات pilot

| Data area | Required setup | Owner | Ready? |
| --- | --- | --- | --- |
| Branches | At least one pilot branch |  | [ ] yes  [ ] no |
| Production center | At least one active center |  | [ ] yes  [ ] no |
| Production department | At least one active department |  | [ ] yes  [ ] no |
| Item mappings | Pilot items mapped to departments |  | [ ] yes  [ ] no |
| Catalog items | Pilot items available through catalog bridge |  | [ ] yes  [ ] no |
| Payment methods | Cash/Card/Transfer/Online configured |  | [ ] yes  [ ] no |
| ERP accounts | Staging mappings verified |  | [ ] yes  [ ] no |

## جلسة pilot

| Field | Value |
| --- | --- |
| Pilot date |  |
| Facilitator |  |
| Business owner |  |
| Accounting owner |  |
| Technical owner |  |
| Communication channel |  |

## تذكير قبل بدء الجلسة

- [ ] لا توجد production credentials مستخدمة.
- [ ] جميع الحسابات على staging فقط.
- [ ] كل tester يعرف دوره.
- [ ] feedback log جاهز.
- [ ] screenshots لا تحتوي بيانات حساسة.
- [ ] accounting submit/finalization لن يحدث إلا بموافقة المحاسب.
