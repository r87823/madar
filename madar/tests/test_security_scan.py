import tempfile
import textwrap
import unittest
from pathlib import Path

from scripts import check_security_rules


class SecurityScanTest(unittest.TestCase):
    def test_current_repository_passes_security_scan(self):
        result = check_security_rules.scan_repo(Path.cwd())

        self.assertEqual(result.issues, [])

    def test_scan_flags_unsafe_guest_endpoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            api_dir = root / "madar" / "api"
            api_dir.mkdir(parents=True)
            (api_dir / "bad.py").write_text(
                "@frappe.whitelist(allow_guest=True)\ndef unsafe():\n    pass\n",
                encoding="utf-8",
            )

            result = check_security_rules.scan_repo(root)

        self.assertTrue(any(issue.code == "UNSAFE_GUEST_ENDPOINT" for issue in result.issues))

    def test_scan_flags_flutter_direct_erp_resource_access(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            lib_dir = root / "lib"
            lib_dir.mkdir()
            (lib_dir / "bad.dart").write_text(
                "final path = '/api/resource/Sales Order';\n",
                encoding="utf-8",
            )

            result = check_security_rules.scan_repo(root)

        self.assertTrue(any(issue.code == "FLUTTER_DIRECT_ERP_ACCESS" for issue in result.issues))

    def test_scan_flags_direct_madar_role_in_service_logic(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            service_dir = root / "madar" / "services"
            service_dir.mkdir(parents=True)
            (service_dir / "bad_service.py").write_text(
                textwrap.dedent(
                    """
                    def check(roles):
                        return "Madar Driver" in roles
                    """
                ),
                encoding="utf-8",
            )

            result = check_security_rules.scan_repo(root)

        self.assertTrue(any(issue.code == "DIRECT_ROLE_CHECK" for issue in result.issues))


if __name__ == "__main__":
    unittest.main()
