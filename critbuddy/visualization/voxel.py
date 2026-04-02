"""
3D voxel visualization for geometry validation.

Supports multiple output formats:
- PNG: Static matplotlib rendering
- VTI: VTK format for ParaView
- Interactive: PyVista viewer
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple

import h5py
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch

from .plot_spec import PlotSpec, auto_plot_spec


@dataclass
class VoxelData:
    """Container for voxel data and metadata."""

    data: np.ndarray
    spec: PlotSpec
    materials: dict
    spacing: Tuple[float, float, float]


def generate_voxel_data(
    geometry,
    materials,
    spec: Optional[PlotSpec] = None,
    max_resolution: int = 100,
) -> VoxelData:
    """Generate voxel data from OpenMC geometry."""
    import openmc
    from critbuddy.core.materials import MATERIAL_COLORS

    if spec is None:
        spec = auto_plot_spec(geometry)

    effective_resolution = getattr(spec, "max_resolution", max_resolution)
    max_dim = max(spec.width)
    scale = effective_resolution / max_dim if max_dim > 0 else 1.0
    pixels = (
        max(min(int(spec.width[0] * scale), effective_resolution), 20),
        max(min(int(spec.width[1] * scale), effective_resolution), 20),
        max(min(int(spec.width[2] * scale), effective_resolution), 20),
    )

    print(f"  Voxel resolution: {pixels[0]} x {pixels[1]} x {pixels[2]}")

    voxel_plot = openmc.Plot()
    voxel_plot.type = "voxel"
    voxel_plot.origin = spec.center
    voxel_plot.width = spec.width
    voxel_plot.pixels = pixels
    voxel_plot.filename = "voxel_temp"
    voxel_plot.color_by = "material"

    plots = openmc.Plots([voxel_plot])
    plots.export_to_xml()
    openmc.plot_geometry()

    voxel_file = Path("voxel_temp.h5")
    if not voxel_file.exists():
        raise FileNotFoundError("Voxel file not generated")

    with h5py.File(voxel_file, "r") as handle:
        data = handle["data"][:]

    data = np.transpose(data, (2, 1, 0))

    mat_info = {}
    for mat in materials:
        color = MATERIAL_COLORS.get(mat.name, (200, 200, 200))
        mat_info[mat.id] = {"name": mat.name, "color": color}

    spacing = (
        spec.width[0] / pixels[0],
        spec.width[1] / pixels[1],
        spec.width[2] / pixels[2],
    )

    voxel_file.unlink(missing_ok=True)
    Path("plots.xml").unlink(missing_ok=True)

    return VoxelData(data=data, spec=spec, materials=mat_info, spacing=spacing)


def export_vti(
    voxel_data: VoxelData,
    output_path: Path,
) -> Path:
    """Export voxel data to VTI format for ParaView."""
    try:
        import pyvista as pv
    except ImportError:
        raise ImportError("PyVista required for VTI export: pip install pyvista")

    data = voxel_data.data
    spec = voxel_data.spec

    grid = pv.ImageData(
        dimensions=(data.shape[0] + 1, data.shape[1] + 1, data.shape[2] + 1),
        spacing=voxel_data.spacing,
        origin=(
            spec.center[0] - spec.width[0] / 2,
            spec.center[1] - spec.width[1] / 2,
            spec.center[2] - spec.width[2] / 2,
        ),
    )

    grid.cell_data["material_id"] = data.flatten(order="F")

    mat_names = np.zeros(data.max() + 1, dtype="<U32")
    for mat_id, info in voxel_data.materials.items():
        if mat_id < len(mat_names):
            mat_names[mat_id] = info["name"]
    grid.field_data["material_names"] = mat_names

    output_path = Path(output_path)
    if not output_path.suffix:
        output_path = output_path.with_suffix(".vti")
    grid.save(str(output_path))

    return output_path


def view_interactive(
    voxel_data: VoxelData,
    exclude_materials: Optional[list] = None,
    opacity: float = 0.8,
    show_edges: bool = False,
) -> None:
    """Launch an interactive PyVista viewer."""
    try:
        import pyvista as pv
    except ImportError:
        raise ImportError("PyVista required for interactive view: pip install pyvista")

    if exclude_materials is None:
        exclude_materials = voxel_data.spec.exclude_materials

    data = voxel_data.data
    spec = voxel_data.spec

    grid = pv.ImageData(
        dimensions=(data.shape[0] + 1, data.shape[1] + 1, data.shape[2] + 1),
        spacing=voxel_data.spacing,
        origin=(
            spec.center[0] - spec.width[0] / 2,
            spec.center[1] - spec.width[1] / 2,
            spec.center[2] - spec.width[2] / 2,
        ),
    )
    grid.cell_data["material_id"] = data.flatten(order="F")

    exclude_ids = set()
    for mat_id, info in voxel_data.materials.items():
        if info["name"] in exclude_materials:
            exclude_ids.add(mat_id)

    plotter = pv.Plotter()
    plotter.set_background("white")

    for mat_id, info in voxel_data.materials.items():
        if mat_id in exclude_ids or mat_id == 0:
            continue

        mat_mesh = grid.threshold([mat_id - 0.5, mat_id + 0.5], scalars="material_id")
        if mat_mesh.n_cells == 0:
            continue

        color = np.array(info["color"]) / 255.0
        plotter.add_mesh(
            mat_mesh,
            color=color,
            opacity=opacity,
            show_edges=show_edges,
            label=info["name"],
        )

    plotter.add_legend()
    plotter.show()


def create_voxel_plot(
    geometry,
    materials,
    output_path: Path,
    spec: Optional[PlotSpec] = None,
    max_resolution: int = 100,
    export_vti_path: Optional[Path] = None,
) -> Path:
    """Generate a static 3D voxel visualization as PNG."""
    voxel_data = generate_voxel_data(geometry, materials, spec, max_resolution)

    if export_vti_path:
        export_vti(voxel_data, export_vti_path)

    spec = voxel_data.spec
    data = voxel_data.data

    mat_colors = {}
    for mat_id, info in voxel_data.materials.items():
        mat_colors[mat_id] = np.array(info["color"]) / 255.0

    filled = data != 0
    colors = np.zeros(filled.shape + (4,), dtype=float)
    for mat_id, rgb in mat_colors.items():
        colors[data == mat_id, :3] = rgb
        colors[data == mat_id, 3] = 1.0

    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection="3d")
    ax.voxels(filled, facecolors=colors, edgecolor="none", alpha=0.9)

    ax.set_box_aspect(spec.width)
    ax.set_axis_off()

    legend_handles = [
        Patch(facecolor=np.array(info["color"]) / 255.0, edgecolor="black", label=info["name"])
        for _, info in sorted(voxel_data.materials.items())
        if info["name"] not in spec.exclude_materials
    ]
    if legend_handles:
        ax.legend(handles=legend_handles, loc="upper right", bbox_to_anchor=(1.15, 1.0))

    plt.tight_layout()
    output_path = Path(output_path)
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return output_path


def create_isometric_slices(
    geometry,
    materials,
    output_path: Path,
    spec: Optional[PlotSpec] = None,
    n_slices: int = 3,
) -> Path:
    """Generate lightweight orthogonal slices for quick geometry inspection."""
    import openmc
    from critbuddy.core.materials import MATERIAL_COLORS

    if spec is None:
        spec = auto_plot_spec(geometry)

    slice_positions = np.linspace(-0.25, 0.25, n_slices)
    fig, axes = plt.subplots(1, n_slices, figsize=(4 * n_slices, 4))
    if n_slices == 1:
        axes = [axes]

    for idx, axis in enumerate(axes):
        plot = openmc.Plot()
        plot.type = "slice"
        plot.basis = "xy"
        plot.origin = (spec.center[0], spec.center[1], spec.center[2] + slice_positions[idx] * spec.width[2])
        plot.width = (spec.width[0], spec.width[1])
        plot.pixels = (500, 500)
        plot.filename = f"slice_{idx}"
        plot.color_by = "material"

        plots = openmc.Plots([plot])
        plots.export_to_xml()
        openmc.plot_geometry()

        image = plt.imread(f"slice_{idx}.png")
        axis.imshow(image)
        axis.set_title(f"Slice {idx + 1}")
        axis.axis("off")

        Path(f"slice_{idx}.png").unlink(missing_ok=True)
        Path("plots.xml").unlink(missing_ok=True)

    legend_handles = []
    for mat in materials:
        if mat.name in spec.exclude_materials:
            continue
        rgb = np.array(MATERIAL_COLORS.get(mat.name, (200, 200, 200))) / 255.0
        legend_handles.append(Patch(facecolor=rgb, edgecolor="black", label=mat.name))
    if legend_handles:
        fig.legend(handles=legend_handles, loc="lower center", ncol=min(4, len(legend_handles)))

    plt.tight_layout()
    output_path = Path(output_path)
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return output_path
