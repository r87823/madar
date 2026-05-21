# قائمة اختبار قبول المستخدم

## طريقة الاستخدام

انسخ الصفوف أو أضف صفوفًا جديدة حسب الحاجة. لا تكتب passwords أو secrets. استخدم أسماء test واضحة تبدأ بـ `PILOT`.

الأولويات:

- blocker
- high
- medium
- low

## 1. Login and Permissions

| ID | Tester role | Steps | Expected result | Actual result | Pass/Fail | Priority | Notes | Screenshot/reference |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| UAT-001 | Admin | Login, open dashboard, open settings/reports | Admin can access admin screens |  |  |  |  |  |
| UAT-002 | Accountant | Login, open accounting/sync/finalization screens | Accountant can access accounting screens |  |  |  |  |  |
| UAT-003 | Branch User | Login, open orders, try admin/accounting screens | Branch user can access branch workflows only |  |  |  |  |  |
| UAT-004 | Branch Supervisor | Login, open approval queue | Supervisor sees branch approval queue only |  |  |  |  |  |
| UAT-005 | Production User | Login, open work orders | Production user sees production work only |  |  |  |  |  |
| UAT-006 | Driver | Login, open my batches | Driver sees assigned batches only |  |  |  |  |  |
| UAT-007 | Cashier | Login, open cashbox review | Cashier can review cashboxes, cannot finalize accounting |  |  |  |  |  |
| UAT-008 | Employee | Login, open attendance/notifications | Employee sees basic allowed screens only |  |  |  |  |  |

## 2. Attendance

| ID | Tester role | Steps | Expected result | Actual result | Pass/Fail | Priority | Notes | Screenshot/reference |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| UAT-020 | Employee | Open attendance, tap تسجيل حضور | Check-in succeeds and state becomes داخل الدوام |  |  |  |  |  |
| UAT-021 | Employee | Tap تسجيل انصراف | Check-out succeeds and state becomes خارج الدوام |  |  |  |  |  |
| UAT-022 | Employee | Open history | Latest attendance entries appear |  |  |  |  |  |

## 3. Order Flow

| ID | Tester role | Steps | Expected result | Actual result | Pass/Fail | Priority | Notes | Screenshot/reference |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| UAT-030 | Branch User | Create order with branch pickup | Fulfillment defaults to استلام من الفرع and branch is required |  |  |  |  |  |
| UAT-031 | Branch User | Create order with customer delivery | Destination branch not required |  |  |  |  |  |
| UAT-032 | Branch User | Search catalog and add item | Item appears with qty and line total |  |  |  |  |  |
| UAT-033 | Branch User | Update quantity | Totals recalculate |  |  |  |  |  |
| UAT-034 | Branch User | Submit empty order | Error appears: cannot submit without items |  |  |  |  |  |
| UAT-035 | Branch User | Submit order with items | Order status becomes مرسل للاعتماد |  |  |  |  |  |

## 4. Approval

| ID | Tester role | Steps | Expected result | Actual result | Pass/Fail | Priority | Notes | Screenshot/reference |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| UAT-040 | Branch Supervisor | Open approval queue | Submitted branch orders appear |  |  |  |  |  |
| UAT-041 | Branch Supervisor | Approve order | Order status becomes معتمد |  |  |  |  |  |
| UAT-042 | Branch Supervisor | Return order with reason | Creator sees returned order and reason |  |  |  |  |  |
| UAT-043 | Branch Supervisor | Reject order with reason | Creator sees rejected order and reason |  |  |  |  |  |

## 5. ERP Sync

| ID | Tester role | Steps | Expected result | Actual result | Pass/Fail | Priority | Notes | Screenshot/reference |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| UAT-050 | Accountant | Create ERP Sales Order draft from approved order | ERP Sales Order reference saved |  |  |  |  |  |
| UAT-051 | Accountant | Submit ERP Sales Order if approved for staging test | Sales Order docstatus becomes submitted |  |  |  |  |  |
| UAT-052 | Accountant | Create Sales Invoice draft after delivery completion | Draft Sales Invoice reference saved |  |  |  |  |  |

## 6. Production

| ID | Tester role | Steps | Expected result | Actual result | Pass/Fail | Priority | Notes | Screenshot/reference |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| UAT-060 | Admin/Production | Create work orders from approved mapped order | Work orders created by department grouping |  |  |  |  |  |
| UAT-061 | Production User | Accept work order | Status becomes accepted and order production status updates |  |  |  |  |  |
| UAT-062 | Production User | Start production | Status becomes in_production |  |  |  |  |  |
| UAT-063 | Production User | Mark ready | Work order ready; order ready when all ready |  |  |  |  |  |
| UAT-064 | Production User | Mark delayed with reason | Status delayed and reason visible |  |  |  |  |  |

## 7. Delivery / Branch Pickup

| ID | Tester role | Steps | Expected result | Actual result | Pass/Fail | Priority | Notes | Screenshot/reference |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| UAT-070 | Delivery User | Create branch transfer batch | Ready branch pickup orders grouped by branch |  |  |  |  |  |
| UAT-071 | Delivery User | Assign driver | Driver sees assigned batch |  |  |  |  |  |
| UAT-072 | Driver | Mark picked up/out for delivery/delivered to branch | Orders become received_at_branch, not customer_picked_up |  |  |  |  |  |
| UAT-073 | Branch User | Mark ready for customer pickup | Order becomes ready_for_customer_pickup |  |  |  |  |  |
| UAT-074 | Branch User | Mark customer picked up | Order becomes customer_picked_up |  |  |  |  |  |
| UAT-075 | Driver | Deliver customer delivery batch | Order becomes delivered_to_customer |  |  |  |  |  |

## 8. Payments

| ID | Tester role | Steps | Expected result | Actual result | Pass/Fail | Priority | Notes | Screenshot/reference |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| UAT-080 | Branch User/Cashier | Collect cash partial payment | paid_amount/remaining/payment_status update |  |  |  |  |  |
| UAT-081 | Branch User/Cashier | Collect card payment | Payment recorded with method card |  |  |  |  |  |
| UAT-082 | Branch User/Cashier | Collect transfer payment | Payment recorded with method transfer |  |  |  |  |  |
| UAT-083 | Branch User/Cashier | Collect online payment | Payment recorded with method online |  |  |  |  |  |
| UAT-084 | Branch User/Cashier | Complete full payment | payment_status becomes paid |  |  |  |  |  |
| UAT-085 | Branch User/Cashier | Try overpayment | Overpayment rejected |  |  |  |  |  |

## 9. Cashbox

| ID | Tester role | Steps | Expected result | Actual result | Pass/Fail | Priority | Notes | Screenshot/reference |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| UAT-090 | Cashier/Branch User | Collect cash payment | Cashbox entry created |  |  |  |  |  |
| UAT-091 | Cashier/Branch User | Submit my cashbox | Cashbox status submitted |  |  |  |  |  |
| UAT-092 | Cashier/Accountant | Approve submitted cashbox | Cashbox status approved |  |  |  |  |  |
| UAT-093 | Cashier/Accountant | Return cashbox with reason | Owner sees returned cashbox and reason |  |  |  |  |  |

## 10. Accounting Finalization

| ID | Tester role | Steps | Expected result | Actual result | Pass/Fail | Priority | Notes | Screenshot/reference |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| UAT-100 | Accountant | Open accounting summary | Readiness flags are understandable |  |  |  |  |  |
| UAT-101 | Accountant | Sync payment entry draft | Draft Payment Entry created and linked |  |  |  |  |  |
| UAT-102 | Accountant | Submit invoice/payment entry only if approved | Submit requires confirmation and updates docstatus |  |  |  |  |  |
| UAT-103 | Accountant | Finalize accounting only if approved | Accounting finalized metadata saved |  |  |  |  |  |

## 11. Notifications

| ID | Tester role | Steps | Expected result | Actual result | Pass/Fail | Priority | Notes | Screenshot/reference |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| UAT-110 | Any target user | Open notifications | Arabic notifications appear |  |  |  |  |  |
| UAT-111 | Any target user | Tap linked notification | Related screen opens or safe access message appears |  |  |  |  |  |
| UAT-112 | Any target user | Mark read / mark all read | Unread count updates |  |  |  |  |  |

## 12. Dashboard and Reports

| ID | Tester role | Steps | Expected result | Actual result | Pass/Fail | Priority | Notes | Screenshot/reference |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| UAT-120 | Authorized user | Open لوحة المتابعة | Cards match role/scope |  |  |  |  |  |
| UAT-121 | Authorized user | Open التقارير | Allowed reports appear |  |  |  |  |  |
| UAT-122 | Authorized user | Change filters | Results update and remain scoped |  |  |  |  |  |

## 13. Settings

| ID | Tester role | Steps | Expected result | Actual result | Pass/Fail | Priority | Notes | Screenshot/reference |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| UAT-130 | Admin | Open settings | Safe non-secret settings visible |  |  |  |  |  |
| UAT-131 | Admin | Update safe setting | Save succeeds and Arabic success message appears |  |  |  |  |  |
| UAT-132 | Non-admin | Try settings | Access denied or card hidden |  |  |  |  |  |

## Exit Decision

| Decision | Selected | Notes |
| --- | --- | --- |
| GO to production setup | [ ] |  |
| NEEDS CHANGES before production | [ ] |  |
| NO-GO due to blockers | [ ] |  |
