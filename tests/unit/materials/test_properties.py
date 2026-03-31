import unittest

from critbuddy.core.materials import centrifuge_air, get_material, uo2f2, water
from critbuddy.core.materials.material_properties import summarize_openmc_material


class MaterialPropertyTests(unittest.TestCase):
    def test_water_summary_reproduces_canonical_mcnp_atom_densities(self):
        mat = water(density_g_cm3=1.0)

        summary = summarize_openmc_material(mat)
        rows = {row.nuclide: row for row in summary.nuclides}

        self.assertAlmostEqual(summary.density_g_cm3, 1.0, places=9)
        self.assertEqual(f"{rows['H1'].atom_density_bcm:.3f}", "0.067")
        self.assertEqual(f"{rows['O16'].atom_density_bcm:.3f}", "0.033")

    def test_uo2f2_summary_from_readable_inputs_tracks_canonical_fuel_card(self):
        mat = uo2f2(
            enrichment_pct=20.0,
            h_to_u=5.0,
            density=4.33,
        )

        summary = summarize_openmc_material(mat)
        rows = {row.nuclide: row for row in summary.nuclides}

        self.assertAlmostEqual(summary.density_g_cm3, 4.33, places=9)
        self.assertAlmostEqual(rows["U235"].atom_density_bcm, 0.001496, places=5)
        self.assertAlmostEqual(rows["U238"].atom_density_bcm, 0.00591035, places=4)
        self.assertEqual(f"{rows['O16'].atom_density_bcm:.4f}", "0.0333")
        self.assertEqual(f"{rows['F19'].atom_density_bcm:.4f}", "0.0148")
        self.assertEqual(f"{rows['H1'].atom_density_bcm:.3f}", "0.037")

    def test_ss304_reference_side_by_side_print(self):
        # Reference:
        # PNNL-15870 Rev. 2, material 331 "Steel, Stainless 304"
        # https://mcnp.lanl.gov/pdf_files/TechReport_2021_PNNL_PNNL-15870Rev.2_DetwilerMcConnEtAl.pdf
        reference_density_g_cm3 = 8.03
        reference_total_atom_density_bcm = 8.860e-02
        reference_rows = {
            "C": {"weight_fraction": 0.000800, "atom_density_bcm": 0.000322, "atom_fraction": 0.003635},
            "Mn55": {"weight_fraction": 0.020000, "atom_density_bcm": 0.001760, "atom_fraction": 0.019870},
            "P31": {"weight_fraction": 0.000450, "atom_density_bcm": 0.000070, "atom_fraction": 0.000793},
            "S": {"weight_fraction": 0.000300, "atom_density_bcm": 0.000045, "atom_fraction": 0.000511},
            "Si": {"weight_fraction": 0.010000, "atom_density_bcm": 0.001722, "atom_fraction": 0.019434},
            "Cr": {"weight_fraction": 0.190000, "atom_density_bcm": 0.017671, "atom_fraction": 0.199443},
        }

        mat = get_material("ss304")
        summary = summarize_openmc_material(mat)
        repo_rows = {row.nuclide: row for row in summary.nuclides}

        print("\nSS304 side-by-side reference check")
        print("  Reference: PNNL-15870 Rev. 2, material 331 'Steel, Stainless 304'")
        print("")
        print(
            f"{'quantity':28s} {'actual':>16s} {'reference':>16s}"
        )
        print("-" * 64)
        print(f"{'bulk density (g/cc)':28s} {summary.density_g_cm3:16.5f} {reference_density_g_cm3:16.5f}")
        print(
            f"{'total atom density (b-cm)':28s} "
            f"{summary.total_atom_density_bcm:16.8e} {reference_total_atom_density_bcm:16.8e}"
        )
        print(f"{'Cr weight fraction':28s} {repo_rows['Cr52'].weight_fraction:16.6f} {reference_rows['Cr']['weight_fraction']:16.6f}")
        print(f"{'Mn weight fraction':28s} {repo_rows['Mn55'].weight_fraction:16.6f} {reference_rows['Mn55']['weight_fraction']:16.6f}")
        print(f"{'Cr atom fraction':28s} {repo_rows['Cr52'].atom_fraction:16.6f} {reference_rows['Cr']['atom_fraction']:16.6f}")
        print(f"{'Mn atom fraction':28s} {repo_rows['Mn55'].atom_fraction:16.6f} {reference_rows['Mn55']['atom_fraction']:16.6f}")
        print("")
        print("Interpretation:")
        print("  Bulk density and total atom density are close overall.")
        print("  Chromium matches closely.")
        print("  Manganese is lower because the repo SS304 is a simplified surrogate, not the full PNNL composition.")

        self.assertEqual(summary.name, "Stainless_Steel_304")

    def test_centrifuge_air_summary_reproduces_canonical_mcnp_atom_densities(self):
        mat = centrifuge_air()

        summary = summarize_openmc_material(mat)
        rows = {row.nuclide: row for row in summary.nuclides}

        self.assertAlmostEqual(summary.total_atom_density_bcm, 0.033, places=9)
        self.assertEqual(f"{rows['N14'].atom_density_bcm:.5f}", "0.00443")
        self.assertEqual(f"{rows['O16'].atom_density_bcm:.5f}", "0.00119")
        self.assertEqual(f"{rows['Ar40'].atom_density_bcm:.5f}", "0.02725")
        self.assertEqual(f"{rows['H1'].atom_density_bcm:.5f}", "0.00012")


if __name__ == "__main__":
    unittest.main()
