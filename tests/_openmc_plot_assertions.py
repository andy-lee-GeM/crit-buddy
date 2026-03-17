import os
from pathlib import Path

import openmc
from critbuddy.reporting.geometry import create_geometry_plot


def render_openmc_plots(
    *,
    materials,
    geometry,
    plots,
    color_legend,
    output_dir: Path,
    expected_plot_names: list[str],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    for path in output_dir.iterdir():
        if path.is_file():
            path.unlink()

    previous_cwd = Path.cwd()
    try:
        os.chdir(output_dir)
        materials.export_to_xml()
        geometry.export_to_xml()
        plots.export_to_xml()
        openmc.plot_geometry()

        for index, plot_name in enumerate(expected_plot_names, start=1):
            raw_path = output_dir / f"plot_{index}.png"
            final_path = output_dir / f"{plot_name}.png"
            if final_path.exists():
                final_path.unlink()
            raw_path.rename(final_path)
            assert final_path.exists()
            assert final_path.stat().st_size > 0

        xy_plot = output_dir / "xy.png"
        xz_plot = output_dir / "xz.png"
        if xy_plot.exists() and xz_plot.exists():
            create_geometry_plot(
                xy_plot_path=xy_plot,
                xz_plot_path=xz_plot,
                output_path=output_dir / "geometry.png",
                color_legend=color_legend,
            )
    finally:
        os.chdir(previous_cwd)
