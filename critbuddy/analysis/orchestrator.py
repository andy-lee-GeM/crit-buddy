#!/usr/bin/env python3
"""
Standard Analysis Orchestrator

Runs the 4-step criticality safety analysis workflow:
1. UF6 Dry - Geometry sweep at 100% fill
2. H/U Sweep - Find peak moderation
3. UO2F2 Wet - Geometry sweep at peak H/U
4. Fill Sweep - Find critical threshold at worst-case geometry

Usage:
    from critbuddy.analysis.orchestrator import run_standard_analysis

    run_standard_analysis(
        ticket_id="CR-010",
        template="pipe_array_3d",
        enrichment=21,
        geometry_params={
            "pipe_size": [4, 6],
            "gap_cm": [1, 2, 6],
            "num_pipes": 2,
            "rows": 3,
            "length_cm": 900,
        }
    )
"""

import csv
import subprocess
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional


# Base paths
CRIT_BUDDY_ROOT = Path(__file__).parent.parent.parent
EXPERIMENTS_DIR = CRIT_BUDDY_ROOT / "experiments" / "crit_requests"
PYTHON_EXE = "/home/andylee/anaconda3/envs/openmc-env/bin/python"
RUN_STUDY = CRIT_BUDDY_ROOT / "run_study.py"


def load_results(results_csv: Path) -> List[Dict[str, Any]]:
    """Load results from CSV file."""
    if not results_csv.exists():
        return []
    with open(results_csv, 'r') as f:
        reader = csv.DictReader(f)
        return list(reader)


def find_latest_run(run_dir: Path) -> Optional[Path]:
    """Find the latest run directory."""
    if not run_dir.exists():
        return None
    latest_link = run_dir / "latest"
    if latest_link.exists():
        return latest_link
    dirs = [d for d in run_dir.iterdir() if d.is_dir() and d.name[0].isdigit()]
    if not dirs:
        return None
    return max(dirs, key=lambda d: d.name)


def run_config(config_path: Path, smoke: bool = False) -> bool:
    """Run a single experiment config."""
    cmd = [PYTHON_EXE, str(RUN_STUDY), str(config_path)]
    if smoke:
        cmd.append("--smoke")

    print(f"\n{'='*60}")
    print(f"Running: {config_path.name}")
    print(f"{'='*60}")

    result = subprocess.run(cmd, cwd=str(CRIT_BUDDY_ROOT))
    return result.returncode == 0


def generate_config(
    output_path: Path,
    template: str,
    name: str,
    fissile_material: str,
    enrichment: float,
    geometry_params: Dict[str, Any],
    fill_fraction: Any = 1.0,
    h_to_u: Any = 0,
    fissile_density: float = 5.09,
) -> None:
    """Generate a YAML config file."""

    config = {
        "problem": template,
        "name": name,
        "fissile_material": fissile_material,
        "fissile_density": fissile_density,
        "fill_fraction": fill_fraction,
        "enrichment": enrichment,
        "environment_material": "humid_air",
        "reflector_thickness_cm": 30,
        "wall_material": "ss304",
    }

    # Add H/U ratio for UO2F2
    if fissile_material == "uo2f2":
        config["h_to_u"] = h_to_u

    # Add geometry parameters
    config.update(geometry_params)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    print(f"Generated: {output_path}")


def run_standard_analysis(
    ticket_id: str,
    template: str,
    enrichment: float,
    geometry_params: Dict[str, Any],
    swept_params: List[str],
    smoke: bool = False,
) -> Dict[str, Any]:
    """
    Run the standard 4-step analysis.

    Args:
        ticket_id: YouTrack ticket ID (e.g., "CR-010")
        template: Problem template name
        enrichment: Enrichment percentage
        geometry_params: Dict of geometry parameters (some may be lists for sweeping)
        swept_params: List of parameter names that are being swept
        smoke: If True, run smoke test (1 case, minimal particles)

    Returns:
        Dict with analysis results and paths
    """

    # Create experiment directory
    exp_name = f"{ticket_id}_{template}"
    exp_dir = EXPERIMENTS_DIR / exp_name
    config_dir = exp_dir / "_config"
    runs_dir = exp_dir / "runs"

    exp_dir.mkdir(parents=True, exist_ok=True)
    config_dir.mkdir(exist_ok=True)

    results = {
        "ticket_id": ticket_id,
        "template": template,
        "enrichment": enrichment,
        "experiment_dir": str(exp_dir),
        "scenarios": {},
    }

    # =========================================================================
    # STEP 1: UF6 Dry - Geometry Sweep
    # =========================================================================
    print("\n" + "="*60)
    print("STEP 1: UF6 Dry - Geometry Sweep")
    print("="*60)

    uf6_config = config_dir / "uf6.yaml"
    generate_config(
        output_path=uf6_config,
        template=template,
        name="UF6 Dry - Geometry Sweep",
        fissile_material="uf6",
        enrichment=enrichment,
        geometry_params=geometry_params,
        fill_fraction=1.0,
        fissile_density=5.09,
    )

    if run_config(uf6_config, smoke=smoke):
        uf6_run = find_latest_run(runs_dir / "uf6")
        if uf6_run:
            uf6_results = load_results(uf6_run / "results.csv")
            uf6_max = max(float(r['keff_2sigma']) for r in uf6_results) if uf6_results else 0
            results["scenarios"]["uf6"] = {
                "cases": len(uf6_results),
                "max_keff": uf6_max,
                "status": "SAFE" if uf6_max < 0.95 else "CRITICAL",
            }
            print(f"UF6 Max k-eff: {uf6_max:.3f}")

    # =========================================================================
    # STEP 2: H/U Sweep - Find Peak Moderation
    # =========================================================================
    print("\n" + "="*60)
    print("STEP 2: H/U Sweep - Find Peak Moderation")
    print("="*60)

    # Use fixed geometry (expected worst case - largest values)
    hu_geometry = {}
    for key, val in geometry_params.items():
        if isinstance(val, list):
            hu_geometry[key] = max(val)  # Use largest value as expected worst case
        else:
            hu_geometry[key] = val

    hu_config = config_dir / "uo2f2_hu_sweep.yaml"
    generate_config(
        output_path=hu_config,
        template=template,
        name="UO2F2 H/U Sweep",
        fissile_material="uo2f2",
        enrichment=enrichment,
        geometry_params=hu_geometry,
        fill_fraction=1.0,
        h_to_u=[0, 10, 20, 25, 30, 50],
    )

    peak_hu = 50  # Default
    if run_config(hu_config, smoke=smoke):
        hu_run = find_latest_run(runs_dir / "uo2f2_hu_sweep")
        if hu_run:
            hu_results = load_results(hu_run / "results.csv")
            if hu_results:
                peak_row = max(hu_results, key=lambda r: float(r['keff']))
                peak_hu = int(float(peak_row['h_to_u']))
                results["scenarios"]["hu_sweep"] = {
                    "cases": len(hu_results),
                    "peak_hu": peak_hu,
                    "peak_keff": float(peak_row['keff_2sigma']),
                }
                print(f"Peak H/U: {peak_hu} (k-eff = {peak_row['keff_2sigma']})")

    # =========================================================================
    # STEP 3: UO2F2 Wet - Geometry Sweep at Peak H/U
    # =========================================================================
    print("\n" + "="*60)
    print(f"STEP 3: UO2F2 Wet - Geometry Sweep at H/U={peak_hu}")
    print("="*60)

    wet_config = config_dir / "uo2f2_wet.yaml"
    generate_config(
        output_path=wet_config,
        template=template,
        name=f"UO2F2 Wet (H/U={peak_hu}) - Geometry Sweep",
        fissile_material="uo2f2",
        enrichment=enrichment,
        geometry_params=geometry_params,
        fill_fraction=1.0,
        h_to_u=peak_hu,
    )

    worst_case_geometry = hu_geometry.copy()  # Default to H/U sweep geometry
    if run_config(wet_config, smoke=smoke):
        wet_run = find_latest_run(runs_dir / "uo2f2_wet")
        if wet_run:
            wet_results = load_results(wet_run / "results.csv")
            if wet_results:
                wet_max = max(float(r['keff_2sigma']) for r in wet_results)
                worst_row = max(wet_results, key=lambda r: float(r['keff']))

                # Extract worst-case geometry
                for param in swept_params:
                    if param in worst_row:
                        worst_case_geometry[param] = worst_row[param]

                results["scenarios"]["uo2f2_wet"] = {
                    "cases": len(wet_results),
                    "max_keff": wet_max,
                    "status": "SAFE" if wet_max < 0.95 else "CRITICAL",
                    "worst_case": worst_case_geometry,
                }
                print(f"UO2F2 Wet Max k-eff: {wet_max:.3f}")
                print(f"Worst case: {worst_case_geometry}")

    # =========================================================================
    # STEP 4: Fill Sweep - Find Critical Threshold
    # =========================================================================
    print("\n" + "="*60)
    print("STEP 4: Fill Sweep - Find Critical Threshold")
    print("="*60)

    fill_config = config_dir / "uo2f2_fill_sweep.yaml"
    generate_config(
        output_path=fill_config,
        template=template,
        name="UO2F2 Fill Sweep (Worst Case)",
        fissile_material="uo2f2",
        enrichment=enrichment,
        geometry_params=worst_case_geometry,
        fill_fraction=[0.1, 0.2, 0.3, 0.4, 0.5],
        h_to_u=peak_hu,
    )

    if run_config(fill_config, smoke=smoke):
        fill_run = find_latest_run(runs_dir / "uo2f2_fill_sweep")
        if fill_run:
            fill_results = load_results(fill_run / "results.csv")
            if fill_results:
                # Find critical threshold and safe limit
                sorted_fill = sorted(fill_results, key=lambda r: float(r['fill_fraction']))

                safe_fill = None
                safe_keff = None
                crit_fill = None

                for r in sorted_fill:
                    fill_pct = float(r['fill_fraction']) * 100
                    k2s = float(r['keff_2sigma'])
                    if k2s < 0.95 and safe_fill is None:
                        safe_fill = fill_pct
                        safe_keff = k2s
                    if k2s >= 1.0 and crit_fill is None:
                        crit_fill = fill_pct

                # Interpolate critical threshold
                for i in range(len(sorted_fill) - 1):
                    k1 = float(sorted_fill[i]['keff_2sigma'])
                    k2 = float(sorted_fill[i+1]['keff_2sigma'])
                    f1 = float(sorted_fill[i]['fill_fraction']) * 100
                    f2 = float(sorted_fill[i+1]['fill_fraction']) * 100
                    if k1 < 1.0 <= k2:
                        crit_fill = f1 + (f2 - f1) * (1.0 - k1) / (k2 - k1)
                        break

                results["scenarios"]["fill_sweep"] = {
                    "cases": len(fill_results),
                    "safe_fill": safe_fill,
                    "safe_keff": safe_keff,
                    "crit_fill": crit_fill,
                }

                if safe_fill:
                    print(f"Safe fill limit: ≤{safe_fill:.0f}% (k-eff = {safe_keff:.3f})")
                if crit_fill:
                    print(f"Critical threshold: ~{crit_fill:.0f}%")

    # =========================================================================
    # SUMMARY
    # =========================================================================
    print("\n" + "="*60)
    print("ANALYSIS COMPLETE")
    print("="*60)

    if "uf6" in results["scenarios"]:
        uf6 = results["scenarios"]["uf6"]
        print(f"UF6 Dry:      k-eff = {uf6['max_keff']:.2f} ({uf6['status']})")

    if "uo2f2_wet" in results["scenarios"]:
        wet = results["scenarios"]["uo2f2_wet"]
        print(f"UO2F2 Wet:    k-eff = {wet['max_keff']:.2f} ({wet['status']})")

    if "fill_sweep" in results["scenarios"]:
        fill = results["scenarios"]["fill_sweep"]
        if fill.get("safe_fill"):
            print(f"Safe Limit:   ≤{fill['safe_fill']:.0f}% fill")
        if fill.get("crit_fill"):
            print(f"Critical:     ~{fill['crit_fill']:.0f}% fill")

    print(f"\nExperiment directory: {exp_dir}")

    return results


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python orchestrator.py <ticket_id> <template> [enrichment]")
        print("Example: python orchestrator.py CR-010 pipe_array_3d 21")
        sys.exit(1)

    ticket_id = sys.argv[1]
    template = sys.argv[2]
    enrichment = float(sys.argv[3]) if len(sys.argv) > 3 else 21

    # Example geometry params for pipe_array_3d
    if template == "pipe_array_3d":
        geometry_params = {
            "pipe_size": [4, 6],
            "gap_cm": [1, 2, 6],
            "num_pipes": 2,
            "rows": 3,
            "length_cm": 900,
        }
        swept_params = ["pipe_size", "gap_cm"]
    else:
        print(f"Template '{template}' not configured. Add geometry_params.")
        sys.exit(1)

    run_standard_analysis(
        ticket_id=ticket_id,
        template=template,
        enrichment=enrichment,
        geometry_params=geometry_params,
        swept_params=swept_params,
        smoke=True,  # Use smoke test for demo
    )
