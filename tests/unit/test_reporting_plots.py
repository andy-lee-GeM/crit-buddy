import csv
import tempfile
import unittest
from pathlib import Path

from critbuddy.reporting import plot_keff_diagram
from critbuddy.reporting.plots import main


class ReportingPlotsTests(unittest.TestCase):
    def test_plot_keff_diagram_writes_single_plot(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            results_csv = tmp_path / "results.csv"
            output_path = tmp_path / "keff.png"
            self._write_csv(
                results_csv,
                headers=["fill_fraction_percent", "keff", "std", "keff_2sigma", "status", "solver"],
                rows=[
                    ["3.0", "0.71707", "0.00110", "0.71927", "SAFE", "openmc"],
                    ["100.0", "1.14043", "0.00110", "1.14263", "CRITICAL", "openmc"],
                ],
            )

            returned_path = plot_keff_diagram(results_csv, output_path)

            self.assertEqual(returned_path, output_path)
            self.assertTrue(output_path.exists())
            self.assertGreater(output_path.stat().st_size, 0)

    def test_plot_keff_cli_writes_grouped_plot(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            results_csv = tmp_path / "results.csv"
            output_path = tmp_path / "grouped.png"
            self._write_csv(
                results_csv,
                headers=["fill_fraction_percent", "fill_height_cm", "keff", "std", "keff_2sigma", "status", "solver"],
                rows=[
                    ["3.0", "9.0678", "0.71707", "0.00110", "0.71927", "SAFE", "openmc"],
                    ["4.0", "9.0678", "0.73000", "0.00110", "0.73220", "SAFE", "openmc"],
                    ["3.0", "12.0904", "0.80000", "0.00110", "0.80220", "SAFE", "openmc"],
                    ["4.0", "12.0904", "0.82000", "0.00110", "0.82220", "SAFE", "openmc"],
                ],
            )

            exit_code = main(
                [
                    "keff",
                    str(results_csv),
                    "--output",
                    str(output_path),
                    "--x",
                    "fill_fraction_percent",
                    "--group-by",
                    "fill_height_cm",
                ]
            )

            self.assertEqual(exit_code, 0)
            self.assertTrue(output_path.exists())
            self.assertGreater(output_path.stat().st_size, 0)

    def test_plot_keff_cli_treats_fill_fraction_and_fill_height_as_single_sweep(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            results_csv = tmp_path / "results.csv"
            output_path = tmp_path / "fill_fraction.png"
            self._write_csv(
                results_csv,
                headers=["fill_fraction_percent", "fill_height_cm", "keff", "std", "keff_2sigma", "status", "solver"],
                rows=[
                    ["0.1", "0.30226", "0.02832", "0.00015", "0.02863", "SAFE", "openmc"],
                    ["0.5", "1.5113", "0.17278", "0.00056", "0.17389", "SAFE", "openmc"],
                    ["1.0", "3.0226", "0.38119", "0.00087", "0.38292", "SAFE", "openmc"],
                    ["2.0", "6.0452", "0.71343", "0.00121", "0.71585", "SAFE", "openmc"],
                ],
            )

            exit_code = main(
                [
                    "keff",
                    str(results_csv),
                    "--output",
                    str(output_path),
                    "--x",
                    "fill_fraction_percent",
                ]
            )

            self.assertEqual(exit_code, 0)
            self.assertTrue(output_path.exists())
            self.assertGreater(output_path.stat().st_size, 0)

    def _write_csv(self, path: Path, *, headers: list[str], rows: list[list[str]]) -> None:
        with path.open("w", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(headers)
            writer.writerows(rows)


if __name__ == "__main__":
    unittest.main()
