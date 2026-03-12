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
    r_fissile: float,
    r_inner: float,
    r_outer: float,
    h_inner: float,
    h_outer: float,
    t_wall: float,
    t_film: float,
    fill_fraction: float,
    fissile_height: float,
    m_fissile,
    m_film,
    m_void,
    m_wall,
    cells: list,
    cylinder_regions: list,
    cell_id: int,
) -> int:
    """Create fissile, optional film, wall, bottom-cap, and top-cap cells."""
    suffix = f"{placement.layer}_{placement.j_idx}_{placement.i_idx}"
    z_bottom = placement.z_base
    z_bottom_inner = z_bottom + t_wall
    z_top_inner = z_bottom + t_wall + h_inner
    z_top = z_bottom + h_outer

    cyl_fissile = openmc.ZCylinder(
        x0=placement.x_center,
        y0=placement.y_center,
        r=r_fissile,
        name=f"cyl_fissile_{suffix}",
    )
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

    if fill_fraction < 1.0:
        z_fill = z_bottom_inner + fissile_height
        z_fill_plane = openmc.ZPlane(z0=z_fill, name=f"z_fill_{suffix}")

        c_fissile = openmc.Cell(cell_id=cell_id, name=f"fissile_{suffix}", fill=m_fissile)
        c_fissile.region = -cyl_fissile & +z_bottom_inner_plane & -z_fill_plane
        cells.append(c_fissile)
        cell_id += 1

        c_void = openmc.Cell(cell_id=cell_id, name=f"void_{suffix}", fill=m_void)
        c_void.region = -cyl_fissile & +z_fill_plane & -z_top_inner_plane
        cells.append(c_void)
        cell_id += 1
    else:
        c_fissile = openmc.Cell(cell_id=cell_id, name=f"fissile_{suffix}", fill=m_fissile)
        c_fissile.region = -cyl_fissile & +z_bottom_inner_plane & -z_top_inner_plane
        cells.append(c_fissile)
        cell_id += 1

    if t_film > 0.0:
        c_film = openmc.Cell(cell_id=cell_id, name=f"film_{suffix}", fill=m_film)
        c_film.region = +cyl_fissile & -cyl_inner & +z_bottom_inner_plane & -z_top_inner_plane
        cells.append(c_film)
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


def _make_box(
    x_lo: float,
    x_hi: float,
    y_lo: float,
    y_hi: float,
    z_lo: float,
    z_hi: float,
    name: str = "",
):
    """Create an axis-aligned transmission box and return region plus surfaces."""
    x_min = openmc.XPlane(x0=x_lo, name=f"{name}x_min")
    x_max = openmc.XPlane(x0=x_hi, name=f"{name}x_max")
    y_min = openmc.YPlane(y0=y_lo, name=f"{name}y_min")
    y_max = openmc.YPlane(y0=y_hi, name=f"{name}y_max")
    z_min = openmc.ZPlane(z0=z_lo, name=f"{name}z_min")
    z_max = openmc.ZPlane(z0=z_hi, name=f"{name}z_max")
    region = +x_min & -x_max & +y_min & -y_max & +z_min & -z_max
    return region, (x_min, x_max, y_min, y_max, z_min, z_max)


def _subtract_cylinders(region, cylinder_regions):
    """Subtract all cylinder envelopes from a region."""
    for cyl_region in cylinder_regions:
        region = region & ~cyl_region
    return region


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

    # Environment between units (humid air, dry air, or water)
    environment = p["ENVIRONMENT_MATERIAL"]
    m_moderator = create_environment_material(
        environment_material=environment,
        environment_density=p.get("ENV_DENSITY"),
    )
    m_film = None
    if p.get("T_FILM", 0.0) > 0.0:
        film_material = p["FILM_MATERIAL"]
        if film_material == p["WALL_MATERIAL"]:
            m_film = m_wall
        else:
            m_film = get_material(film_material, solver="openmc")

    fill_fraction = p.get("FILL_FRACTION", 1.0)
    fissile_height = p.get("FISSILE_HEIGHT", p["H_INNER"])
    m_void = None
    material_list = []

    def _append_material(material):
        if material is None:
            return
        if all(existing is not material for existing in material_list):
            material_list.append(material)

    _append_material(m_fissile)
    _append_material(m_wall)
    _append_material(m_film)
    _append_material(m_moderator)

    if fill_fraction < 1.0:
        m_void = get_material(p.get("VOID_MATERIAL", "void"), solver="openmc")
        _append_material(m_void)

    materials = openmc.Materials(material_list)

    # =========================================================================
    # DIMENSIONS
    # =========================================================================

    # Cylinder dimensions
    R_fissile = p["R_FISSILE"]
    R_inner = p["R_INNER"]
    R_outer = p["R_OUTER"]
    H_inner = p["H_INNER"]
    H_outer = p["H_OUTER"]
    t_wall = p["T_WALL"]
    t_film = p.get("T_FILM", 0.0)

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
            r_fissile=R_fissile,
            r_inner=R_inner,
            r_outer=R_outer,
            h_inner=H_inner,
            h_outer=H_outer,
            t_wall=t_wall,
            t_film=t_film,
            fill_fraction=fill_fraction,
            fissile_height=fissile_height,
            m_fissile=m_fissile,
            m_film=m_film,
            m_void=m_void,
            m_wall=m_wall,
            cells=cells,
            cylinder_regions=cylinder_regions,
            cell_id=cell_id,
        )

    # =========================================================================
    # BOUNDING BOX AND OUTER SHELL
    # =========================================================================
    # Region contract for this section:
    #   system_region    : total region of entire problem (outer box)
    #   cassette_region     : cassette region (inner box)
    #   moderator_region : cassette region minus all cylinders (inner box)
    #   shell_region     : system_region minus array_region
    #
    # Boundary behavior on system_region:
    #   x: periodic (x_min <-> x_max) : to simulate repeating cassettes
    #   y: vacuum
    #   z: vacuum

    # Array dimensions
    array_x = p["ARRAY_X"]
    array_y = p["ARRAY_Y"]
    array_z = p["ARRAY_Z"]

    # 1) Compute outer and inner box bounds
    # Outer system box:
    # - X uses half-gap padding for periodic continuation.
    # - Y/Z use explicit shell thickness for vacuum leakage.
    outer_x = (-gap_xy / 2.0, array_x + gap_xy / 2.0)
    outer_y = (-reflector, array_y + reflector)
    outer_z = (-reflector, array_z + reflector)

    # Inner array box (actual cassette extent).
    inner_x = (0.0, array_x)
    inner_y = (0.0, array_y)
    inner_z = (0.0, array_z)

    total_x = outer_x[1] - outer_x[0]
    total_y = outer_y[1] - outer_y[0]
    total_z = outer_z[1] - outer_z[0]

    # 2) Build system and array regions from box surfaces
    system_region, outer_surfaces = _make_box(*outer_x, *outer_y, *outer_z)
    x_min, x_max, y_min, y_max, z_min, z_max = outer_surfaces

    # Assign fixed boundary behavior on the outer system box.
    x_min.boundary_type = x_max.boundary_type = "periodic"
    y_min.boundary_type = y_max.boundary_type = "vacuum"
    z_min.boundary_type = z_max.boundary_type = "vacuum"

    # Periodic pair in X (reverse link is set automatically by OpenMC).
    x_min.periodic_surface = x_max

    # Inner array box (transmission surfaces used only for region partitioning).
    array_region, _ = _make_box(*inner_x, *inner_y, *inner_z, name="array_")

    # 3) Apply region algebra
    moderator_region = _subtract_cylinders(array_region, cylinder_regions)
    shell_region = system_region & ~array_region

    # 4) Instantiate moderator and shell cells
    c_moderator = openmc.Cell(cell_id=cell_id, name="moderator", fill=m_moderator)
    c_moderator.region = moderator_region
    cells.append(c_moderator)
    cell_id += 1

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
        "R_FISSILE": R_fissile,
        "R_INNER": R_inner,
        "R_OUTER": R_outer,
        "H_INNER": H_inner,
        "H_OUTER": H_outer,
        "T_WALL": t_wall,
        "T_FILM": t_film,
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
        "film_material": p.get("FILM_MATERIAL"),
        "FILL_FRACTION": fill_fraction,
        "FISSILE_HEIGHT": fissile_height,
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
    radial_offset = dims["T_WALL"] + dims.get("T_FILM", 0.0)
    x_min = radial_offset
    x_max = dims["ARRAY_X"] - radial_offset
    y_min = radial_offset
    y_max = dims["ARRAY_Y"] - radial_offset
    z_min = dims["T_WALL"]
    z_max = dims["ARRAY_Z"] - dims["T_WALL"]

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
    fissile_height = dims.get("FISSILE_HEIGHT", H_inner)

    # Center of array
    center_x = array_x / 2
    center_y = array_y / 2
    center_z = array_z / 2

    # XY slice: cut through middle of fissile region in first layer
    z_slice = t_wall + fissile_height / 2

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
