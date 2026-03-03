#!/usr/bin/env python3
"""
================================================================================
CASCADE ARRAY CRITICALITY MODEL - OpenMC
================================================================================
Template:   cascade_array
Problem:    Cylinder pack with optional boundary shell

Geometry Hierarchy:
    Level 1: Cylinder    - Single steel-clad vessel with fissile material
    Level 2: Pack        - i x j x k array of cylinders
    Level 3: Pack + boundary shell (ROOT)

Applications: Cascade hall layouts, process equipment arrays
================================================================================
"""

import openmc
from dataclasses import dataclass
from critbuddy.core.materials import (
    create_fissile_material,
    create_environment_material,
    get_material,
    get_color_mapping,
    get_color_legend,
)


@dataclass(frozen=True)
class CylinderPlacement:
    """Single cylinder placement in pack coordinates."""

    layer: int
    j_idx: int
    i_idx: int
    x_center: float
    y_center: float
    z_base: float


def iter_cylinder_placements(p):
    """Yield deterministic cylinder placements from derived geometry params."""
    r_outer = p["R_OUTER"]
    pitch_cyl = p["PITCH_CYLINDER"]
    pitch_z = p["PITCH_Z"]
    i_count = p["I"]
    j_count = p["J"]
    k_count = p["K"]

    for layer in range(k_count):
        z_base = layer * pitch_z
        for j_idx in range(j_count):
            for i_idx in range(i_count):
                x_center = r_outer + i_idx * pitch_cyl
                y_center = r_outer + j_idx * pitch_cyl
                yield CylinderPlacement(
                    layer=layer,
                    j_idx=j_idx,
                    i_idx=i_idx,
                    x_center=x_center,
                    y_center=y_center,
                    z_base=z_base,
                )


def _add_cylinder_cells(
    placement: CylinderPlacement,
    *,
    r_inner: float,
    r_outer: float,
    h_inner: float,
    h_outer: float,
    t_wall: float,
    m_fissile,
    m_wall,
    cells: list,
    cylinder_regions: list,
    cell_id: int,
) -> int:
    """Create fissile, wall, bottom-cap, and top-cap cells for one placement."""
    suffix = f"{placement.layer}_{placement.j_idx}_{placement.i_idx}"
    z_bottom = placement.z_base
    z_bottom_inner = z_bottom + t_wall
    z_top_inner = z_bottom + t_wall + h_inner
    z_top = z_bottom + h_outer

    cyl_inner = openmc.ZCylinder(
        x0=placement.x_center,
        y0=placement.y_center,
        r=r_inner,
        name=f"cyl_inner_{suffix}",
    )
    cyl_outer = openmc.ZCylinder(
        x0=placement.x_center,
        y0=placement.y_center,
        r=r_outer,
        name=f"cyl_outer_{suffix}",
    )
    z_bottom_plane = openmc.ZPlane(z0=z_bottom, name=f"z_bottom_{suffix}")
    z_bottom_inner_plane = openmc.ZPlane(z0=z_bottom_inner, name=f"z_bottom_inner_{suffix}")
    z_top_inner_plane = openmc.ZPlane(z0=z_top_inner, name=f"z_top_inner_{suffix}")
    z_top_plane = openmc.ZPlane(z0=z_top, name=f"z_top_{suffix}")

    c_fissile = openmc.Cell(cell_id=cell_id, name=f"fissile_{suffix}", fill=m_fissile)
    c_fissile.region = -cyl_inner & +z_bottom_inner_plane & -z_top_inner_plane
    cells.append(c_fissile)
    cell_id += 1

    c_wall = openmc.Cell(cell_id=cell_id, name=f"wall_{suffix}", fill=m_wall)
    c_wall.region = +cyl_inner & -cyl_outer & +z_bottom_inner_plane & -z_top_inner_plane
    cells.append(c_wall)
    cell_id += 1

    c_cap_bottom = openmc.Cell(cell_id=cell_id, name=f"cap_bottom_{suffix}", fill=m_wall)
    c_cap_bottom.region = -cyl_outer & +z_bottom_plane & -z_bottom_inner_plane
    cells.append(c_cap_bottom)
    cell_id += 1

    c_cap_top = openmc.Cell(cell_id=cell_id, name=f"cap_top_{suffix}", fill=m_wall)
    c_cap_top.region = -cyl_outer & +z_top_inner_plane & -z_top_plane
    cells.append(c_cap_top)
    cell_id += 1

    cylinder_regions.append(-cyl_outer & +z_bottom_plane & -z_top_plane)
    return cell_id


def build_model(p):
    """
    Build OpenMC model for cascade array.

    Creates cylinders explicitly at each grid position (no nested lattices).
    This approach is more reliable for visualization and debugging.

    Args:
        p: Parameter dictionary from template.derive_params()

    Returns:
        materials: openmc.Materials
        geometry: openmc.Geometry
        dims: Dictionary of dimensions for plotting/reporting
    """

    # =========================================================================
    # MATERIALS
    # =========================================================================

    fissile_type = p["FISSILE_MATERIAL"]
    enrichment = p["ENRICHMENT"]
    m_fissile = create_fissile_material(
        fissile_material=fissile_type,
        enrichment_pct=enrichment,
        fissile_density=p.get("FISSILE_DENSITY"),
        h_to_u=p.get("H_TO_U", 0.0),
    )

    # Wall material
    m_wall = get_material(p["WALL_MATERIAL"], solver="openmc")

    # Environment between units (humid air or dry air only - no water)
    environment = p["ENVIRONMENT_MATERIAL"]
    m_moderator = create_environment_material(
        environment_material=environment,
        environment_density=p.get("ENV_DENSITY"),
    )

    boundary_type = p.get("BOUNDARY_TYPE", "vacuum")
    materials = openmc.Materials([m_fissile, m_wall, m_moderator])

    # =========================================================================
    # DIMENSIONS
    # =========================================================================

    # Cylinder dimensions
    R_inner = p["R_INNER"]
    R_outer = p["R_OUTER"]
    H_inner = p["H_INNER"]
    H_outer = p["H_OUTER"]
    t_wall = p["T_WALL"]

    # Pack dimensions
    i_count = p["I"]  # cylinders in X
    j_count = p["J"]  # cylinders in Y
    k_count = p["K"]  # cylinders in Z (layers)
    pitch_cyl = p["PITCH_CYLINDER"]
    pitch_z = p["PITCH_Z"]

    # Pack extents
    pack_x = p["CASSETTE_X"]
    pack_y = p["CASSETTE_Y"]
    pack_z = p["CASSETTE_Z"]

    # Overall dimensions (same as pack in this template)
    reflector = p["REFLECTOR_THICKNESS"]
    gap_xy = p["GAP_XY"]
    gap_z = p["GAP_Z"]

    # =========================================================================
    # CREATE CYLINDERS EXPLICITLY
    # =========================================================================

    cells = []
    cell_id = 1
    cylinder_regions = []  # Track cylinder regions for moderator exclusion

    for placement in iter_cylinder_placements(p):
        cell_id = _add_cylinder_cells(
            placement,
            r_inner=R_inner,
            r_outer=R_outer,
            h_inner=H_inner,
            h_outer=H_outer,
            t_wall=t_wall,
            m_fissile=m_fissile,
            m_wall=m_wall,
            cells=cells,
            cylinder_regions=cylinder_regions,
            cell_id=cell_id,
        )

    # =========================================================================
    # BOUNDING BOX AND OUTER SHELL
    # =========================================================================

    # Array dimensions
    array_x = p["ARRAY_X"]
    array_y = p["ARRAY_Y"]
    array_z = p["ARRAY_Z"]

    if boundary_type == "reflective":
        # Infinite-lattice style: boundaries are half-gap from outermost walls.
        pad_x = gap_xy / 2.0
        pad_y = gap_xy / 2.0
        pad_z = gap_z / 2.0
    else:
        # Finite case: explicit environment shell around array.
        pad_x = reflector
        pad_y = reflector
        pad_z = reflector

    x_lo = -pad_x
    x_hi = array_x + pad_x
    y_lo = -pad_y
    y_hi = array_y + pad_y
    z_lo = -pad_z
    z_hi = array_z + pad_z

    total_x = x_hi - x_lo
    total_y = y_hi - y_lo
    total_z = z_hi - z_lo

    # Bounding box surfaces
    x_min = openmc.XPlane(x0=x_lo, boundary_type=boundary_type, name="x_min")
    x_max = openmc.XPlane(x0=x_hi, boundary_type=boundary_type, name="x_max")
    y_min = openmc.YPlane(y0=y_lo, boundary_type=boundary_type, name="y_min")
    y_max = openmc.YPlane(y0=y_hi, boundary_type=boundary_type, name="y_max")
    z_min = openmc.ZPlane(z0=z_lo, boundary_type=boundary_type, name="z_min")
    z_max = openmc.ZPlane(z0=z_hi, boundary_type=boundary_type, name="z_max")

    # Inner box surfaces (array boundary - separates interior from outer shell)
    array_x_min = openmc.XPlane(x0=0, name="array_x_min")
    array_x_max = openmc.XPlane(x0=array_x, name="array_x_max")
    array_y_min = openmc.YPlane(y0=0, name="array_y_min")
    array_y_max = openmc.YPlane(y0=array_y, name="array_y_max")
    array_z_min = openmc.ZPlane(z0=0, name="array_z_min")
    array_z_max = openmc.ZPlane(z0=array_z, name="array_z_max")

    system_region = +x_min & -x_max & +y_min & -y_max & +z_min & -z_max
    array_region = (+array_x_min & -array_x_max &
                    +array_y_min & -array_y_max &
                    +array_z_min & -array_z_max)

    # In reflective mode, fill all non-cylinder space with environment.
    # In vacuum mode, environment is only inside array volume.
    moderator_region = system_region if boundary_type == "reflective" else array_region

    # Exclude all cylinder regions from moderator
    for cyl_region in cylinder_regions:
        moderator_region = moderator_region & ~cyl_region

    c_moderator = openmc.Cell(cell_id=cell_id, name="moderator", fill=m_moderator)
    c_moderator.region = moderator_region
    cells.append(c_moderator)
    cell_id += 1

    if boundary_type == "vacuum":
        shell_region = system_region & ~array_region
        c_shell = openmc.Cell(cell_id=cell_id, name="environment_shell", fill=m_moderator)
        c_shell.region = shell_region
        cells.append(c_shell)

    # =========================================================================
    # GEOMETRY ASSEMBLY
    # =========================================================================

    universe = openmc.Universe(cells=cells)
    geometry = openmc.Geometry(universe)

    # =========================================================================
    # OUTPUT DIMENSIONS
    # =========================================================================

    dims = {
        # Cylinder
        "R_INNER": R_inner,
        "R_OUTER": R_outer,
        "H_INNER": H_inner,
        "H_OUTER": H_outer,
        "T_WALL": t_wall,
        # Pack
        "I": i_count,
        "J": j_count,
        "K": k_count,
        "GAP_XY": gap_xy,
        "GAP_Z": gap_z,
        "PITCH_CYLINDER": pitch_cyl,
        "PITCH_Z": pitch_z,
        "CASSETTE_X": pack_x,
        "CASSETTE_Y": pack_y,
        "CASSETTE_Z": pack_z,
        # Overall
        "REFLECTOR_THICKNESS": reflector,
        "REFLECTOR_THICKNESS_INPUT": p.get("REFLECTOR_THICKNESS_INPUT", reflector),
        "BOUNDARY_TYPE": boundary_type,
        "ARRAY_X": array_x,
        "ARRAY_Y": array_y,
        "ARRAY_Z": array_z,
        "TOTAL_X": total_x,
        "TOTAL_Y": total_y,
        "TOTAL_Z": total_z,
        # Materials
        "fissile_material": fissile_type,
        "fissile_density": m_fissile.density,
        "h_to_u": p.get("H_TO_U", 0.0),
        "enrichment": enrichment,
        "environment": environment,
        "total_cylinders": p["TOTAL_CYLINDERS"],
        "cylinders_per_pack": p["CYLINDERS_PER_PACK"],
    }

    return materials, geometry, dims


# =============================================================================
# SETTINGS
# =============================================================================


def create_settings(p, dims):
    """Create OpenMC settings with distributed source."""
    settings = openmc.Settings()
    settings.run_mode = "eigenvalue"
    settings.particles = int(p["PARTICLES"])
    settings.batches = int(p["BATCHES"])
    settings.inactive = int(p["INACTIVE"])

    # Box source encompassing all fissile regions.
    # This intentionally spans the full fissile envelope (including inter-unit gaps).
    t_wall = dims["T_WALL"]
    x_min = t_wall
    x_max = dims["ARRAY_X"] - t_wall
    y_min = t_wall
    y_max = dims["ARRAY_Y"] - t_wall
    z_min = t_wall
    z_max = dims["ARRAY_Z"] - t_wall

    settings.source = openmc.IndependentSource(
        space=openmc.stats.Box(
            lower_left=(x_min, y_min, z_min),
            upper_right=(x_max, y_max, z_max),
        )
    )

    return settings


# =============================================================================
# PLOTS
# =============================================================================


def create_plots(dims, materials):
    """Create visualization plots for the cascade array."""

    color_mapping = get_color_mapping(materials)

    plots = openmc.Plots()

    total_x = dims["TOTAL_X"]
    total_y = dims["TOTAL_Y"]
    total_z = dims["TOTAL_Z"]

    array_x = dims["ARRAY_X"]
    array_y = dims["ARRAY_Y"]
    array_z = dims["ARRAY_Z"]

    t_wall = dims["T_WALL"]
    H_inner = dims["H_INNER"]

    # Center of array
    center_x = array_x / 2
    center_y = array_y / 2
    center_z = array_z / 2

    # XY slice: cut through middle of fissile region in first layer
    z_slice = t_wall + H_inner / 2

    plot_xy = openmc.Plot(name="xy")
    plot_xy.basis = "xy"
    plot_xy.origin = (center_x, center_y, z_slice)
    plot_xy.width = (total_x * 1.05, total_y * 1.05)
    plot_xy.pixels = (2000, 2000)
    plot_xy.color_by = "material"
    plot_xy.colors = color_mapping
    plots.append(plot_xy)

    # XZ slice: cut through center of first Y-line cylinders.
    y_slice = dims["R_OUTER"]

    plot_xz = openmc.Plot(name="xz")
    plot_xz.basis = "xz"
    plot_xz.origin = (center_x, y_slice, center_z)
    plot_xz.width = (total_x * 1.05, total_z * 1.05)
    plot_xz.pixels = (2000, 1000)
    plot_xz.color_by = "material"
    plot_xz.colors = color_mapping
    plots.append(plot_xz)

    # YZ slice: cut through center of first column cylinders.
    x_slice = dims["R_OUTER"]

    plot_yz = openmc.Plot(name="yz")
    plot_yz.basis = "yz"
    plot_yz.origin = (x_slice, center_y, center_z)
    plot_yz.width = (total_y * 1.05, total_z * 1.05)
    plot_yz.pixels = (2000, 1000)
    plot_yz.color_by = "material"
    plot_yz.colors = color_mapping
    plots.append(plot_yz)

    return plots, get_color_legend(materials)


# =============================================================================
# SUMMARY
# =============================================================================


def print_summary(p, dims):
    """Print case summary."""
    boundary = dims.get("BOUNDARY_TYPE", "vacuum")
    if boundary == "vacuum":
        boundary_detail = (
            f"vacuum (environment shell = {dims['REFLECTOR_THICKNESS_INPUT']:.2f} cm)"
        )
    else:
        boundary_detail = (
            f"reflective (half-gap pads: XY={dims['GAP_XY'] / 2:.2f} cm, "
            f"Z={dims['GAP_Z'] / 2:.2f} cm)"
        )

    print(
        f"""
================================================================================
                      CASCADE ARRAY SUMMARY
================================================================================
HIERARCHY
  Level 1: Cylinder     R_inner={dims['R_INNER']:.2f} cm, H_inner={dims['H_INNER']:.2f} cm
  Level 2: Pack         {dims['I']} x {dims['J']} x {dims['K']} = {dims['cylinders_per_pack']} cylinders
  Level 3: Root         Pack + boundary shell

TOTAL CYLINDERS: {dims['total_cylinders']}

CYLINDER GEOMETRY
  Inner radius:         {dims['R_INNER']:>8.2f} cm
  Outer radius:         {dims['R_OUTER']:>8.2f} cm
  Wall thickness:       {dims['T_WALL']:>8.3f} cm
  Inner height:         {dims['H_INNER']:>8.2f} cm
  Outer height:         {dims['H_OUTER']:>8.2f} cm

SPACING
  Horizontal gap (XY):  {dims['GAP_XY']:>8.2f} cm  (wall-to-wall)
  Vertical gap (Z):     {dims['GAP_Z']:>8.2f} cm  (cap-to-cap)
  Cylinder pitch (XY):  {dims['PITCH_CYLINDER']:>8.2f} cm
  Cylinder pitch (Z):   {dims['PITCH_Z']:>8.2f} cm

PACK DIMENSIONS
  X (i direction):      {dims['CASSETTE_X']:>8.2f} cm
  Y (j direction):      {dims['CASSETTE_Y']:>8.2f} cm
  Z (k direction):      {dims['CASSETTE_Z']:>8.2f} cm

ARRAY DIMENSIONS
  X (pack width):       {dims['ARRAY_X']:>8.2f} cm
  Y (pack depth):       {dims['ARRAY_Y']:>8.2f} cm
  Z (stack height):     {dims['ARRAY_Z']:>8.2f} cm

TOTAL DIMENSIONS (with boundary shell)
  X:                    {dims['TOTAL_X']:>8.2f} cm
  Y:                    {dims['TOTAL_Y']:>8.2f} cm
  Z:                    {dims['TOTAL_Z']:>8.2f} cm
  Boundary:             {boundary_detail}

FISSILE MATERIAL
  Type:                 {dims['fissile_material'].upper()}
  Enrichment:           {dims['enrichment']:>8.2f} wt% U-235
  Density:              {dims['fissile_density']:>8.3f} g/cc
  H/U ratio:            {dims['h_to_u']:>8.1f}

ENVIRONMENT
  Material:             {dims['environment']}

SIMULATION
  {int(p['PARTICLES'])} particles x {int(p['BATCHES'])} batches ({int(p['INACTIVE'])} inactive)
================================================================================
"""
    )
