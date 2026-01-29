"""
3D voxel visualization for geometry validation.

Generates PNG renderings from OpenMC voxel plots using matplotlib.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from pathlib import Path
from typing import Dict, Tuple, Optional
import tempfile
import os


def create_voxel_plot(
    geometry,
    materials,
    output_path: Path,
    width: Tuple[float, float, float],
    center: Tuple[float, float, float] = (0, 0, 50),
    pixels: Tuple[int, int, int] = (100, 100, 50),
    color_mapping: Optional[Dict[str, Tuple[int, int, int]]] = None,
    cutaway: bool = True,
) -> Path:
    """
    Generate a 3D voxel visualization as PNG.

    Args:
        geometry: OpenMC Geometry object
        materials: OpenMC Materials object
        output_path: Path for output PNG
        width: (x, y, z) dimensions of the plot region in cm
        center: (x, y, z) center of the plot region
        pixels: (nx, ny, nz) resolution
        color_mapping: Dict mapping material name to RGB tuple
        cutaway: If True, remove one quadrant to show internal structure

    Returns:
        Path to the generated PNG
    """
    import openmc

    # Default colors
    if color_mapping is None:
        color_mapping = {
            "UF6": (127, 255, 0),
            "Aluminum": (147, 112, 219),
            "Steel": (105, 105, 105),
            "Water": (30, 144, 255),
            "Air": (135, 206, 250),
            "Concrete": (188, 143, 143),
        }

    # Create voxel plot
    voxel_plot = openmc.Plot()
    voxel_plot.type = 'voxel'
    voxel_plot.origin = center
    voxel_plot.width = width
    voxel_plot.pixels = pixels
    voxel_plot.filename = 'voxel_temp'
    voxel_plot.color_by = 'material'

    plots = openmc.Plots([voxel_plot])
    plots.export_to_xml()

    # Run OpenMC plot generation
    openmc.plot_geometry()

    # Read voxel data
    voxel_file = Path('voxel_temp.h5')
    if not voxel_file.exists():
        raise FileNotFoundError("Voxel file not generated")

    import h5py
    with h5py.File(voxel_file, 'r') as f:
        data = f['data'][:]
        # data shape is (nz, ny, nx) with material IDs

    # Build material ID to color mapping
    mat_id_to_color = {}
    mat_id_to_name = {}
    for mat in materials:
        mat_id_to_name[mat.id] = mat.name
        if mat.name in color_mapping:
            rgb = color_mapping[mat.name]
            mat_id_to_color[mat.id] = np.array(rgb) / 255.0
        else:
            mat_id_to_color[mat.id] = np.array([0.8, 0.8, 0.8])

    # Create figure with 3D projection
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')

    # Convert material IDs to colors for voxel plot
    nz, ny, nx = data.shape

    # Find environment material IDs (Air, Water) - exclude from solid rendering
    # so internal structure (UF6, walls) is always visible
    env_ids = set()
    for mat in materials:
        if mat.name in ("Air", "Water"):
            env_ids.add(mat.id)

    # Create boolean array for filled voxels (exclude environment materials)
    filled = (data > 0)
    for env_id in env_ids:
        filled = filled & (data != env_id)

    # Create color array
    colors = np.zeros((*data.shape, 4))
    for mat_id, color in mat_id_to_color.items():
        mask = data == mat_id
        colors[mask, :3] = color
        colors[mask, 3] = 1.0

    # Plot voxels
    ax.voxels(filled, facecolors=colors, edgecolor='none', alpha=0.9)

    # Set view angle with Z pointing up
    ax.view_init(elev=25, azim=225)

    # Labels
    ax.set_xlabel('X (pixels)')
    ax.set_ylabel('Y (pixels)')
    ax.set_zlabel('Z (pixels)')
    ax.set_title('3D Geometry Visualization')

    # Add legend
    legend_elements = []
    from matplotlib.patches import Patch
    for mat in materials:
        if mat.name in color_mapping:
            rgb = np.array(color_mapping[mat.name]) / 255.0
            legend_elements.append(Patch(facecolor=rgb, label=mat.name))
    ax.legend(handles=legend_elements, loc='upper left')

    # Save
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    # Cleanup
    voxel_file.unlink(missing_ok=True)
    Path('plots.xml').unlink(missing_ok=True)

    return output_path


def create_isometric_slices(
    geometry,
    materials,
    output_path: Path,
    width: Tuple[float, float],
    height: float,
    center: Tuple[float, float, float] = (0, 0, 50),
    n_slices: int = 5,
    color_mapping: Optional[Dict[str, Tuple[int, int, int]]] = None,
) -> Path:
    """
    Generate stacked 2D slices for a pseudo-3D view.

    This is lighter weight than full voxel rendering.

    Args:
        geometry: OpenMC Geometry object
        materials: OpenMC Materials object
        output_path: Path for output PNG
        width: (x, y) dimensions of each slice
        height: Total height to slice through
        center: (x, y, z) center of the geometry
        n_slices: Number of horizontal slices
        color_mapping: Dict mapping material name to RGB tuple

    Returns:
        Path to the generated PNG
    """
    import openmc

    if color_mapping is None:
        color_mapping = {
            "UF6": (127, 255, 0),
            "Aluminum": (147, 112, 219),
            "Steel": (105, 105, 105),
            "Water": (30, 144, 255),
            "Air": (135, 206, 250),
        }

    # Build color mapping for OpenMC
    omc_colors = {}
    for mat in materials:
        if mat.name in color_mapping:
            omc_colors[mat] = color_mapping[mat.name]
        else:
            omc_colors[mat] = (200, 200, 200)

    # Create slices at different heights
    z_positions = np.linspace(center[2] - height/3, center[2] + height/3, n_slices)

    fig, axes = plt.subplots(1, n_slices, figsize=(4 * n_slices, 4))
    if n_slices == 1:
        axes = [axes]

    for i, z in enumerate(z_positions):
        plot = openmc.Plot()
        plot.basis = 'xy'
        plot.origin = (center[0], center[1], z)
        plot.width = width
        plot.pixels = (400, 400)
        plot.color_by = 'material'
        plot.colors = omc_colors
        plot.filename = f'slice_{i}'

        plots = openmc.Plots([plot])
        plots.export_to_xml()
        openmc.plot_geometry()

        # Load and display
        img_path = Path(f'plot_1.png')
        if img_path.exists():
            img = plt.imread(img_path)
            axes[i].imshow(img)
            axes[i].set_title(f'z = {z:.1f} cm')
            axes[i].axis('off')
            img_path.unlink()

        # Cleanup
        Path('plots.xml').unlink(missing_ok=True)
        Path(f'slice_{i}.png').unlink(missing_ok=True)

    # Add legend
    from matplotlib.patches import Patch
    legend_elements = []
    for mat in materials:
        if mat.name in color_mapping:
            rgb = np.array(color_mapping[mat.name]) / 255.0
            legend_elements.append(Patch(facecolor=rgb, label=mat.name))
    fig.legend(handles=legend_elements, loc='upper right')

    plt.suptitle('Geometry Slices at Different Heights')
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    return output_path
