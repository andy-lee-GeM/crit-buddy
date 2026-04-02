#!/usr/bin/env python3
"""Collect runnable models, selected artifacts, figures, and heavier data."""

from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path
import shutil
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")
import matplotlib.pyplot as plt

from _handoff_common import DEFAULT_OUTPUT_ROOT, get_model_spec, package_root


def _copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def _copy_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def _copy_minimal_benchmark(spec, out_root: Path) -> None:
    benchmark_root = out_root / "data" / "benchmark"
    openmc_root = benchmark_root / "openmc"
    mcnp_root = benchmark_root / "mcnp"

    _copy_file(spec.benchmark_root / "openmc" / "model.py", openmc_root / "model.py")
    _copy_file(spec.benchmark_study_yaml, openmc_root / "study.yaml")
    _copy_tree(spec.benchmark_root / "openmc" / "cases", openmc_root / "cases")
    _copy_tree(spec.benchmark_root / "openmc" / "results", openmc_root / "results")
    _copy_tree(spec.benchmark_root / "mcnp", mcnp_root)
    _copy_file(spec.benchmark_results_md, benchmark_root / "results.md")


def _copy_minimal_sensitivity(study, out_root: Path) -> None:
    sensitivity_root = out_root / "data" / "sensitivities" / study.slug
    _copy_file(study.report_md, sensitivity_root / "report.md")
    _copy_file(study.study_yaml, sensitivity_root / "study.yaml")
    _copy_file(study.results_csv, sensitivity_root / "results.csv")


def _plot_results_csv(csv_path: Path, x_field: str, x_label: str, title: str, output_path: Path) -> None:
    with csv_path.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    rows.sort(key=lambda row: float(row[x_field]))
    xs = [float(row[x_field]) for row in rows]
    ys = [float(row["keff"]) for row in rows]
    yerr = [float(row["std"]) for row in rows]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.errorbar(xs, ys, yerr=yerr, marker="o", linewidth=1.5, capsize=3)
    ax.set_xlabel(x_label)
    ax.set_ylabel("k-effective")
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def collect_handoff_artifacts(model_name: str, output_root: Path = DEFAULT_OUTPUT_ROOT) -> Path:
    spec = get_model_spec(model_name)
    out_root = package_root(output_root, model_name)

    _copy_file(spec.openmc_model, out_root / "models" / "model.py")
    _copy_file(spec.mcnp_model, out_root / "models" / "model.inp")

    _copy_file(spec.benchmark_results_md, out_root / "artifacts" / "benchmark" / "results.md")
    _copy_file(spec.benchmark_study_yaml, out_root / "artifacts" / "benchmark" / "study.yaml")
    _copy_file(spec.benchmark_plot, out_root / "figures" / "benchmark" / spec.benchmark_plot.name)

    _copy_minimal_benchmark(spec, out_root)

    for study in spec.sensitivity_studies:
        _copy_file(
            study.report_md,
            out_root / "artifacts" / "sensitivities" / f"{study.slug}-report.md",
        )
        _copy_file(
            study.study_yaml,
            out_root / "artifacts" / "sensitivities" / f"{study.slug}-study.yaml",
        )
        if study.reuse_plot is not None:
            _copy_file(
                study.reuse_plot,
                out_root / "figures" / "sensitivities" / study.plot_filename,
            )
        else:
            _plot_results_csv(
                study.results_csv,
                study.plot_x_field,
                study.plot_x_label,
                study.plot_title,
                out_root / "figures" / "sensitivities" / study.plot_filename,
            )
        _copy_minimal_sensitivity(study, out_root)
    return out_root


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    args = parser.parse_args()
    collect_handoff_artifacts(args.model, args.output_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
