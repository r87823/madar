#!/usr/bin/env python3
"""Lightweight Madar security rule scan.

This is intentionally conservative: it catches obvious drift in the rules that
matter most before production, without trying to replace code review.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


ALLOWED_GUEST_FILES = {Path("madar/api/health.py")}
ROLE_ALLOWED_PARTS = {
    "madar/permissions/registry.py",
    "madar/permissions/roles.py",
    "madar/dev/bootstrap_users.py",
    "madar/patches/v0_0/create_madar_roles.py",
    "madar/tests/",
    "docs/",
}
MADAR_ROLE_NAMES = {
    "Madar Admin",
    "Madar Employee",
    "Madar Branch User",
    "Madar Branch Supervisor",
    "Madar Production User",
    "Madar Driver",
    "Madar Cashier",
    "Madar Accountant",
}
FLUTTER_ALLOWED_PARTS = {"test/"}
SECRET_ALLOWED_PARTS = {
    "scripts/check_security_rules.py",
    "madar/tests/",
    "test/",
    "docs/",
    "lib/features/auth/login_screen.dart",
    "lib/core/auth/auth_controller.dart",
    "lib/core/api/frappe_api_client.dart",
}
SKIP_DIRS = {
    ".dart_tool",
    ".git",
    "__pycache__",
    "build",
    "node_modules",
    ".venv",
    "venv",
}
TEXT_SUFFIXES = {".py", ".dart", ".md", ".txt", ".json", ".yaml", ".yml", ".toml"}


@dataclass(frozen=True)
class Issue:
    code: str
    path: str
    line: int
    message: str


@dataclass(frozen=True)
class ScanResult:
    issues: list[Issue]

    @property
    def ok(self) -> bool:
        return not self.issues


def scan_repo(root: Path) -> ScanResult:
    root = root.resolve()
    issues: list[Issue] = []
    for path in _iter_text_files(root):
        rel = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8", errors="ignore")
        issues.extend(_scan_guest_endpoints(rel, text))
        issues.extend(_scan_flutter_erp_access(rel, text))
        issues.extend(_scan_direct_role_checks(rel, text))
        issues.extend(_scan_obvious_secrets(rel, text))
    return ScanResult(issues=issues)


def _iter_text_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix in TEXT_SUFFIXES or path.name in {"AGENTS.md", "PLANS.md"}:
            yield path


def _scan_guest_endpoints(rel: str, text: str) -> list[Issue]:
    if not rel.startswith("madar/api/"):
        return []
    if "allow_guest" not in text:
        return []
    rel_path = Path(rel)
    issues = []
    for line_no, line in _matching_lines(text, r"allow_guest\s*=\s*(True|1)"):
        if rel_path not in ALLOWED_GUEST_FILES:
            issues.append(
                Issue(
                    "UNSAFE_GUEST_ENDPOINT",
                    rel,
                    line_no,
                    "Only madar/api/health.py may use allow_guest=True.",
                )
            )
    return issues


def _scan_flutter_erp_access(rel: str, text: str) -> list[Issue]:
    if not rel.startswith("lib/") and not rel.startswith("test/"):
        return []
    if _is_allowed(rel, FLUTTER_ALLOWED_PARTS):
        return []
    patterns = [
        r"/api/resource",
        r"\bSales Order\b",
        r"\bSales Invoice\b",
        r"\bPayment Entry\b",
        r"\bDelivery Note\b",
        r"\bStock Entry\b",
    ]
    issues = []
    for pattern in patterns:
        for line_no, _line in _matching_lines(text, pattern):
            issues.append(
                Issue(
                    "FLUTTER_DIRECT_ERP_ACCESS",
                    rel,
                    line_no,
                    "Flutter must call Madar whitelisted methods, not ERPNext resources or DocTypes.",
                )
            )
    return issues


def _scan_direct_role_checks(rel: str, text: str) -> list[Issue]:
    if not (rel.startswith("madar/services/") or rel.startswith("madar/api/")):
        return []
    if _is_allowed(rel, ROLE_ALLOWED_PARTS):
        return []
    issues = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        if any(role_name in line for role_name in MADAR_ROLE_NAMES) or re.search(
            r"\brole\s*(==|!=)|\b['\"][^'\"]+['\"]\s+in\s+roles\b", line
        ):
            issues.append(
                Issue(
                    "DIRECT_ROLE_CHECK",
                    rel,
                    line_no,
                    "Protected logic must use permission keys/helpers instead of direct role checks.",
                )
            )
    return issues


def _scan_obvious_secrets(rel: str, text: str) -> list[Issue]:
    if _is_allowed(rel, SECRET_ALLOWED_PARTS):
        return []
    patterns = [
        r"MADAR_SSH_PASSWORD",
        r"sshpass",
        r"BEGIN (RSA |OPENSSH |EC |DSA )?PRIVATE KEY",
        r"r8787m@",
        r"api[_-]?secret\s*[:=]\s*['\"][^'\"]+['\"]",
        r"api[_-]?key\s*[:=]\s*['\"][^'\"]+['\"]",
        r"password\s*[:=]\s*['\"][^'\"]+['\"]",
        r"token\s*[:=]\s*['\"][^'\"]+['\"]",
    ]
    issues = []
    for pattern in patterns:
        for line_no, _line in _matching_lines(text, pattern):
            issues.append(
                Issue(
                    "POTENTIAL_SECRET",
                    rel,
                    line_no,
                    "Potential credential-like value found; review without printing the value.",
                )
            )
    return issues


def _matching_lines(text: str, pattern: str):
    regex = re.compile(pattern, re.IGNORECASE)
    for index, line in enumerate(text.splitlines(), start=1):
        if regex.search(line):
            yield index, line


def _is_allowed(rel: str, allowed_parts: set[str]) -> bool:
    return any(rel == part or rel.startswith(part) for part in allowed_parts)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Madar security rule checks.")
    parser.add_argument("root", nargs="?", default=".", help="Repository root")
    args = parser.parse_args(argv)
    result = scan_repo(Path(args.root))
    if result.ok:
        print("Security scan passed: no issues found.")
        return 0
    print(f"Security scan found {len(result.issues)} issue(s):")
    for issue in result.issues:
        print(f"{issue.code}: {issue.path}:{issue.line}: {issue.message}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
