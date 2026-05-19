# Production Services

R4-T01 creates the production mapping foundation. R4-T02 adds Madar operational department work orders. Production remains separate from ERPNext manufacturing, stock, delivery, invoice, payment, and payroll behavior.

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

Inactive mappings are treated as missing. The helper is a gate for production work order creation.

## Department Work Orders

R4-T02 adds Madar operational work orders grouped by `production_center` and `production_department`. Creation starts from an approved `Madar Order` only after item department mappings validate successfully.

Creation is idempotent per Madar Order. If work orders already exist for the order, the service returns the existing rows rather than creating duplicates. If any order item has no active mapping, no work orders are created and the response returns `missing_item_codes`.

Lifecycle transitions are intentionally small:

- `pending` -> `accepted`.
- `accepted` -> `in_production`.
- `in_production` -> `ready`.
- `pending` or `in_production` -> `delayed`.

Delay requires a reason. All mutations should add an audit comment when the Frappe document supports it.

## API Boundary

All production mapping APIs are authenticated Frappe whitelisted methods under `madar.api.production_mapping`. The API layer only authenticates and delegates to `madar.services.production_mapping_service`.

Required permissions:

- View active centers/departments: `production.view_work_orders`, `production.manage_mappings`, or `system.full_access`.
- Manage centers, departments, mappings, and validation: `production.manage_mappings` or `system.full_access`.

No endpoint performs direct role checks.

## ERP Boundary

Madar Work Orders are not ERPNext Work Orders. R4-T02 must not create ERPNext manufacturing work orders, BOMs, stock reservations, delivery records, invoices, payment entries, payroll records, or cashbox documents.
