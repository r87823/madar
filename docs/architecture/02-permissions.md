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

