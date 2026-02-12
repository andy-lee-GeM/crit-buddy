#!/usr/bin/env python3
"""
================================================================================
SHIPPING CYLINDER ARRAY CRITICALITY MODEL - OpenMC
================================================================================
Template:   shipping_cylinder_array
Problem:    3D array of UF6 shipping cylinders with floor modeling
Geometry:   rows × cols × layers array with configurable gaps and floor
================================================================================
"""

import openmc
from critbuddy.core.materials import create_uf6, get_material


def build_model(p):
    """
    Build OpenMC model for 3D cylinder array.

    Creates a 3D array of shipping cylinders (rows × cols × layers),
    each with UF6 core and wall, sitting on a floor/pad and surrounded
    by environment (air or water).

    Coordinate system:
    - Origin at center of array (XY) and floor surface (Z=0)
    - Cylinders sit on floor, stacking upward in Z
    """

    # ══════════════════════════════════════════════════════════════════════════
    # MATERIALS
    # ══════════════════════════════════════════════════════════════════════════

    materials_list = []

    m_uf6 = create_uf6(p["ENRICHMENT"], density=p["UF6_DENSITY"])
    materials_list.append(m_uf6)

    m_wall = get_material(p["WALL_MATERIAL"], solver="openmc")
    materials_list.append(m_wall)

    m_env = get_material(p["ENVIRONMENT"], solver="openmc")
    materials_list.append(m_env)

    m_floor = None
    if p["FLOOR_MATERIAL"] != "none" and p["FLOOR_THICKNESS"] > 0:
        m_floor = get_material(p["FLOOR_MATERIAL"], solver="openmc")
        materials_list.append(m_floor)

    materials = openmc.Materials(materials_list)

    # ══════════════════════════════════════════════════════════════════════════
    # GEOMETRY
    # ══════════════════════════════════════════════════════════════════════════

    rows = p["ROWS"]
    cols = p["COLS"]
    layers = p["LAYERS"]
    pitch_x = p["PITCH_X"]
    pitch_y = p["PITCH_Y"]
    pitch_z = p["PITCH_Z"]
    r_inner = p["R_INNER"]
    r_outer = p["R_OUTER"]
    cyl_total_height = p["CYL_TOTAL_HEIGHT"]
    cyl_internal_height = p["CYL_INTERNAL_HEIGHT"]
    wall_t = p["WALL_THICKNESS"]
    x_offset = p["X_OFFSET"]
    y_offset = p["Y_OFFSET"]

    cells = []
    cell_id = 1

    # Bounding box surfaces
    x_min = openmc.XPlane(x0=-p["TOTAL_X"]/2, boundary_type="vacuum", name="x_min")
    x_max = openmc.XPlane(x0=p["TOTAL_X"]/2, boundary_type="vacuum", name="x_max")
    y_min = openmc.YPlane(y0=-p["TOTAL_Y"]/2, boundary_type="vacuum", name="y_min")
    y_max = openmc.YPlane(y0=p["TOTAL_Y"]/2, boundary_type="vacuum", name="y_max")
    z_min = openmc.ZPlane(z0=p["Z_FLOOR_BOTTOM"], boundary_type="vacuum", name="z_min")
    z_max = openmc.ZPlane(z0=p["Z_ENV_TOP"], boundary_type="vacuum", name="z_max")

    # Floor surface (top of floor / bottom of array)
    z_floor_top = openmc.ZPlane(z0=p["Z_FLOOR_TOP"], name="z_floor_top")

    # Track all cylinder regions for environment cell exclusion
    cylinder_regions = []

    # Create cylinders at each grid position
    for layer in range(layers):
        # Z position for this layer (bottom of cylinder)
        z_cyl_bottom = layer * pitch_z

        # Z planes for this layer
        z_bot = openmc.ZPlane(z0=z_cyl_bottom, name=f"z_bot_L{layer}")
        z_uf6_bot = openmc.ZPlane(z0=z_cyl_bottom + wall_t, name=f"z_uf6_bot_L{layer}")
        z_uf6_top = openmc.ZPlane(z0=z_cyl_bottom + wall_t + cyl_internal_height, name=f"z_uf6_top_L{layer}")
        z_top = openmc.ZPlane(z0=z_cyl_bottom + cyl_total_height, name=f"z_top_L{layer}")

        for row in range(rows):
            for col in range(cols):
                # XY position for this cylinder
                x_center = x_offset + col * pitch_x
                y_center = y_offset + row * pitch_y

                # Create cylinder surfaces
                inner_cyl = openmc.ZCylinder(
                    x0=x_center, y0=y_center, r=r_inner,
                    name=f"inner_L{layer}_R{row}_C{col}"
                )
                outer_cyl = openmc.ZCylinder(
                    x0=x_center, y0=y_center, r=r_outer,
                    name=f"outer_L{layer}_R{row}_C{col}"
                )

                # UF6 core
                c_uf6 = openmc.Cell(
                    cell_id=cell_id,
                    name=f"UF6_L{layer}_R{row}_C{col}",
                    fill=m_uf6
                )
                c_uf6.region = -inner_cyl & +z_uf6_bot & -z_uf6_top
                cells.append(c_uf6)
                cell_id += 1

                # Wall (radial)
                c_wall = openmc.Cell(
                    cell_id=cell_id,
                    name=f"Wall_L{layer}_R{row}_C{col}",
                    fill=m_wall
                )
                c_wall.region = +inner_cyl & -outer_cyl & +z_bot & -z_top
                cells.append(c_wall)
                cell_id += 1

                # Bottom cap
                c_cap_bot = openmc.Cell(
                    cell_id=cell_id,
                    name=f"CapBot_L{layer}_R{row}_C{col}",
                    fill=m_wall
                )
                c_cap_bot.region = -inner_cyl & +z_bot & -z_uf6_bot
                cells.append(c_cap_bot)
                cell_id += 1

                # Top cap
                c_cap_top = openmc.Cell(
                    cell_id=cell_id,
                    name=f"CapTop_L{layer}_R{row}_C{col}",
                    fill=m_wall
                )
                c_cap_top.region = -inner_cyl & +z_uf6_top & -z_top
                cells.append(c_cap_top)
                cell_id += 1

                # Track full cylinder region for environment exclusion
                cylinder_regions.append(-outer_cyl & +z_bot & -z_top)

    # Floor cell (if present)
    floor_region = None
    if m_floor is not None:
        c_floor = openmc.Cell(cell_id=cell_id, name="Floor", fill=m_floor)
        floor_region = +x_min & -x_max & +y_min & -y_max & +z_min & -z_floor_top
        c_floor.region = floor_region
        cells.append(c_floor)
        cell_id += 1

    # Environment cell (everything outside cylinders and floor, inside bounding box)
    env_region = +x_min & -x_max & +y_min & -y_max & +z_floor_top & -z_max

    # Exclude all cylinder regions
    for cyl_region in cylinder_regions:
        env_region = env_region & ~cyl_region

    c_env = openmc.Cell(cell_id=cell_id, name="Environment", fill=m_env)
    c_env.region = env_region
    cells.append(c_env)

    # ══════════════════════════════════════════════════════════════════════════
    # ASSEMBLE GEOMETRY
    # ══════════════════════════════════════════════════════════════════════════

    universe = openmc.Universe(cells=cells)
    geometry = openmc.Geometry(universe)

    # Dimensions for plotting
    dims = {
        "rows": rows,
        "cols": cols,
        "layers": layers,
        "pitch_x": pitch_x,
        "pitch_y": pitch_y,
        "pitch_z": pitch_z,
        "gap_x": p["GAP_X"],
        "gap_y": p["GAP_Y"],
        "gap_z": p["GAP_Z"],
        "r_inner": r_inner,
        "r_outer": r_outer,
        "cyl_height": cyl_total_height,
        "array_x": p["ARRAY_X"],
        "array_y": p["ARRAY_Y"],
        "array_z": p["ARRAY_Z"],
        "total_x": p["TOTAL_X"],
        "total_y": p["TOTAL_Y"],
        "total_z": p["TOTAL_Z"],
        "floor_thickness": p["FLOOR_THICKNESS"],
        "boundary": p["BOUNDARY"],
        "x_offset": x_offset,
        "y_offset": y_offset,
    }

    return materials, geometry, dims


def create_settings(p, dims):
    """Create OpenMC settings with source distributed across all cylinders."""
    settings = openmc.Settings()
    settings.run_mode = "eigenvalue"
    settings.particles = int(p["PARTICLES"])
    settings.batches = int(p["BATCHES"])
    settings.inactive = int(p["INACTIVE"])

    # Box source encompassing all UF6 regions
    x_min = dims["x_offset"] - dims["r_inner"] * 0.5
    x_max = dims["x_offset"] + (dims["cols"] - 1) * dims["pitch_x"] + dims["r_inner"] * 0.5
    y_min = dims["y_offset"] - dims["r_inner"] * 0.5
    y_max = dims["y_offset"] + (dims["rows"] - 1) * dims["pitch_y"] + dims["r_inner"] * 0.5
    z_min = p["WALL_THICKNESS"]
    z_max = (dims["layers"] - 1) * dims["pitch_z"] + p["CYL_TOTAL_HEIGHT"] - p["WALL_THICKNESS"]

    settings.source = openmc.IndependentSource(
        space=openmc.stats.Box(
            lower_left=(x_min, y_min, z_min),
            upper_right=(x_max, y_max, z_max),
        )
    )

    return settings


def create_plots(dims, materials):
    """
    Create visualization plots for the 3D array.

    Returns:
        plots: openmc.Plots object
        color_legend: dict mapping material name -> RGB tuple
    """
    from critbuddy.core.materials import get_color_mapping, get_color_legend

    color_mapping = get_color_mapping(materials)
    plots = openmc.Plots()

    total_x = dims["total_x"]
    total_y = dims["total_y"]
    array_z = dims["array_z"]
    floor_t = dims["floor_thickness"]
    boundary = dims["boundary"]
    y_offset = dims["y_offset"]
    cyl_height = dims["cyl_height"]
    layers = dims["layers"]
    pitch_z = dims["pitch_z"]

    # XY slice (top-down view at mid-height of first layer)
    z_mid = cyl_height / 2
    p1 = openmc.Plot(name="xy_layer1")
    p1.basis = "xy"
    p1.origin = (0, 0, z_mid)
    p1.width = (total_x * 1.05, total_y * 1.05)
    p1.pixels = (800, 800)
    p1.color_by = "material"
    p1.colors = color_mapping
    plots.append(p1)

    # XZ slice (side view through first row)
    total_height = array_z + boundary + floor_t
    z_center = (array_z - floor_t) / 2
    p2 = openmc.Plot(name="xz")
    p2.basis = "xz"
    p2.origin = (0, y_offset, z_center)
    p2.width = (total_x * 1.05, total_height * 1.05)
    p2.pixels = (800, 1000)
    p2.color_by = "material"
    p2.colors = color_mapping
    plots.append(p2)

    # YZ slice (side view through first column)
    x_offset = dims["x_offset"]
    p3 = openmc.Plot(name="yz")
    p3.basis = "yz"
    p3.origin = (x_offset, 0, z_center)
    p3.width = (total_y * 1.05, total_height * 1.05)
    p3.pixels = (800, 1000)
    p3.color_by = "material"
    p3.colors = color_mapping
    plots.append(p3)

    return plots, get_color_legend(materials)


def print_summary(p, dims):
    """Print case summary."""
    n_cylinders = dims["rows"] * dims["cols"] * dims["layers"]
    print(f"""
================================================================================
              3D CYLINDER ARRAY - {p['CYLINDER_NAME']}
================================================================================
CYLINDER TYPE
  Type:               {p['CYLINDER_TYPE']}
  Wall material:      {p['WALL_MATERIAL']}

ARRAY CONFIGURATION
  Layout:             {dims['rows']} rows x {dims['cols']} cols x {dims['layers']} layers
  Total cylinders:    {n_cylinders}

SPACING
  Gap X:              {dims['gap_x']:>8.2f} cm (between outer walls)
  Gap Y:              {dims['gap_y']:>8.2f} cm (between outer walls)
  Gap Z:              {dims['gap_z']:>8.2f} cm (between stacked cylinders)

CYLINDER GEOMETRY
  Inner radius:       {dims['r_inner']:>8.4f} cm
  Outer radius:       {dims['r_outer']:>8.4f} cm
  Total height:       {dims['cyl_height']:>8.2f} cm (with caps)
  Wall thickness:     {p['WALL_THICKNESS']:>8.4f} cm

FISSILE MATERIAL
  Enrichment:         {p['ENRICHMENT']:>8.2f} wt% U-235
  Density:            {p['UF6_DENSITY']:>8.3f} g/cc

FLOOR
  Material:           {p['FLOOR_MATERIAL']}
  Thickness:          {dims['floor_thickness']:>8.2f} cm

ENVIRONMENT
  Material:           {p['ENVIRONMENT']}
  Boundary:           {dims['boundary']:>8.2f} cm

TOTAL DIMENSIONS
  X:                  {dims['total_x']:>8.2f} cm
  Y:                  {dims['total_y']:>8.2f} cm
  Z:                  {dims['total_z']:>8.2f} cm (including floor)

SIMULATION
  {int(p['PARTICLES'])} particles x {int(p['BATCHES'])} batches ({int(p['INACTIVE'])} inactive)
================================================================================
""")
