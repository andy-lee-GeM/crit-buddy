#!/usr/bin/env python3
"""Shared helpers for local handoff package generation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[4]
DEFAULT_OUTPUT_ROOT = ROOT / "models" / "handoffs"


@dataclass(frozen=True)
class StudySpec:
    slug: str
    report_md: Path
    study_yaml: Path
    results_csv: Path
    plot_x_field: str
    plot_x_label: str
    plot_filename: str
    plot_title: str
    source_tree: Path
    reuse_plot: Path | None = None


@dataclass(frozen=True)
class ModelSpec:
    name: str
    title: str
    handoff_md: Path
    openmc_model: Path
    mcnp_model: Path
    benchmark_root: Path
    benchmark_results_md: Path
    benchmark_study_yaml: Path
    benchmark_results_csv: Path
    benchmark_plot: Path
    sensitivity_studies: tuple[StudySpec, ...]


PIPE_BENCHMARK_ROOT = ROOT / "certifications" / "pipe-cross-model" / "2026-03-30-r1"
CENTRIFUGE_BENCHMARK_ROOT = ROOT / "certifications" / "centrifuge-unit-cell" / "2026-03-30-r1"


MODEL_SPECS: dict[str, ModelSpec] = {
    "pipe-cross-model": ModelSpec(
        name="pipe-cross-model",
        title="Pipe Cross Model",
        handoff_md=ROOT / "models" / "pipe-cross-model" / "HANDOFF.md",
        openmc_model=ROOT / "models" / "pipe-cross-model" / "openmc" / "model.py",
        mcnp_model=ROOT / "models" / "pipe-cross-model" / "mcnp" / "reference.inp",
        benchmark_root=PIPE_BENCHMARK_ROOT,
        benchmark_results_md=PIPE_BENCHMARK_ROOT / "results.md",
        benchmark_study_yaml=PIPE_BENCHMARK_ROOT / "openmc" / "study.yaml",
        benchmark_results_csv=PIPE_BENCHMARK_ROOT / "openmc" / "results" / "results.csv",
        benchmark_plot=PIPE_BENCHMARK_ROOT / "openmc" / "results" / "plots" / "keff_vs_separation_cm.png",
        sensitivity_studies=(
            StudySpec(
                slug="pipe-cross-hu-sweep",
                report_md=ROOT / "studies" / "pipe-cross-hu-sweep" / "report.md",
                study_yaml=ROOT / "studies" / "pipe-cross-hu-sweep" / "study.yaml",
                results_csv=ROOT
                / "studies"
                / "pipe-cross-hu-sweep"
                / "runs"
                / "study"
                / "2026-03-24_15-24-53"
                / "results.csv",
                plot_x_field="h_to_u",
                plot_x_label="H/U",
                plot_filename="keff_vs_h_to_u.png",
                plot_title="Pipe Cross H/U Sweep",
                source_tree=ROOT / "studies" / "pipe-cross-hu-sweep",
            ),
        ),
    ),
    "centrifuge-unit-cell": ModelSpec(
        name="centrifuge-unit-cell",
        title="Centrifuge Unit Cell",
        handoff_md=ROOT / "models" / "centrifuge-unit-cell" / "HANDOFF.md",
        openmc_model=ROOT / "models" / "centrifuge-unit-cell" / "openmc" / "model.py",
        mcnp_model=ROOT / "models" / "centrifuge-unit-cell" / "mcnp" / "model.inp",
        benchmark_root=CENTRIFUGE_BENCHMARK_ROOT,
        benchmark_results_md=CENTRIFUGE_BENCHMARK_ROOT / "results.md",
        benchmark_study_yaml=CENTRIFUGE_BENCHMARK_ROOT / "openmc" / "study.yaml",
        benchmark_results_csv=CENTRIFUGE_BENCHMARK_ROOT / "openmc" / "results" / "results.csv",
        benchmark_plot=CENTRIFUGE_BENCHMARK_ROOT
        / "openmc"
        / "results"
        / "plots"
        / "keff_vs_fill_z_cm.png",
        sensitivity_studies=(
            StudySpec(
                slug="fill-height-benchmark",
                report_md=CENTRIFUGE_BENCHMARK_ROOT / "results.md",
                study_yaml=CENTRIFUGE_BENCHMARK_ROOT / "openmc" / "study.yaml",
                results_csv=CENTRIFUGE_BENCHMARK_ROOT / "openmc" / "results" / "results.csv",
                plot_x_field="fill_z_cm",
                plot_x_label="Fill Height (cm)",
                plot_filename="keff_vs_fill_z_cm.png",
                plot_title="Centrifuge Fill Height Sweep",
                source_tree=CENTRIFUGE_BENCHMARK_ROOT,
                reuse_plot=CENTRIFUGE_BENCHMARK_ROOT
                / "openmc"
                / "results"
                / "plots"
                / "keff_vs_fill_z_cm.png",
            ),
        ),
    ),
}


def get_model_spec(model_name: str) -> ModelSpec:
    try:
        return MODEL_SPECS[model_name]
    except KeyError as exc:
        available = ", ".join(sorted(MODEL_SPECS))
        raise SystemExit(f"Unsupported model '{model_name}'. Available: {available}") from exc


def package_root(output_root: Path, model_name: str) -> Path:
    return output_root / model_name


def reset_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_text(path: Path, content: str) -> None:
    ensure_parent(path)
    path.write_text(content, encoding="utf-8")

