import re
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "get_mcnp_density.py"


class GetMCNPDensityScriptTests(unittest.TestCase):
    def run_script(self, *args: str) -> str:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=ROOT,
            capture_output=True,
            check=True,
            text=True,
        )
        return result.stdout

    def test_uo2f2_derives_bulk_density_from_h_to_u(self):
        stdout = self.run_script("uo2f2", "-enrichment", "20", "-hu", "3")

        self.assertIn("uo2f2_enr_20.0wt  |  m1", stdout)
        self.assertIn("Bulk density          : 5.63436476e+00  g/cc", stdout)
        self.assertIn("MCNP atom density     : 9.63815207e-02  atoms/b-cm", stdout)
        self.assertRegex(stdout, r"H/U\s*:\s*3(?:\.0+)?")
        self.assertRegex(stdout, r"Density Basis\s*:\s*derived_from_h_to_u")
        self.assertNotIn("uo2f2_enr_5.0wt", stdout)
        self.assertIn("U235", stdout)
        self.assertIn("U238", stdout)

    def test_uo2f2_explicit_density_override_wins_over_h_to_u(self):
        stdout = self.run_script(
            "uo2f2",
            "-enrichment",
            "20",
            "-hu",
            "3",
            "--uo2f2-density",
            "5.1",
        )

        self.assertIn("Bulk density          : 5.10000000e+00  g/cc", stdout)
        self.assertIn("MCNP cell density     : -5.10000000e+00  g/cc", stdout)
        self.assertRegex(stdout, r"Density Basis\s*:\s*user_specified_uo2f2_density")
        atom_density_match = re.search(
            r"MCNP atom density\s*:\s*([0-9.]+e[+-][0-9]+)\s+atoms/b-cm",
            stdout,
        )
        self.assertIsNotNone(atom_density_match)


if __name__ == "__main__":
    unittest.main()
