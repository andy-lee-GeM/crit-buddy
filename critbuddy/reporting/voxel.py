"""
3D voxel visualization for geometry validation.

Supports multiple output formats:
- PNG: Static matplotlib rendering
- VTI: VTK format for ParaView
- Interactive: PyVista viewer
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from pathlib import Path
from typing import Optional, Tuple, Dict
from dataclasses import dataclass
import h5py

from .plot_spec import PlotSpec, auto_plot_spec


@dataclass
class VoxelData:
    """Container for voxel data and metadata."""
    data: np.ndarray  # 3D array of material IDs (nx, ny, nz)
    spec: PlotSpec
    materials: dict  # {material_id: {"name": str, "color": tuple}}
    spacing: Tuple[float, float, float]  # Voxel size in each dimension


def generate_voxel_data(
    geometry,
    materials,
    spec: Optional[PlotSpec] = None,
    max_resolution: int = 100,
) -> VoxelData:
    """
    Generate voxel data from OpenMC geometry.

    Args:
        geometry: OpenMC Geometry object
        materials: OpenMC Materials object
        spec: PlotSpec with framing parameters (auto-computed if None)
        max_resolution: Cap on pixels per axis (memory protection)

    Returns:
        VoxelData containing the 3D material array and metadata
    """
    import openmc
    from critbuddy.core.materials import MATERIAL_COLORS

    # Auto-compute spec if not provided
    if spec is None:
        spec = auto_plot_spec(geometry)

    # Use spec's max_resolution if available, otherwise use parameter
    effective_resolution = getattr(spec, 'max_resolution', max_resolution)

    # Calculate resolution (proportional to dimensions, capped)
    max_dim = max(spec.width)
    scale = effective_resolution / max_dim if max_dim > 0 else 1.0
    pixels = (
        max(min(int(spec.width[0] * scale), effective_resolution), 20),
        max(min(int(spec.width[1] * scale), effective_resolution), 20),
        max(min(int(spec.width[2] * scale), effective_resolution), 20),
    )

    print(f"  Voxel resolution: {pixels[0]} x {pixels[1]} x {pixels[2]}")

    # Create and run OpenMC voxel plot
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

    # Read voxel data
    voxel_file = Path("voxel_temp.h5")
    if not voxel_file.exists():
        raise FileNotFoundError("Voxel file not generated")

    with h5py.File(voxel_file, "r") as f:
        data = f["data"][:]

    # Fix axis order: OpenMC gives (nz, ny, nx), we want (nx, ny, nz)
    data = np.transpose(data, (2, 1, 0))

    # Build material metadata
    mat_info = {}
    for mat in materials:
        color = MATERIAL_COLORS.get(mat.name, (200, 200, 200))
        mat_info[mat.id] = {"name": mat.name, "color": color}

    # Calculate voxel spacing
    spacing = (
        spec.width[0] / pixels[0],
        spec.width[1] / pixels[1],
        spec.width[2] / pixels[2],
    )

    # Cleanup temp files
    voxel_file.unlink(missing_ok=True)
    Path("plots.xml").unlink(missing_ok=True)

    return VoxelData(data=data, spec=spec, materials=mat_info, spacing=spacing)


def export_vti(
    voxel_data: VoxelData,
    output_path: Path,
) -> Path:
    """
    Export voxel data to VTI format for ParaView.

    Args:
        voxel_data: VoxelData from generate_voxel_data()
        output_path: Path for output .vti file

    Returns:
        Path to the generated VTI file
    """
    try:
        import pyvista as pv
    except ImportError:
        raise ImportError("PyVista required for VTI export: pip install pyvista")

    data = voxel_data.data
    spec = voxel_data.spec

    # Create ImageData (uniform grid)
    grid = pv.ImageData(
        dimensions=(data.shape[0] + 1, data.shape[1] + 1, data.shape[2] + 1),
        spacing=voxel_data.spacing,
        origin=(
            spec.center[0] - spec.width[0] / 2,
            spec.center[1] - spec.width[1] / 2,
            spec.center[2] - spec.width[2] / 2,
        ),
    )

    # Add material IDs as cell data
    grid.cell_data["material_id"] = data.flatten(order="F")

    # Create material name lookup for ParaView
    # Add as field data so it's available in ParaView
    mat_names = np.zeros(data.max() + 1, dtype="<U32")
    for mat_id, info in voxel_data.materials.items():
        if mat_id < len(mat_names):
            mat_names[mat_id] = info["name"]
    grid.field_data["material_names"] = mat_names

    # Save
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
    """
    Launch interactive PyVista viewer.

    Args:
        voxel_data: VoxelData from generate_voxel_data()
        exclude_materials: Material names to hide (default: from spec)
        opacity: Mesh opacity (0-1)
        show_edges: Show voxel edges
    """
    try:
        import pyvista as pv
    except ImportError:
        raise ImportError("PyVista required for interactive view: pip install pyvista")

    if exclude_materials is None:
        exclude_materials = voxel_data.spec.exclude_materials

    data = voxel_data.data
    spec = voxel_data.spec

    # Create ImageData
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

    # Find material IDs to exclude
    exclude_ids = set()
    for mat_id, info in voxel_data.materials.items():
        if info["name"] in exclude_materials:
            exclude_ids.add(mat_id)

    # Create plotter
    plotter = pv.Plotter()
    plotter.set_background("white")

    # Add each material as a separate mesh with its color
    for mat_id, info in voxel_data.materials.items():
        if mat_id in exclude_ids or mat_id == 0:
            continue

        # Threshold to get only this material
        mat_mesh = grid.threshold([mat_id - 0.5, mat_id + 0.5], scalars="material_id")
        if mat_mesh.n_cells == 0:
            continue

        # Convert color from 0-255 to 0-1
        color = tuple(c / 255 for c in info["color"])

        plotter.add_mesh(
            mat_mesh,
            color=color,
            opacity=opacity,
            show_edges=show_edges,
            label=info["name"],
        )

    plotter.add_legend()
    plotter.add_axes()
    plotter.show()


def create_voxel_plot(
    geometry,
    materials,
    output_path: Path,
    spec: Optional[PlotSpec] = None,
    max_resolution: int = 100,
    export_vti_path: Optional[Path] = None,
) -> Path:
    """
    Generate a 3D voxel visualization as PNG.

    Args:
        geometry: OpenMC Geometry object
        materials: OpenMC Materials object
        output_path: Path for output PNG
        spec: PlotSpec with framing parameters (auto-computed if None)
        max_resolution: Cap on pixels per axis (memory protection)
        export_vti_path: If provided, also export VTI file for ParaView

    Returns:
        Path to the generated PNG
    """
    from critbuddy.core.materials import MATERIAL_COLORS

    # Generate voxel data
    voxel_data = generate_voxel_data(geometry, materials, spec, max_resolution)

    # Export VTI if requested
    if export_vti_path:
        vti_path = export_vti(voxel_data, export_vti_path)
        print(f"  VTI file: {vti_path}")

    # Use the spec from voxel_data (may have been auto-computed)
    spec = voxel_data.spec
    data = voxel_data.data

    # Build color arrays for matplotlib
    mat_colors = {}
    for mat_id, info in voxel_data.materials.items():
        mat_colors[mat_id] = np.array(info["color"]) / 255.0

    # Find material IDs to exclude (so we can see inside)
    exclude_ids = set()
    for mat_id, info in voxel_data.materials.items():
        if info["name"] in spec.exclude_materials:
            exclude_ids.add(mat_id)

    # Create filled mask (exclude void and environment materials)
    filled = data > 0
    for mat_id in exclude_ids:
        filled = filled & (data != mat_id)

    # Create RGBA color array
    colors = np.zeros((*data.shape, 4))
    for mat_id, color in mat_colors.items():
        mask = data == mat_id
        colors[mask, :3] = color
        colors[mask, 3] = 1.0

    # Render
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection="3d")

    ax.voxels(filled, facecolors=colors, edgecolor="none", alpha=0.9)

    # Set view based on up_axis
    if spec.up_axis == "z":
        ax.view_init(elev=25, azim=225)
    elif spec.up_axis == "y":
        ax.view_init(elev=0, azim=225)
    elif spec.up_axis == "x":
        ax.view_init(elev=0, azim=0)

    ax.set_xlabel("X (cm)")
    ax.set_ylabel("Y (cm)")
    ax.set_zlabel("Z (cm)")
    ax.set_title("3D Geometry")

    # Legend (only show materials that aren't excluded)
    legend_elements = [
        Patch(facecolor=mat_colors.get(mat_id, [0.8, 0.8, 0.8]), label=info["name"])
        for mat_id, info in voxel_data.materials.items()
        if info["name"] not in spec.exclude_materials and mat_id != 0
    ]
    if legend_elements:
        ax.legend(handles=legend_elements, loc="upper left")

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()

    return output_path


def create_isometric_slices(
    geometry,
    materials,
    output_path: Path,
    spec: Optional[PlotSpec] = None,
    n_slices: int = 5,
) -> Path:
    """
    Generate stacked 2D slices for a pseudo-3D view.

    This is lighter weight than full voxel rendering.

    Args:
        geometry: OpenMC Geometry object
        materials: OpenMC Materials object
        output_path: Path for output PNG
        spec: PlotSpec with framing parameters (auto-computed if None)
        n_slices: Number of horizontal slices

    Returns:
        Path to the generated PNG
    """
    import openmc
    from critbuddy.core.materials import MATERIAL_COLORS

    # Auto-compute spec if not provided
    if spec is None:
        spec = auto_plot_spec(geometry)

    # Build color mapping for OpenMC
    omc_colors = {}
    for mat in materials:
        if mat.name in MATERIAL_COLORS:
            omc_colors[mat] = MATERIAL_COLORS[mat.name]
        else:
            omc_colors[mat] = (200, 200, 200)

    # Create slices at different heights along the up axis
    if spec.up_axis == "z":
        z_min = spec.center[2] - spec.width[2] / 3
        z_max = spec.center[2] + spec.width[2] / 3
        z_positions = np.linspace(z_min, z_max, n_slices)
        slice_basis = "xy"
        slice_width = (spec.width[0], spec.width[1])
    elif spec.up_axis == "y":
        z_min = spec.center[1] - spec.width[1] / 3
        z_max = spec.center[1] + spec.width[1] / 3
        z_positions = np.linspace(z_min, z_max, n_slices)
        slice_basis = "xz"
        slice_width = (spec.width[0], spec.width[2])
    else:  # x
        z_min = spec.center[0] - spec.width[0] / 3
        z_max = spec.center[0] + spec.width[0] / 3
        z_positions = np.linspace(z_min, z_max, n_slices)
        slice_basis = "yz"
        slice_width = (spec.width[1], spec.width[2])

    fig, axes = plt.subplots(1, n_slices, figsize=(4 * n_slices, 4))
    if n_slices == 1:
        axes = [axes]

    for i, z in enumerate(z_positions):
        if spec.up_axis == "z":
            origin = (spec.center[0], spec.center[1], z)
        elif spec.up_axis == "y":
            origin = (spec.center[0], z, spec.center[2])
        else:
            origin = (z, spec.center[1], spec.center[2])

        plot = openmc.Plot()
        plot.basis = slice_basis
        plot.origin = origin
        plot.width = slice_width
        plot.pixels = (400, 400)
        plot.color_by = "material"
        plot.colors = omc_colors
        plot.filename = f"slice_{i}"

        plots = openmc.Plots([plot])
        plots.export_to_xml()
        openmc.plot_geometry()

        # Load and display
        img_path = Path("plot_1.png")
        if img_path.exists():
            img = plt.imread(img_path)
            axes[i].imshow(img)
            axes[i].set_title(f"{spec.up_axis} = {z:.1f} cm")
            axes[i].axis("off")
            img_path.unlink()

        # Cleanup
        Path("plots.xml").unlink(missing_ok=True)
        Path(f"slice_{i}.png").unlink(missing_ok=True)

    # Add legend
    legend_elements = []
    for mat in materials:
        if mat.name in MATERIAL_COLORS:
            rgb = np.array(MATERIAL_COLORS[mat.name]) / 255.0
            legend_elements.append(Patch(facecolor=rgb, label=mat.name))
    fig.legend(handles=legend_elements, loc="upper right")

    plt.suptitle("Geometry Slices at Different Heights")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()

    return output_path
