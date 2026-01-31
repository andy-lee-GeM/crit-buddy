#!/usr/bin/env python3
"""
================================================================================
CYLINDER ARRAY CRITICALITY MODEL - OpenMC
================================================================================
Template:   cylinder_array
Problem:    Array of vertical cylinders filled with UF6
Geometry:   Multiple cylinders in rectangular array with environment
================================================================================
"""

import openmc
from critbuddy.core.materials import create_uf6, get_material


def build_model(p):
    """
    Build OpenMC model for cylinder array.

    Creates a rectangular array of cylinders, each with UF6 core and wall,
    surrounded by an environment (air or water).
    """

    # ══════════════════════════════════════════════════════════════════════════
    # MATERIALS
    # ══════════════════════════════════════════════════════════════════════════

    m_uf6 = create_uf6(p["ENRICHMENT"], p["UF6_DENSITY"])
    m_wall = get_material(p["WALL_MATERIAL"], solver="openmc")
    m_env = get_material(p["ENVIRONMENT"], solver="openmc")

    materials = openmc.Materials([m_uf6, m_wall, m_env])

    # ══════════════════════════════════════════════════════════════════════════
    # GEOMETRY - Create unit cell and replicate
    # ══════════════════════════════════════════════════════════════════════════

    rows = p["ROWS"]
    cols = p["COLS"]
    pitch = p["PITCH"]
    inner_r = p["INNER_RADIUS"]
    outer_r = p["OUTER_RADIUS"]
    height = p["HEIGHT"]
    boundary = p["BOUNDARY"]

    cells = []
    cell_id = 1

    # Z planes for cylinder bounds (UF6 region)
    z_bottom = openmc.ZPlane(z0=p["Z_BOTTOM"], name="z_bottom")
    z_top = openmc.ZPlane(z0=p["Z_TOP"], name="z_top")
    # Z planes for caps (wall material extends above/below UF6)
    z_cap_bottom = openmc.ZPlane(z0=p["Z_CAP_BOTTOM"], name="z_cap_bottom")
    z_cap_top = openmc.ZPlane(z0=p["Z_CAP_TOP"], name="z_cap_top")

    # Bounding box surfaces
    x_min = openmc.XPlane(x0=-p["TOTAL_X"]/2, boundary_type="vacuum", name="x_min")
    x_max = openmc.XPlane(x0=p["TOTAL_X"]/2, boundary_type="vacuum", name="x_max")
    y_min = openmc.YPlane(y0=-p["TOTAL_Y"]/2, boundary_type="vacuum", name="y_min")
    y_max = openmc.YPlane(y0=p["TOTAL_Y"]/2, boundary_type="vacuum", name="y_max")
    z_min = openmc.ZPlane(z0=p["Z_ENV_BOTTOM"], boundary_type="vacuum", name="z_min")
    z_max = openmc.ZPlane(z0=p["Z_ENV_TOP"], boundary_type="vacuum", name="z_max")

    # Create cylinders at each grid position
    cylinder_regions = []  # Track all cylinder regions for environment cell

    for row in range(rows):
        for col in range(cols):
            # Calculate center position
            x_center = p["X_OFFSET"] + col * pitch
            y_center = p["Y_OFFSET"] + row * pitch

            # Create cylinder surfaces at this position
            inner_cyl = openmc.ZCylinder(x0=x_center, y0=y_center, r=inner_r,
                                         name=f"inner_{row}_{col}")
            outer_cyl = openmc.ZCylinder(x0=x_center, y0=y_center, r=outer_r,
                                         name=f"outer_{row}_{col}")

            # UF6 core cell
            c_uf6 = openmc.Cell(cell_id=cell_id, name=f"UF6_{row}_{col}", fill=m_uf6)
            c_uf6.region = -inner_cyl & +z_bottom & -z_top
            cells.append(c_uf6)
            cell_id += 1

            # Wall cell (cylindrical shell)
            c_wall = openmc.Cell(cell_id=cell_id, name=f"Wall_{row}_{col}", fill=m_wall)
            c_wall.region = +inner_cyl & -outer_cyl & +z_bottom & -z_top
            cells.append(c_wall)
            cell_id += 1

            # Bottom cap (disk of wall material below UF6)
            c_cap_bottom = openmc.Cell(cell_id=cell_id, name=f"CapBottom_{row}_{col}", fill=m_wall)
            c_cap_bottom.region = -outer_cyl & +z_cap_bottom & -z_bottom
            cells.append(c_cap_bottom)
            cell_id += 1

            # Top cap (disk of wall material above UF6)
            c_cap_top = openmc.Cell(cell_id=cell_id, name=f"CapTop_{row}_{col}", fill=m_wall)
            c_cap_top.region = -outer_cyl & +z_top & -z_cap_top
            cells.append(c_cap_top)
            cell_id += 1

            # Track full cylinder region (including caps) for environment exclusion
            cylinder_regions.append(-outer_cyl & +z_cap_bottom & -z_cap_top)

    # Environment cell (everything outside cylinders, inside bounding box)
    # We need to exclude all cylinder regions from the environment
    env_region = +x_min & -x_max & +y_min & -y_max & +z_min & -z_max

    # Exclude all cylinder regions from environment
    for cyl_region in cylinder_regions:
        env_region = env_region & ~cyl_region

    c_env = openmc.Cell(cell_id=cell_id, name="Environment", fill=m_env)
    c_env.region = env_region
    cells.append(c_env)

    # ══════════════════════════════════════════════════════════════════════════
    # GEOMETRY
    # ══════════════════════════════════════════════════════════════════════════

    universe = openmc.Universe(cells=cells)
    geometry = openmc.Geometry(universe)

    # Return dimensions for plotting
    dims = {
        "rows": rows,
        "cols": cols,
        "pitch": pitch,  # Center-to-center (internal use)
        "gap": p["GAP"],  # Gap between outer walls (user-facing)
        "inner_r": inner_r,
        "outer_r": outer_r,
        "height": height,
        "total_x": p["TOTAL_X"],
        "total_y": p["TOTAL_Y"],
        "boundary": boundary,
        "x_offset": p["X_OFFSET"],
        "y_offset": p["Y_OFFSET"],
    }

    return materials, geometry, dims


def create_settings(p, dims):
    """Create OpenMC settings with source in each cylinder."""
    settings = openmc.Settings()
    settings.run_mode = "eigenvalue"
    settings.particles = int(p["PARTICLES"])
    settings.batches = int(p["BATCHES"])
    settings.inactive = int(p["INACTIVE"])

    # Create source points in each cylinder
    source_points = []
    for row in range(dims["rows"]):
        for col in range(dims["cols"]):
            x = p["X_OFFSET"] + col * dims["pitch"]
            y = p["Y_OFFSET"] + row * dims["pitch"]
            z = p["KSRC_Z"]
            source_points.append((x, y, z))

    # Use box source encompassing all cylinders
    # (simpler and more robust than individual point sources)
    x_min = p["X_OFFSET"] - dims["inner_r"] * 0.5
    x_max = p["X_OFFSET"] + (dims["cols"] - 1) * dims["pitch"] + dims["inner_r"] * 0.5
    y_min = p["Y_OFFSET"] - dims["inner_r"] * 0.5
    y_max = p["Y_OFFSET"] + (dims["rows"] - 1) * dims["pitch"] + dims["inner_r"] * 0.5
    z_center = p["KSRC_Z"]

    settings.source = openmc.IndependentSource(
        space=openmc.stats.Box(
            lower_left=(x_min, y_min, z_center - 1),
            upper_right=(x_max, y_max, z_center + 1),
        )
    )

    return settings


def create_plots(dims, materials):
    """
    Create visualization plots for the array.

    Returns:
        plots: openmc.Plots object
        color_legend: dict mapping material name -> RGB tuple
    """
    from critbuddy.core.materials import get_color_mapping

    color_mapping = get_color_mapping(materials)

    plots = openmc.Plots()

    # Calculate plot dimensions
    total_x = dims["total_x"]
    total_y = dims["total_y"]
    height = dims["height"]
    boundary = dims["boundary"]
    y_offset = dims["y_offset"]
    pitch = dims["pitch"]
    rows = dims["rows"]

    # XY slice (top-down view at mid-height)
    p1 = openmc.Plot(name="xy")
    p1.basis = "xy"
    p1.origin = (0, 0, height / 2)
    p1.width = (total_x * 1.1, total_y * 1.1)
    p1.pixels = (800, 800)
    p1.color_by = "material"
    p1.colors = color_mapping
    plots.append(p1)

    # XZ slice (side view through first row of cylinders)
    # Position y at the first row to slice through cylinders, not air
    first_row_y = y_offset  # y-coordinate of first row of cylinders
    p2 = openmc.Plot(name="xz")
    p2.basis = "xz"
    p2.origin = (0, first_row_y, height / 2)
    p2.width = (total_x * 1.1, (height + 2 * boundary) * 1.1)
    p2.pixels = (800, 600)
    p2.color_by = "material"
    p2.colors = color_mapping
    plots.append(p2)

    from critbuddy.core.materials import get_color_legend
    return plots, get_color_legend(materials)


def print_summary(p, dims):
    """Print case summary."""
    n_cylinders = dims["rows"] * dims["cols"]
    print(f"""
================================================================================
                         CYLINDER ARRAY SUMMARY
================================================================================
ARRAY CONFIGURATION
  Layout:             {dims['rows']} rows x {dims['cols']} cols = {n_cylinders} cylinders
  Gap:                {dims['gap']:>8.2f} cm (between outer walls)
  Pitch:              {dims['pitch']:>8.2f} cm (center-to-center)

CYLINDER GEOMETRY (sealed with caps)
  Inner radius:       {dims['inner_r']:>8.2f} cm
  Outer radius:       {dims['outer_r']:>8.2f} cm
  Wall thickness:     {p['WALL_THICKNESS']:>8.2f} cm
  Height (UF6):       {dims['height']:>8.2f} cm
  Total height:       {dims['height'] + 2*p['WALL_THICKNESS']:>8.2f} cm (with caps)

FISSILE MATERIAL
  Enrichment:         {p['ENRICHMENT']:>8.2f} wt% U-235
  Density:            {p['UF6_DENSITY']:>8.3f} g/cc

ENVIRONMENT
  Material:           {p['ENVIRONMENT']}
  Boundary:           {dims['boundary']:>8.2f} cm

TOTAL DIMENSIONS
  X:                  {dims['total_x']:>8.2f} cm
  Y:                  {dims['total_y']:>8.2f} cm

SIMULATION
  {int(p['PARTICLES'])} particles x {int(p['BATCHES'])} batches ({int(p['INACTIVE'])} inactive)
================================================================================
""")
