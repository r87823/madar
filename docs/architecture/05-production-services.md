# Production Services

R4-T01 creates the production mapping foundation only. It does not create production work orders or trigger stock, delivery, invoice, payment, or accounting behavior.

## Ownership

Madar owns production operational workflow state. ERPNext remains the source of truth for `Item`, stock, warehouses, and commercial documents. Flutter must access production setup through Madar APIs only.

## Master Data

Madar defines three setup DocTypes:

- `Madar Production Center`: production site or facility grouping.
- `Madar Production Department`: active department inside a production center.
- `Madar Item Department Mapping`: one active item-to-production-department mapping per item code.

Mappings reference ERPNext item codes but do not mutate ERPNext items.

## Validation Boundary

`validate_order_department_mappings(order_name)` checks an approved `Madar Order` and returns:

- `is_valid`.
- `missing_item_codes`.
- `mapped_item_codes`.

Inactive mappings are treated as missing. The helper is a gate for future production work order creation, but R4-T01 intentionally stops at validation.

## API Boundary

All production mapping APIs are authenticated Frappe whitelisted methods under `madar.api.production_mapping`. The API layer only authenticates and delegates to `madar.services.production_mapping_service`.

Required permissions:

- View active centers/departments: `production.view_work_orders`, `production.manage_mappings`, or `system.full_access`.
- Manage centers, departments, mappings, and validation: `production.manage_mappings` or `system.full_access`.

No endpoint performs direct role checks.
