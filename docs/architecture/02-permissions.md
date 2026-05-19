# Permissions

Madar uses Frappe DocTypes and Frappe permissions as the base authorization model. Protected actions must not rely on direct role checks inside endpoint functions.

## Rules

- Use Frappe DocType permissions wherever possible.
- Use permission helper functions from `madar.permissions` for protected server-side decisions.
- Do not check roles directly in mobile endpoints for protected actions.
- Do not trust Flutter to enforce authorization.
- Apply authorization before sensitive reads, sensitive mutations, and workflow transitions.

## Permission Helper Pattern

Future helpers should answer capability questions in domain language, such as whether the current user can approve a workflow transition or access an employee self-service resource.

Helpers should:

- Accept explicit inputs such as user, document, action, and context.
- Return a clear allow or deny result.
- Raise or map denials to stable mobile error codes at the API boundary.
- Be covered by tests when behavior is added.

## Permission Registry

Madar exposes app-level permission keys from `madar.permissions.registry`. These keys are the contract future protected workflows should use instead of checking roles directly in endpoint code.

Initial permission keys include:

- `system.full_access`.
- `attendance.check_in`.
- `attendance.check_out`.
- `employee_services.view_self`.
- `employee_services.request_leave`.
- `orders.create`.
- `orders.submit_for_approval`.
- `orders.approve`.
- `production.view_work_orders`.
- `production.update_work_order`.
- `production.manage_mappings`.
- `delivery.view_assigned_batches`.
- `delivery.update_batch`.
- `payments.collect`.
- `cashbox.view_own`.
- `cashbox.submit`.
- `accounting.view_sync_logs`.

The current registry maps these keys to Frappe roles as a foundation step. `system.full_access` grants every Madar permission key. Future tasks may replace or extend this mapping with DocType-backed rules, but endpoint code should continue to ask permission-key questions.

## Madar Roles

Madar bootstraps app-specific Frappe Roles during migration:

- `Madar Admin`.
- `Madar Employee`.
- `Madar Branch User`.
- `Madar Branch Supervisor`.
- `Madar Production User`.
- `Madar Driver`.
- `Madar Cashier`.
- `Madar Accountant`.

These roles are created idempotently. If a role already exists, migration keeps it and continues. The bootstrap must not assign roles to users, create users, or create Employee records.

The permission registry maps Madar roles to permission keys:

- `Madar Admin` grants `system.full_access`.
- `Madar Employee` grants attendance check-in/check-out and employee self-service permissions.
- `Madar Branch User` grants order create and submit-for-approval permissions.
- `Madar Branch Supervisor` grants order approval permission.
- `Madar Production User` grants production work-order view/update permissions.
- `Madar Driver` grants delivery batch update, payment collection, and own cashbox submit permissions.
- `Madar Cashier` grants payment collection and own cashbox submit permissions.
- `Madar Accountant` grants accounting sync log view permission.

Frappe built-in `Administrator`, `System Manager`, and `Employee` mappings remain supported for compatibility and system administration. Future protected actions should use permission keys and scope helpers, not raw role checks.

## Development Test Role Assignments

Development/staging bootstrap may create explicitly marked test users and assign Madar roles for endpoint verification. This bootstrap must be opt-in, idempotent, and limited to safe User and Employee context records. It must not create production business documents, assign roles to real users, or store passwords in project files.

## Current User Context

The authenticated mobile context endpoint is:

```text
/api/method/madar.api.me.get_context
```

It returns the current Frappe user, display name, roles, Madar permission keys, optional safe Employee context, and optional safe Branch context. It must not expose passwords, API keys, API secrets, sensitive HR fields, or session internals.

The context response also includes a `scopes` object:

```json
{
  "branch_names": [],
  "department_names": []
}
```

For regular users, scope values come from safe Employee context fields. For users with `system.full_access`, scope helpers may return wildcard values:

```json
{
  "branch_names": ["*"],
  "department_names": ["*"]
}
```

Future order, delivery, payment, cashbox, production, approval, notification, attendance, and leave workflows should consume permission keys and scope helpers instead of checking Frappe roles directly.

## Order Draft Permissions and Scopes

R3-T01 introduces `Madar Order` as a Madar-owned operational document. Order APIs must use permission keys and scope helpers:

- `orders.create` allows creating draft orders and cancelling still-draft orders.
- `orders.submit_for_approval` allows moving a draft order to `submitted`.
- `system.full_access` may view all Madar orders.
- Branch-scoped users may view orders assigned to their scoped branch.
- Users without branch scope may view only their own created orders.

Endpoint code must not check raw Frappe roles for order actions. The API layer delegates to `madar.services.order_service`, which performs permission and scope decisions before reads or mutations.

R3-T02 order item APIs reuse the same order permissions and scopes:

- `orders.create` allows browsing the safe catalog bridge and mutating line items on editable orders.
- Only scoped orders may be read or mutated.
- Item mutations are allowed only while the order is `draft` or `returned_for_edit`.
- `submitted` and `cancelled` orders reject item mutations.
- Totals are recalculated in `madar.services.order_item_service`, not in Flutter or API wrappers.

R3-T03 approval APIs use:

- `orders.submit_for_approval` to submit `draft` or `returned_for_edit` orders.
- `orders.approve` to list the approval queue and approve, return, or reject submitted orders.
- Approval queue visibility is branch-scoped for supervisors and wildcard-scoped for `system.full_access`.
- Return and reject decisions require a reason and add an audit comment.
- `approved` and `rejected` orders are not editable by order item APIs.
- Approved orders are operationally frozen and receive ERP sync metadata for the future server-side sync boundary.
- ERP sync boundary helpers must remain internal service methods until a later task defines protected APIs, jobs, and permissions.
- R3-T05 ERP sync is manual/internal only and has no mobile endpoint. A later task must define explicit admin permissions before exposing sync actions through any API.
- R3-T06 exposes ERP sync review and retry through Madar APIs for accounting/admin users. These APIs require `accounting.view_sync_logs`; endpoint code delegates to `madar.services.erp_sync_service` and must not check raw roles directly.

## Production Mapping Permissions

R4-T01 introduces production master data and item-to-department mapping as a prerequisite for future work orders:

- `production.view_work_orders` may view active production centers and departments.
- `production.manage_mappings` may create or update production centers, production departments, and item department mappings.
- `system.full_access` grants `production.manage_mappings` through the registry, so `Madar Admin`, `Administrator`, and `System Manager` can manage mappings.
- Branch/order users do not manage production mappings.

Production mapping endpoints must not check raw roles directly. The API layer delegates to `madar.services.production_mapping_service`, which evaluates permission keys and returns stable `PERMISSION_DENIED` errors when needed.

## Sensitive Mutations

Any future sensitive mutation must create an audit log. Examples include payment changes, cashbox actions, delivery status changes, production status changes, approval decisions, and employee self-service mutations.

The audit record should capture:

- Actor.
- Action.
- Target document.
- Before and after values when appropriate.
- Request context when safe to store.
- Timestamp.

## Status Transitions

Any future status transition must go through a state machine service. Endpoints and DocType hooks should not independently set workflow status fields for protected operational workflows.

R3-T01 keeps order transitions deliberately small in `madar.services.order_service`:

- `draft` -> `submitted`.
- `draft` -> `cancelled`.
- `cancelled` cannot be submitted.
- `submitted` cannot be cancelled in this phase.
