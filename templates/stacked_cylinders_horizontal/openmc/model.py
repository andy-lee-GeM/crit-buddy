#!/usr/bin/env python3
"""
================================================================================
STACKED HORIZONTAL CYLINDERS CRITICALITY MODEL - OpenMC
================================================================================
Template:   stacked_cylinders_horizontal
Problem:    Horizontal UF6 shipping cylinders in pyramid/rectangular stacks
Geometry:   Cylinders lying on side, stacked with optional pyramid pattern
Applications: Warehouse storage, shipping cylinder stacking studies
================================================================================
"""

import openmc
from critbuddy.core.materials import create_uf6, get_material


def build_model(p):
    """
    Build OpenMC model for stacked horizontal cylinders.

    Coordinate system:
    - X: cylinder length direction (all cylinders aligned)
    - Y: side-by-side arrangement within each layer
    - Z: vertical stacking direction
    - Origin at center (XY) and floor surface (Z=0)
    """

    # ══════════════════════════════════════════════════════════════════════════
    # MATERIALS
    # ══════════════════════════════════════════════════════════════════════════

    m_uf6 = create_uf6(p["ENRICHMENT"], p["UF6_DENSITY"])
    m_wall = get_material(p["WALL_MATERIAL"], solver="openmc")
    m_env = get_material(p["ENVIRONMENT"], solver="openmc")

    if p["FLOOR_MATERIAL"] != "none":
        m_floor = get_material(p["FLOOR_MATERIAL"], solver="openmc")
        materials = openmc.Materials([m_uf6, m_wall, m_env, m_floor])
    else:
        m_floor = None
        materials = openmc.Materials([m_uf6, m_wall, m_env])

    # ══════════════════════════════════════════════════════════════════════════
    # SURFACES
    # ══════════════════════════════════════════════════════════════════════════

    r_inner = p["R_INNER"]
    r_outer = p["R_OUTER"]
    x_half = p["X_HALF"]
    x_inner_half = p["X_INNER_HALF"]
    cylinder_positions = p["CYLINDER_POSITIONS"]

    # X planes (shared by all cylinders - they all have same length)
    x_neg_outer = openmc.XPlane(x0=-x_half, name="x_neg_outer")
    x_pos_outer = openmc.XPlane(x0=x_half, name="x_pos_outer")
    x_neg_inner = openmc.XPlane(x0=-x_inner_half, name="x_neg_inner")
    x_pos_inner = openmc.XPlane(x0=x_inner_half, name="x_pos_inner")

    # Create cylindrical surfaces for each cylinder position
    # Cylinders are aligned along X axis, positioned at different Y, Z
    cyl_inner_surfs = []
    cyl_outer_surfs = []

    for i, pos in enumerate(cylinder_positions):
        y_pos = pos["y"]
        z_pos = pos["z"]
        cyl_inner_surfs.append(
            openmc.XCylinder(r=r_inner, y0=y_pos, z0=z_pos, name=f"cyl_inner_{i}")
        )
        cyl_outer_surfs.append(
            openmc.XCylinder(r=r_outer, y0=y_pos, z0=z_pos, name=f"cyl_outer_{i}")
        )

    # Boundary surfaces
    boundary = p["BOUNDARY"]
    x_bound_neg = openmc.XPlane(x0=-x_half - boundary, name="x_bound_neg", boundary_type="vacuum")
    x_bound_pos = openmc.XPlane(x0=x_half + boundary, name="x_bound_pos", boundary_type="vacuum")
    y_bound_neg = openmc.YPlane(y0=-p["ARRAY_Y"]/2 - boundary, name="y_bound_neg", boundary_type="vacuum")
    y_bound_pos = openmc.YPlane(y0=p["ARRAY_Y"]/2 + boundary, name="y_bound_pos", boundary_type="vacuum")
    z_bound_neg = openmc.ZPlane(z0=p["Z_FLOOR_BOTTOM"], name="z_bound_neg", boundary_type="vacuum")
    z_bound_pos = openmc.ZPlane(z0=p["Z_ENV_TOP"], name="z_bound_pos", boundary_type="vacuum")

    # Floor surface
    z_floor_top = openmc.ZPlane(z0=0.0, name="z_floor_top")

    # ══════════════════════════════════════════════════════════════════════════
    # CELLS
    # ══════════════════════════════════════════════════════════════════════════

    cells = []
    cell_id = 1

    # Create UF6 and wall cells for each cylinder
    for i, pos in enumerate(cylinder_positions):
        # UF6 region (inside cylinder, within internal length)
        c_uf6 = openmc.Cell(cell_id=cell_id, name=f"UF6_{i}", fill=m_uf6)
        c_uf6.region = -cyl_inner_surfs[i] & +x_neg_inner & -x_pos_inner
        cells.append(c_uf6)
        cell_id += 1

        # Wall - cylindrical shell (radial wall)
        c_wall_radial = openmc.Cell(cell_id=cell_id, name=f"Wall_radial_{i}", fill=m_wall)
        c_wall_radial.region = +cyl_inner_surfs[i] & -cyl_outer_surfs[i] & +x_neg_outer & -x_pos_outer
        cells.append(c_wall_radial)
        cell_id += 1

        # Wall - left end cap
        c_wall_left = openmc.Cell(cell_id=cell_id, name=f"Wall_left_{i}", fill=m_wall)
        c_wall_left.region = -cyl_inner_surfs[i] & +x_neg_outer & -x_neg_inner
        cells.append(c_wall_left)
        cell_id += 1

        # Wall - right end cap
        c_wall_right = openmc.Cell(cell_id=cell_id, name=f"Wall_right_{i}", fill=m_wall)
        c_wall_right.region = -cyl_inner_surfs[i] & +x_pos_inner & -x_pos_outer
        cells.append(c_wall_right)
        cell_id += 1

    # Environment cell (outside all cylinders, above floor)
    outside_all_cylinders = +z_floor_top
    for i in range(len(cylinder_positions)):
        outside_all_cylinders = outside_all_cylinders & +cyl_outer_surfs[i]

    # Also need to be within the main cylinder X extent or in the boundary regions
    c_env = openmc.Cell(cell_id=cell_id, name="Environment", fill=m_env)
    c_env.region = (
        outside_all_cylinders &
        +x_bound_neg & -x_bound_pos &
        +y_bound_neg & -y_bound_pos &
        -z_bound_pos
    )
    cells.append(c_env)
    cell_id += 1

    # Floor cell (if present)
    if m_floor is not None:
        c_floor = openmc.Cell(cell_id=cell_id, name="Floor", fill=m_floor)
        c_floor.region = (
            +z_bound_neg & -z_floor_top &
            +x_bound_neg & -x_bound_pos &
            +y_bound_neg & -y_bound_pos
        )
        cells.append(c_floor)
        cell_id += 1

    # ══════════════════════════════════════════════════════════════════════════
    # GEOMETRY
    # ══════════════════════════════════════════════════════════════════════════

    universe = openmc.Universe(cells=cells)
    geometry = openmc.Geometry(universe)

    # Dimensions for plotting
    dims = {
        "total_x": p["TOTAL_X"],
        "total_y": p["TOTAL_Y"],
        "total_z": p["TOTAL_Z"],
        "array_x": p["ARRAY_X"],
        "array_y": p["ARRAY_Y"],
        "array_z": p["ARRAY_Z"],
        "floor_thickness": p["FLOOR_THICKNESS"],
        "num_cylinders": p["TOTAL_CYLINDERS"],
        "stacking_pattern": p["STACKING_PATTERN"],
        "r_outer": r_outer,
    }
    return materials, geometry, dims


def create_settings(p, dims):
    """Create OpenMC settings."""
    settings = openmc.Settings()
    settings.run_mode = "eigenvalue"
    settings.particles = int(p["PARTICLES"])
    settings.batches = int(p["BATCHES"])
    settings.inactive = int(p["INACTIVE"])
    settings.source = openmc.IndependentSource(
        space=openmc.stats.Point((p["KSRC_X"], p["KSRC_Y"], p["KSRC_Z"]))
    )
    return settings


def create_plots(dims, materials):
    """Create visualization plots."""
    from critbuddy.core.materials import get_color_mapping, get_color_legend

    total_x = dims["total_x"]
    total_y = dims["total_y"]
    total_z = dims["total_z"]
    floor_t = dims["floor_thickness"]
    array_z = dims["array_z"]

    # Z center for plotting (middle of cylinder array)
    z_center = array_z / 2

    color_mapping = get_color_mapping(materials)
    plots = openmc.Plots()

    # XY slice (top-down view - shows cylinder length)
    p1 = openmc.Plot(name="xy")
    p1.basis = "xy"
    p1.origin = (0, 0, z_center)
    p1.width = (total_x * 1.1, total_y * 1.1)
    p1.pixels = (600, 600)
    p1.color_by = "material"
    p1.colors = color_mapping
    plots.append(p1)

    # YZ slice (front view - shows stacking pattern and floor)
    p2 = openmc.Plot(name="xz")
    p2.basis = "yz"
    p2.origin = (0, 0, (array_z - floor_t) / 2)
    p2.width = (total_y * 1.1, (total_z + floor_t) * 1.1)
    p2.pixels = (600, 600)
    p2.color_by = "material"
    p2.colors = color_mapping
    plots.append(p2)

    return plots, get_color_legend(materials)


def print_summary(p, dims):
    """Print case summary."""
    print(f"""
================================================================================
                         CASE SUMMARY
================================================================================
FISSILE MATERIAL
  Enrichment:         {p['ENRICHMENT']:>8.2f} wt% U-235
  Density:            {p['UF6_DENSITY']:>8.3f} g/cc

CYLINDER
  Type:               {p['CYLINDER_TYPE']} ({p['CYLINDER_NAME']})
  Inner radius:       {p['R_INNER']:>8.4f} cm
  Wall thickness:     {p['WALL_THICKNESS']:>8.4f} cm
  Length:             {p['CYL_LENGTH']:>8.2f} cm

STACKING CONFIGURATION
  Pattern:            {p['STACKING_PATTERN']} (bottom to top)
  Total cylinders:    {p['TOTAL_CYLINDERS']}
  Gap Y (same layer): {p['GAP_Y']:>8.2f} cm
  Gap Z (layers):     {p['GAP_Z']:>8.2f} cm

FLOOR
  Material:           {p['FLOOR_MATERIAL']}
  Thickness:          {p['FLOOR_THICKNESS']:>8.2f} cm

ENVIRONMENT
  Material:           {p['ENVIRONMENT']}
  Boundary:           {p['BOUNDARY']:>8.2f} cm

SIMULATION
  {int(p['PARTICLES'])} particles x {int(p['BATCHES'])} batches ({int(p['INACTIVE'])} inactive)
================================================================================
""")
