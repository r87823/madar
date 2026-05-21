#!/usr/bin/env python3
"""Read-only Madar operational monitoring checks.

Run from a Frappe bench host/container. The script shells out to `bench execute`
for simple count queries and prints counts only, never raw document errors.
"""

from __future__ import annotations

import argparse
import ast
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CountCheck:
    key: str
    table: str
    field: str
    value: str | int
    critical_threshold: int | None = None


CHECKS = [
    CountCheck("order_erp_sync_failed", "tabMadar Order", "erp_sync_status", "failed", 0),
    CountCheck("order_invoice_sync_failed", "tabMadar Order", "erp_invoice_sync_status", "failed", 0),
    CountCheck("payment_erp_sync_failed", "tabMadar Payment", "erp_sync_status", "failed", 0),
    CountCheck("accounting_needs_attention", "tabMadar Order", "accounting_status", "needs_attention", None),
    CountCheck("cashboxes_waiting_review", "tabMadar Cashbox", "status", "submitted", None),
    CountCheck(
        "high_priority_unread_notifications",
        "tabMadar Notification",
        "priority",
        "high",
        None,
    ),
]


def bench_count(bench_path: Path, site: str, check: CountCheck) -> int:
    if check.key == "high_priority_unread_notifications":
        query = f"select count(*) from `{check.table}` where `priority`=%s and `is_read`=0"
        values = ["high"]
    else:
        query = f"select count(*) from `{check.table}` where `{check.field}`=%s"
        values = [check.value]
    args = repr([query, values])
    command = ["bench", "--site", site, "execute", "frappe.db.sql", "--args", args]
    result = subprocess.run(
        command,
        cwd=bench_path,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        print(f"UNKNOWN {check.key}=query_failed")
        raise SystemExit(3)
    output = result.stdout.strip()
    count = _extract_first_int(output)
    if count is None:
        print(f"UNKNOWN {check.key}=invalid_output")
        raise SystemExit(3)
    return count


def _extract_first_int(output: str) -> int | None:
    if not output:
        return None
    try:
        value = ast.literal_eval(output)
    except (SyntaxError, ValueError):
        try:
            return int(output)
        except ValueError:
            return None
    return _first_int(value)


def _first_int(value: object) -> int | None:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, (list, tuple)):
        for item in value:
            found = _first_int(item)
            if found is not None:
                return found
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Madar ERP/accounting monitoring counters.")
    parser.add_argument("--bench-path", default="/home/frappe/frappe-bench")
    parser.add_argument("--site", default="hrms.localhost")
    parser.add_argument(
        "--warn-on-backlog",
        action="store_true",
        help="Return warning if non-critical backlog counters are greater than zero.",
    )
    args = parser.parse_args()

    bench_path = Path(args.bench_path)
    if not bench_path.exists():
        print(f"UNKNOWN bench_path_missing path={bench_path}")
        return 3

    exit_code = 0
    parts: list[str] = []
    for check in CHECKS:
        count = bench_count(bench_path, args.site, check)
        parts.append(f"{check.key}={count}")
        if check.critical_threshold is not None and count > check.critical_threshold:
            exit_code = max(exit_code, 2)
        elif args.warn_on_backlog and count > 0:
            exit_code = max(exit_code, 1)

    status = "OK" if exit_code == 0 else "WARNING" if exit_code == 1 else "CRITICAL"
    print(f"{status} " + " ".join(parts))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
