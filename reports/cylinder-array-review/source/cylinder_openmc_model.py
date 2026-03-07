#!/usr/bin/env python3
"""
================================================================================
3D CYLINDER ARRAY CRITICALITY MODEL - OpenMC
================================================================================
Template:   cylinder_array_3d
Problem:    3D array of vertical cylinders filled with UF6
Geometry:   Cylinders arranged in rows × cols × layers grid
Applications: Stacked storage configurations, warehouse layouts
================================================================================
"""

import openmc
from critbuddy.core.materials import (
    create_uf6, create_uo2f2, get_material, get_density
)


def build_model(p):
    """
    Build OpenMC model for 3D cylinder array.

    Creates a 3D grid of cylinders, each with UF6 core, wall, and end caps,
    surrounded by water at specified density.

    Coordinate system:
        - X: row direction
        - Y: column direction
        - Z: layer direction (vertical stacking)
        - Origin at center of array
    """

    # ══════════════════════════════════════════════════════════════════════════
    # MATERIALS
    # ══════════════════════════════════════════════════════════════════════════

    # Fissile material (UF6 or UO2F2)
    fissile_material = p["FISSILE_MATERIAL"]
    fissile_density = p["FISSILE_DENSITY"]
    h_to_u = p.get("H_TO_U", 0.0)

    if fissile_material == "uo2f2":
        # UO2F2: use H/U ratio for wet modeling (density auto-calculated)
        m_fissile = create_uo2f2(p["ENRICHMENT"], h_to_u=h_to_u)
    else:
        # UF6: use specified density
        m_fissile = create_uf6(p["ENRICHMENT"], density=fissile_density)

    # Wall material
    m_wall = get_material(p["WALL_MATERIAL"], solver="openmc")

    # Environment material (between units and surrounding array)
    env_material = p["ENVIRONMENT"]
    m_env = get_material(env_material, solver="openmc")

    # Void material for unfilled portion of cylinder (if fill_fraction < 1.0)
    fill_fraction = p["FILL_FRACTION"]
    m_void = None
    if fill_fraction < 1.0:
        m_void = get_material(p["VOID_MATERIAL"], solver="openmc")
        materials = openmc.Materials([m_fissile, m_wall, m_env, m_void])
    else:
        materials = openmc.Materials([m_fissile, m_wall, m_env])

    # ══════════════════════════════════════════════════════════════════════════
    # GEOMETRY
    # ══════════════════════════════════════════════════════════════════════════

    rows = p["ROWS"]
    cols = p["COLS"]
    layers = p["LAYERS"]
    gap_xy = p["GAP_XY"]
    gap_z = p["GAP_Z"]
    spacing_xy = p["SPACING_XY"]  # center-to-center
    spacing_z = p["SPACING_Z"]    # center-to-center
    inner_r = p["INNER_RADIUS"]
    outer_r = p["OUTER_RADIUS"]
    height = p["HEIGHT"]
    uf6_height = p["FISSILE_HEIGHT"]  # Fissile fill height (may be < height)
    fill_fraction = p.get("FILL_FRACTION", 1.0)
    wall_t = p["WALL_THICKNESS"]
    total_cyl_h = p["TOTAL_CYL_HEIGHT"]

    cells = []
    cell_id = 1
    cylinder_regions = []  # Track all cylinder regions for water exclusion

    # Create cylinders at each grid position
    for layer in range(layers):
        for row in range(rows):
            for col in range(cols):
                # Calculate center position
                x_center = p["X_OFFSET"] + row * spacing_xy
                y_center = p["Y_OFFSET"] + col * spacing_xy
                z_center = p["Z_OFFSET"] + layer * spacing_z

                # Z bounds for this cylinder
                z_bot_cap = z_center - total_cyl_h / 2
                z_bot_uf6 = z_bot_cap + wall_t
                z_top_uf6 = z_bot_uf6 + height
                z_top_cap = z_top_uf6 + wall_t

                # Create cylinder surfaces at this position
                inner_cyl = openmc.ZCylinder(x0=x_center, y0=y_center, r=inner_r,
                                             name=f"inner_{layer}_{row}_{col}")
                outer_cyl = openmc.ZCylinder(x0=x_center, y0=y_center, r=outer_r,
                                             name=f"outer_{layer}_{row}_{col}")

                # Z planes for this cylinder
                z_bot_cap_plane = openmc.ZPlane(z0=z_bot_cap, name=f"z_bot_cap_{layer}_{row}_{col}")
                z_bot_uf6_plane = openmc.ZPlane(z0=z_bot_uf6, name=f"z_bot_uf6_{layer}_{row}_{col}")
                z_top_uf6_plane = openmc.ZPlane(z0=z_top_uf6, name=f"z_top_uf6_{layer}_{row}_{col}")
                z_top_cap_plane = openmc.ZPlane(z0=z_top_cap, name=f"z_top_cap_{layer}_{row}_{col}")

                # Handle partial fill: UF6 at bottom, void above
                if fill_fraction < 1.0:
                    z_uf6_top_actual = z_bot_uf6 + uf6_height
                    z_uf6_top_plane_actual = openmc.ZPlane(z0=z_uf6_top_actual, name=f"z_uf6_top_actual_{layer}_{row}_{col}")

                    # UF6 core cell (partial fill)
                    c_uf6 = openmc.Cell(cell_id=cell_id, name=f"UF6_{layer}_{row}_{col}", fill=m_fissile)
                    c_uf6.region = -inner_cyl & +z_bot_uf6_plane & -z_uf6_top_plane_actual
                    cells.append(c_uf6)
                    cell_id += 1

                    # Void cell above UF6
                    c_void = openmc.Cell(cell_id=cell_id, name=f"Void_{layer}_{row}_{col}", fill=m_void)
                    c_void.region = -inner_cyl & +z_uf6_top_plane_actual & -z_top_uf6_plane
                    cells.append(c_void)
                    cell_id += 1
                else:
                    # UF6 core cell (full fill)
                    c_uf6 = openmc.Cell(cell_id=cell_id, name=f"UF6_{layer}_{row}_{col}", fill=m_fissile)
                    c_uf6.region = -inner_cyl & +z_bot_uf6_plane & -z_top_uf6_plane
                    cells.append(c_uf6)
                    cell_id += 1

                # Wall cell (cylindrical shell)
                c_wall = openmc.Cell(cell_id=cell_id, name=f"Wall_{layer}_{row}_{col}", fill=m_wall)
                c_wall.region = +inner_cyl & -outer_cyl & +z_bot_uf6_plane & -z_top_uf6_plane
                cells.append(c_wall)
                cell_id += 1

                # Bottom cap
                c_cap_bot = openmc.Cell(cell_id=cell_id, name=f"CapBot_{layer}_{row}_{col}", fill=m_wall)
                c_cap_bot.region = -outer_cyl & +z_bot_cap_plane & -z_bot_uf6_plane
                cells.append(c_cap_bot)
                cell_id += 1

                # Top cap
                c_cap_top = openmc.Cell(cell_id=cell_id, name=f"CapTop_{layer}_{row}_{col}", fill=m_wall)
                c_cap_top.region = -outer_cyl & +z_top_uf6_plane & -z_top_cap_plane
                cells.append(c_cap_top)
                cell_id += 1

                # Track full cylinder region for water exclusion
                cylinder_regions.append(-outer_cyl & +z_bot_cap_plane & -z_top_cap_plane)

    # Bounding box surfaces
    boundary_type = p.get("BOUNDARY_TYPE", "vacuum")
    x_min = openmc.XPlane(x0=-p["TOTAL_X"]/2, boundary_type=boundary_type, name="x_min")
    x_max = openmc.XPlane(x0=p["TOTAL_X"]/2, boundary_type=boundary_type, name="x_max")
    y_min = openmc.YPlane(y0=-p["TOTAL_Y"]/2, boundary_type=boundary_type, name="y_min")
    y_max = openmc.YPlane(y0=p["TOTAL_Y"]/2, boundary_type=boundary_type, name="y_max")
    z_min = openmc.ZPlane(z0=-p["TOTAL_Z"]/2, boundary_type=boundary_type, name="z_min")
    z_max = openmc.ZPlane(z0=p["TOTAL_Z"]/2, boundary_type=boundary_type, name="z_max")

    # Water cell (everything outside cylinders, inside bounding box)
    water_region = +x_min & -x_max & +y_min & -y_max & +z_min & -z_max

    # Exclude all cylinder regions from water
    for cyl_region in cylinder_regions:
        water_region = water_region & ~cyl_region

    c_env = openmc.Cell(cell_id=cell_id, name="Environment", fill=m_env)
    c_env.region = water_region
    cells.append(c_env)

    # ══════════════════════════════════════════════════════════════════════════
    # GEOMETRY ASSEMBLY
    # ══════════════════════════════════════════════════════════════════════════

    universe = openmc.Universe(cells=cells)
    geometry = openmc.Geometry(universe)

    # Return dimensions for plotting
    # Get actual density from material (may be auto-calculated from H/U)
    actual_fissile_density = m_fissile.density

    dims = {
        "rows": rows,
        "cols": cols,
        "layers": layers,
        "total_cylinders": p["TOTAL_CYLINDERS"],
        "spacing_xy": spacing_xy,
        "spacing_z": spacing_z,
        "gap_xy": p["GAP_XY"],
        "gap_z": p["GAP_Z"],
        "inner_r": inner_r,
        "outer_r": outer_r,
        "height": height,
        "fissile_height": uf6_height,
        "fill_fraction": fill_fraction,
        "total_cyl_height": total_cyl_h,
        "total_x": p["TOTAL_X"],
        "total_y": p["TOTAL_Y"],
        "total_z": p["TOTAL_Z"],
        "reflector_thickness": p["REFLECTOR_THICKNESS"],
        "fissile_material": fissile_material,
        "fissile_density": actual_fissile_density,
        "h_to_u": h_to_u,
        "environment": env_material,
        "x_offset": p["X_OFFSET"],
        "y_offset": p["Y_OFFSET"],
        "z_offset": p["Z_OFFSET"],
        "boundary_type": boundary_type,
    }

    return materials, geometry, dims


def create_settings(p, dims):
    """Create OpenMC settings with distributed source."""
    settings = openmc.Settings()
    settings.run_mode = "eigenvalue"
    settings.particles = int(p["PARTICLES"])
    settings.batches = int(p["BATCHES"])
    settings.inactive = int(p["INACTIVE"])

    # Box source encompassing all cylinders
    x_min = dims["x_offset"] - dims["inner_r"] * 0.5
    x_max = dims["x_offset"] + (dims["rows"] - 1) * dims["spacing_xy"] + dims["inner_r"] * 0.5
    y_min = dims["y_offset"] - dims["inner_r"] * 0.5
    y_max = dims["y_offset"] + (dims["cols"] - 1) * dims["spacing_xy"] + dims["inner_r"] * 0.5
    z_min = dims["z_offset"] - dims["height"] * 0.25
    z_max = dims["z_offset"] + (dims["layers"] - 1) * dims["spacing_z"] + dims["height"] * 0.25

    settings.source = openmc.IndependentSource(
        space=openmc.stats.Box(
            lower_left=(x_min, y_min, z_min),
            upper_right=(x_max, y_max, z_max),
        )
    )

    return settings


def create_plots(dims, materials):
    """Create visualization plots for the 3D array."""
    from critbuddy.core.materials import get_color_mapping, get_color_legend

    color_mapping = get_color_mapping(materials)

    plots = openmc.Plots()

    total_x = dims["total_x"]
    total_y = dims["total_y"]
    total_z = dims["total_z"]

    # Calculate z-position to slice through fissile material (not headspace)
    # For partial fill, fissile material is at bottom of cylinder
    # z_offset is center of first layer cylinder
    # fissile region bottom = z_offset - total_cyl_height/2 + wall_thickness (approx)
    # slice through middle of fissile region
    wall_t = dims["outer_r"] - dims["inner_r"]  # wall thickness
    z_cyl_bottom = dims["z_offset"] - dims["total_cyl_height"] / 2 + wall_t
    z_fissile_center = z_cyl_bottom + dims["fissile_height"] / 2

    # XY slice (top-down view through fissile material in first layer)
    p1 = openmc.Plot(name="xy")
    p1.basis = "xy"
    p1.origin = (0, 0, z_fissile_center)  # Slice through fissile region, not headspace
    p1.width = (total_x * 1.1, total_y * 1.1)
    p1.pixels = (800, 800)
    p1.color_by = "material"
    p1.colors = color_mapping
    plots.append(p1)

    # XZ slice (side view through first column)
    p2 = openmc.Plot(name="xz")
    p2.basis = "xz"
    p2.origin = (0, dims["y_offset"], 0)  # Slice through first column, not y=0
    p2.width = (total_x * 1.1, total_z * 1.1)
    p2.pixels = (800, 600)
    p2.color_by = "material"
    p2.colors = color_mapping
    plots.append(p2)

    # YZ slice (end view through first row)
    p3 = openmc.Plot(name="yz")
    p3.basis = "yz"
    p3.origin = (dims["x_offset"], 0, 0)  # Slice through first row, not x=0
    p3.width = (total_y * 1.1, total_z * 1.1)
    p3.pixels = (800, 600)
    p3.color_by = "material"
    p3.colors = color_mapping
    plots.append(p3)

    return plots, get_color_legend(materials)


def print_summary(p, dims):
    """Print case summary."""
    print(f"""
================================================================================
                      3D CYLINDER ARRAY SUMMARY
================================================================================
ARRAY CONFIGURATION
  Layout:             {dims['rows']} rows x {dims['cols']} cols x {dims['layers']} layers
  Total cylinders:    {dims['total_cylinders']}
  Gap (horizontal):   {dims['gap_xy']:>8.2f} cm
  Gap (vertical):     {dims['gap_z']:>8.2f} cm
  Spacing (XY):       {dims['spacing_xy']:>8.2f} cm  (center-to-center)
  Spacing (Z):        {dims['spacing_z']:>8.2f} cm  (center-to-center)

CYLINDER GEOMETRY
  Inner radius:       {dims['inner_r']:>8.2f} cm
  Outer radius:       {dims['outer_r']:>8.2f} cm
  Wall thickness:     {p['WALL_THICKNESS']:>8.2f} cm
  Height (interior):  {dims['height']:>8.2f} cm
  Total height:       {dims['total_cyl_height']:>8.2f} cm (with caps)

FISSILE MATERIAL
  Material:           {dims.get('fissile_material', 'uf6').upper()}
  H/U ratio:          {dims.get('h_to_u', 0.0):>8.1f}
  Enrichment:         {p['ENRICHMENT']:>8.2f} wt% U-235
  Density:            {dims.get('fissile_density', 5.09):>8.3f} g/cc
  Fill fraction:      {dims.get('fill_fraction', 1.0):>8.1%}
  Fissile height:     {dims.get('fissile_height', dims['height']):>8.2f} cm

ENVIRONMENT
  Material:           {dims.get('environment', 'humid_air')}
  Thickness:          {dims['reflector_thickness']:>8.2f} cm
  Boundary:           {dims.get('boundary_type', 'vacuum')}

TOTAL DIMENSIONS
  X:                  {dims['total_x']:>8.2f} cm
  Y:                  {dims['total_y']:>8.2f} cm
  Z:                  {dims['total_z']:>8.2f} cm

SIMULATION
  {int(p['PARTICLES'])} particles x {int(p['BATCHES'])} batches ({int(p['INACTIVE'])} inactive)
================================================================================
""")
