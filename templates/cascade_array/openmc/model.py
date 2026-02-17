#!/usr/bin/env python3
"""
================================================================================
CASCADE ARRAY CRITICALITY MODEL - OpenMC
================================================================================
Template:   cascade_array
Problem:    Hierarchical array of cylinders in cassettes arranged in rows

Geometry Hierarchy:
    Level 1: Cylinder    - Single steel-clad vessel with fissile material
    Level 2: Cassette    - i x j x k array of cylinders
    Level 3: Row         - M cassettes in a line
    Level 4: Cascade     - 2 rows + reflector (ROOT)

Applications: Cascade hall layouts, process equipment arrays
================================================================================
"""

import openmc
from critbuddy.core.materials import (
    create_uf6,
    create_uo2f2,
    create_steel,
    create_humid_air,
    create_air,
    create_water,
    get_material,
    get_color_mapping,
    get_color_legend,
)


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

    # Fissile material (UF6 or UO2F2)
    if fissile_type == "uo2f2":
        h_to_u = p.get("H_TO_U_RATIO", 0.0)
        m_fissile = create_uo2f2(enrichment, h_to_u=h_to_u)
    else:
        density = p.get("FISSILE_DENSITY", 5.09)
        m_fissile = create_uf6(enrichment, density=density)

    # Steel wall
    m_steel = get_material(p["WALL_MATERIAL"], solver="openmc")

    # Environment between units (humid air or dry air only - no water)
    environment = p["ENVIRONMENT_MATERIAL"]
    if environment == "air":
        m_moderator = create_air()
    else:
        # Default to humid air (100% RH at 40C)
        m_moderator = create_humid_air()

    # 30cm water reflector
    m_reflector = create_water(1.0)

    materials = openmc.Materials([m_fissile, m_steel, m_moderator, m_reflector])

    # =========================================================================
    # DIMENSIONS
    # =========================================================================

    # Cylinder dimensions
    R_inner = p["R_INNER"]
    R_outer = p["R_OUTER"]
    H_inner = p["H_INNER"]
    H_outer = p["H_OUTER"]
    t_wall = p["T_WALL"]

    # Cassette dimensions
    i_count = p["I"]  # cylinders in X
    j_count = p["J"]  # cylinders in Y
    k_count = p["K"]  # cylinders in Z (layers)
    pitch_cyl = p["PITCH_CYLINDER"]
    pitch_z = p["PITCH_Z"]

    # Row dimensions
    M = p["M"]  # cassettes per row
    pitch_cassette = p["PITCH_CASSETTE"]

    # Cascade dimensions
    pitch_row = p["PITCH_ROW"]
    reflector = p["REFLECTOR_THICKNESS"]

    # Calculate cassette dimensions
    cassette_x = i_count * pitch_cyl
    cassette_y = j_count * pitch_cyl

    # =========================================================================
    # CREATE CYLINDERS EXPLICITLY
    # =========================================================================

    cells = []
    cell_id = 1
    cylinder_regions = []  # Track cylinder regions for moderator exclusion

    # Loop through all cylinder positions
    # Hierarchy: 2 rows -> M cassettes per row -> i x j x k cylinders per cassette

    for row_idx in range(2):  # 2 rows
        row_y_offset = row_idx * pitch_row

        for cassette_idx in range(M):  # M cassettes per row
            cassette_x_offset = cassette_idx * pitch_cassette

            for layer in range(k_count):  # k layers in Z
                z_offset = layer * pitch_z

                for jj in range(j_count):  # j cylinders in Y
                    for ii in range(i_count):  # i cylinders in X
                        # Calculate center position of this cylinder
                        # Cylinder centered within its cell
                        x_center = cassette_x_offset + (ii + 0.5) * pitch_cyl
                        y_center = row_y_offset + (jj + 0.5) * pitch_cyl
                        z_base = z_offset  # bottom of cylinder

                        # Z bounds for this cylinder
                        z_bot = z_base
                        z_bot_inner = z_base + t_wall
                        z_top_inner = z_base + t_wall + H_inner
                        z_top = z_base + H_outer

                        # Create cylinder surfaces at this position
                        cyl_inner = openmc.ZCylinder(
                            x0=x_center, y0=y_center, r=R_inner,
                            name=f"cyl_inner_{row_idx}_{cassette_idx}_{layer}_{jj}_{ii}"
                        )
                        cyl_outer = openmc.ZCylinder(
                            x0=x_center, y0=y_center, r=R_outer,
                            name=f"cyl_outer_{row_idx}_{cassette_idx}_{layer}_{jj}_{ii}"
                        )

                        # Z planes for this cylinder
                        z_bot_plane = openmc.ZPlane(z0=z_bot, name=f"z_bot_{row_idx}_{cassette_idx}_{layer}_{jj}_{ii}")
                        z_bot_inner_plane = openmc.ZPlane(z0=z_bot_inner, name=f"z_bot_inner_{row_idx}_{cassette_idx}_{layer}_{jj}_{ii}")
                        z_top_inner_plane = openmc.ZPlane(z0=z_top_inner, name=f"z_top_inner_{row_idx}_{cassette_idx}_{layer}_{jj}_{ii}")
                        z_top_plane = openmc.ZPlane(z0=z_top, name=f"z_top_{row_idx}_{cassette_idx}_{layer}_{jj}_{ii}")

                        # Fissile core cell
                        c_fissile = openmc.Cell(
                            cell_id=cell_id,
                            name=f"fissile_{row_idx}_{cassette_idx}_{layer}_{jj}_{ii}",
                            fill=m_fissile
                        )
                        c_fissile.region = -cyl_inner & +z_bot_inner_plane & -z_top_inner_plane
                        cells.append(c_fissile)
                        cell_id += 1

                        # Wall cell (cylindrical shell)
                        c_wall = openmc.Cell(
                            cell_id=cell_id,
                            name=f"wall_{row_idx}_{cassette_idx}_{layer}_{jj}_{ii}",
                            fill=m_steel
                        )
                        c_wall.region = +cyl_inner & -cyl_outer & +z_bot_inner_plane & -z_top_inner_plane
                        cells.append(c_wall)
                        cell_id += 1

                        # Bottom cap
                        c_cap_bot = openmc.Cell(
                            cell_id=cell_id,
                            name=f"cap_bot_{row_idx}_{cassette_idx}_{layer}_{jj}_{ii}",
                            fill=m_steel
                        )
                        c_cap_bot.region = -cyl_outer & +z_bot_plane & -z_bot_inner_plane
                        cells.append(c_cap_bot)
                        cell_id += 1

                        # Top cap
                        c_cap_top = openmc.Cell(
                            cell_id=cell_id,
                            name=f"cap_top_{row_idx}_{cassette_idx}_{layer}_{jj}_{ii}",
                            fill=m_steel
                        )
                        c_cap_top.region = -cyl_outer & +z_top_inner_plane & -z_top_plane
                        cells.append(c_cap_top)
                        cell_id += 1

                        # Track full cylinder region for moderator exclusion
                        cylinder_regions.append(-cyl_outer & +z_bot_plane & -z_top_plane)

    # =========================================================================
    # BOUNDING BOX AND REFLECTOR
    # =========================================================================

    # Array dimensions
    array_x = p["ARRAY_X"]
    array_y = p["ARRAY_Y"]
    array_z = p["ARRAY_Z"]

    # Total dimensions with reflector
    total_x = array_x + 2 * reflector
    total_y = array_y + 2 * reflector
    total_z = array_z + 2 * reflector

    # Bounding box surfaces (vacuum boundary)
    x_min = openmc.XPlane(x0=-reflector, boundary_type="vacuum", name="x_min")
    x_max = openmc.XPlane(x0=array_x + reflector, boundary_type="vacuum", name="x_max")
    y_min = openmc.YPlane(y0=-reflector, boundary_type="vacuum", name="y_min")
    y_max = openmc.YPlane(y0=array_y + reflector, boundary_type="vacuum", name="y_max")
    z_min = openmc.ZPlane(z0=-reflector, boundary_type="vacuum", name="z_min")
    z_max = openmc.ZPlane(z0=array_z + reflector, boundary_type="vacuum", name="z_max")

    # Inner box surfaces (array boundary - separates moderator from reflector)
    array_x_min = openmc.XPlane(x0=0, name="array_x_min")
    array_x_max = openmc.XPlane(x0=array_x, name="array_x_max")
    array_y_min = openmc.YPlane(y0=0, name="array_y_min")
    array_y_max = openmc.YPlane(y0=array_y, name="array_y_max")
    array_z_min = openmc.ZPlane(z0=0, name="array_z_min")
    array_z_max = openmc.ZPlane(z0=array_z, name="array_z_max")

    # Moderator region (inside array, outside cylinders)
    moderator_region = (+array_x_min & -array_x_max &
                        +array_y_min & -array_y_max &
                        +array_z_min & -array_z_max)

    # Exclude all cylinder regions from moderator
    for cyl_region in cylinder_regions:
        moderator_region = moderator_region & ~cyl_region

    c_moderator = openmc.Cell(cell_id=cell_id, name="moderator", fill=m_moderator)
    c_moderator.region = moderator_region
    cells.append(c_moderator)
    cell_id += 1

    # Reflector region (outside array, inside bounding box)
    reflector_region = (+x_min & -x_max & +y_min & -y_max & +z_min & -z_max &
                        ~(+array_x_min & -array_x_max &
                          +array_y_min & -array_y_max &
                          +array_z_min & -array_z_max))

    c_reflector = openmc.Cell(cell_id=cell_id, name="reflector", fill=m_reflector)
    c_reflector.region = reflector_region
    cells.append(c_reflector)

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
        # Cassette
        "I": i_count,
        "J": j_count,
        "K": k_count,
        "PITCH_CYLINDER": pitch_cyl,
        "PITCH_Z": pitch_z,
        "CASSETTE_X": cassette_x,
        "CASSETTE_Y": cassette_y,
        "CASSETTE_Z": k_count * pitch_z,
        # Row
        "M": M,
        "PITCH_CASSETTE": pitch_cassette,
        "ROW_X": M * pitch_cassette,
        # Cascade
        "PITCH_ROW": pitch_row,
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
        "h_to_u_ratio": p.get("H_TO_U_RATIO", 0.0),
        "enrichment": enrichment,
        "environment_material": environment,
        "total_cylinders": p["TOTAL_CYLINDERS"],
        "total_cassettes": p["TOTAL_CASSETTES"],
        "cylinders_per_cassette": p["CYLINDERS_PER_CASSETTE"],
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

    # Box source encompassing all fissile regions
    # First cylinder center is at (pitch/2, pitch/2, t_wall + H_inner/2)
    pitch_cyl = dims["PITCH_CYLINDER"]
    t_wall = dims["T_WALL"]
    H_inner = dims["H_INNER"]
    R_inner = dims["R_INNER"]

    # Source box: cover all cylinders with some margin
    x_min = pitch_cyl / 2 - R_inner * 0.5
    x_max = dims["ARRAY_X"] - pitch_cyl / 2 + R_inner * 0.5
    y_min = pitch_cyl / 2 - R_inner * 0.5
    y_max = dims["ARRAY_Y"] - pitch_cyl / 2 + R_inner * 0.5
    z_min = t_wall + H_inner * 0.25
    z_max = dims["ARRAY_Z"] - dims["PITCH_Z"] + t_wall + H_inner * 0.75

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

    reflector = dims["REFLECTOR_THICKNESS"]
    array_x = dims["ARRAY_X"]
    array_y = dims["ARRAY_Y"]
    array_z = dims["ARRAY_Z"]

    # Cylinder positions
    pitch_cyl = dims["PITCH_CYLINDER"]
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

    # XZ slice: cut through center of first row of cylinders (y = pitch/2)
    y_slice = pitch_cyl / 2

    plot_xz = openmc.Plot(name="xz")
    plot_xz.basis = "xz"
    plot_xz.origin = (center_x, y_slice, center_z)
    plot_xz.width = (total_x * 1.05, total_z * 1.05)
    plot_xz.pixels = (2000, 1000)
    plot_xz.color_by = "material"
    plot_xz.colors = color_mapping
    plots.append(plot_xz)

    # YZ slice: cut through center of first column of cylinders (x = pitch/2)
    x_slice = pitch_cyl / 2

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
    print(
        f"""
================================================================================
                      CASCADE ARRAY SUMMARY
================================================================================
HIERARCHY
  Level 1: Cylinder     R_inner={dims['R_INNER']:.2f} cm, H_inner={dims['H_INNER']:.2f} cm
  Level 2: Cassette     {dims['I']} x {dims['J']} x {dims['K']} = {dims['cylinders_per_cassette']} cylinders
  Level 3: Row          {dims['M']} cassettes per row
  Level 4: Cascade      2 rows, {dims['total_cassettes']} cassettes total

TOTAL CYLINDERS: {dims['total_cylinders']}

CYLINDER GEOMETRY
  Inner radius:         {dims['R_INNER']:>8.2f} cm
  Outer radius:         {dims['R_OUTER']:>8.2f} cm
  Wall thickness:       {dims['T_WALL']:>8.3f} cm
  Inner height:         {dims['H_INNER']:>8.2f} cm
  Outer height:         {dims['H_OUTER']:>8.2f} cm

SPACING
  Cylinder pitch (XY):  {dims['PITCH_CYLINDER']:>8.2f} cm  (gap = {p['D_CYLINDER']:.2f} cm)
  Cylinder pitch (Z):   {dims['PITCH_Z']:>8.2f} cm  (gap = {p['D_CYLINDER']:.2f} cm)
  Cassette pitch:       {dims['PITCH_CASSETTE']:>8.2f} cm  (gap = {p['D_CASSETTE']:.2f} cm)
  Row pitch:            {dims['PITCH_ROW']:>8.2f} cm  (gap = {p['D_ROW']:.2f} cm)

CASSETTE DIMENSIONS
  X (i direction):      {dims['CASSETTE_X']:>8.2f} cm
  Y (j direction):      {dims['CASSETTE_Y']:>8.2f} cm
  Z (k direction):      {dims['CASSETTE_Z']:>8.2f} cm

ARRAY DIMENSIONS
  X (row length):       {dims['ARRAY_X']:>8.2f} cm
  Y (2 rows):           {dims['ARRAY_Y']:>8.2f} cm
  Z (stack height):     {dims['ARRAY_Z']:>8.2f} cm

TOTAL DIMENSIONS (with reflector)
  X:                    {dims['TOTAL_X']:>8.2f} cm
  Y:                    {dims['TOTAL_Y']:>8.2f} cm
  Z:                    {dims['TOTAL_Z']:>8.2f} cm
  Reflector:            {dims['REFLECTOR_THICKNESS']:>8.2f} cm

FISSILE MATERIAL
  Type:                 {dims['fissile_material'].upper()}
  Enrichment:           {dims['enrichment']:>8.2f} wt% U-235
  Density:              {dims['fissile_density']:>8.3f} g/cc
  H/U ratio:            {dims['h_to_u_ratio']:>8.1f}

ENVIRONMENT
  Material:             {dims['environment_material']}

SIMULATION
  {int(p['PARTICLES'])} particles x {int(p['BATCHES'])} batches ({int(p['INACTIVE'])} inactive)
================================================================================
"""
    )
