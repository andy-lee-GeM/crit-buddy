#!/usr/bin/env python3
"""
================================================================================
PIPE CRITICALITY MODEL - OpenMC
================================================================================
Template:   pipe
Problem:    Single or arrayed horizontal pipes (rows x cols), filled with UF6/UO2F2
Geometry:   Horizontal cylinders arranged in Y-Z plane
Applications: Process piping, cascade line spacing studies
================================================================================
"""

import openmc
from critbuddy.core.materials import (
    create_fissile_material,
    create_environment_material,
    get_material,
    vacuum,
)


def build_model(p):
    """
    Build OpenMC model for single or arrayed horizontal pipes.

    Coordinate system:
    - X: pipe length direction (horizontal)
    - Y: pipe arrangement direction (side by side)
    - Z: vertical (stacked rows)
    - Origin at center of pipe array
    """

    # ══════════════════════════════════════════════════════════════════════════
    # MATERIALS
    # ══════════════════════════════════════════════════════════════════════════

    # Fissile material (UF6 or UO2F2)
    fissile_type = p.get("FISSILE_MATERIAL", "uf6")
    m_fissile = create_fissile_material(
        fissile_material=fissile_type,
        enrichment_pct=p["ENRICHMENT"],
        fissile_density=p.get("FISSILE_DENSITY"),
        h_to_u=p.get("H_TO_U", 0.0),
    )

    m_wall = get_material(p["WALL_MATERIAL"], solver="openmc")

    # Environment material (humid_air, air, or water)
    env_material = p["ENVIRONMENT_MATERIAL"]
    m_env = create_environment_material(
        environment_material=env_material,
        environment_density=p.get("ENV_DENSITY"),
    )

    # Vacuum space above liquid for unfilled portion of pipe (if fill_fraction < 1.0)
    fill_fraction = p.get("FILL_FRACTION", 1.0)
    fill_height = p.get("FILL_HEIGHT", 0.0)  # Relative to pipe center
    m_vacuum = None
    if fill_fraction < 1.0:
        m_vacuum = vacuum()
        materials = openmc.Materials([m_fissile, m_wall, m_env, m_vacuum])
    else:
        materials = openmc.Materials([m_fissile, m_wall, m_env])

    # ══════════════════════════════════════════════════════════════════════════
    # SURFACES
    # ══════════════════════════════════════════════════════════════════════════

    num_pipes = p["COLS"]
    rows = p.get("ROWS", 1)
    r_inner = p["R_INNER"]
    r_outer = p["R_OUTER"]
    pipe_y_positions = p["PIPE_Y_POSITIONS"]
    pipe_z_positions = p.get("PIPE_Z_POSITIONS", [0.0])

    # X planes (pipe ends - shared by all pipes)
    x_neg = openmc.XPlane(x0=-p["X_INNER"], name="x_neg")
    x_pos = openmc.XPlane(x0=p["X_INNER"], name="x_pos")

    # Create cylindrical surfaces for each pipe in 2D grid (rows x num_pipes)
    cyl_inner = []
    cyl_outer = []
    pipe_positions = []  # Store (y, z) positions for each pipe
    idx = 0
    for z_pos in pipe_z_positions:
        for y_pos in pipe_y_positions:
            cyl_inner.append(openmc.XCylinder(r=r_inner, y0=y_pos, z0=z_pos, name=f"cyl_inner_{idx}"))
            cyl_outer.append(openmc.XCylinder(r=r_outer, y0=y_pos, z0=z_pos, name=f"cyl_outer_{idx}"))
            pipe_positions.append((y_pos, z_pos))
            idx += 1

    # Outer boundary surfaces
    x_neg_bound = openmc.XPlane(x0=-p["X_TOTAL"], name="x_neg_bound", boundary_type="vacuum")
    x_pos_bound = openmc.XPlane(x0=p["X_TOTAL"], name="x_pos_bound", boundary_type="vacuum")
    y_neg_bound = openmc.YPlane(y0=-p["Y_TOTAL"], name="y_neg_bound", boundary_type="vacuum")
    y_pos_bound = openmc.YPlane(y0=p["Y_TOTAL"], name="y_pos_bound", boundary_type="vacuum")
    z_neg_bound = openmc.ZPlane(z0=-p["Z_TOTAL"], name="z_neg_bound", boundary_type="vacuum")
    z_pos_bound = openmc.ZPlane(z0=p["Z_TOTAL"], name="z_pos_bound", boundary_type="vacuum")

    # ══════════════════════════════════════════════════════════════════════════
    # CELLS
    # ══════════════════════════════════════════════════════════════════════════

    cells = []
    cell_id = 1
    total_pipes = len(cyl_inner)

    # Create fissile and wall cells for each pipe in 2D grid
    pipe_regions = []  # Track all pipe regions for water exclusion
    for i in range(total_pipes):
        y_pos, z_pos = pipe_positions[i]

        if fill_fraction < 1.0:
            # Partial fill: create ZPlane at fill level for this pipe
            fill_z = z_pos + fill_height
            z_fill_plane = openmc.ZPlane(z0=fill_z, name=f"fill_plane_{i}")

            # Fissile material cell (below fill level)
            c_fissile = openmc.Cell(cell_id=cell_id, name=f"Fissile_{i}", fill=m_fissile)
            c_fissile.region = -cyl_inner[i] & +x_neg & -x_pos & -z_fill_plane
            cells.append(c_fissile)
            cell_id += 1

            # Vacuum cell (above fill level)
            c_vacuum = openmc.Cell(cell_id=cell_id, name=f"Vacuum_{i}", fill=m_vacuum)
            c_vacuum.region = -cyl_inner[i] & +x_neg & -x_pos & +z_fill_plane
            cells.append(c_vacuum)
            cell_id += 1
        else:
            # Full fill: entire inner cylinder is fissile
            c_fissile = openmc.Cell(cell_id=cell_id, name=f"Fissile_{i}", fill=m_fissile)
            c_fissile.region = -cyl_inner[i] & +x_neg & -x_pos
            cells.append(c_fissile)
            cell_id += 1

        # Wall cell
        c_wall = openmc.Cell(cell_id=cell_id, name=f"Wall_{i}", fill=m_wall)
        c_wall.region = +cyl_inner[i] & -cyl_outer[i] & +x_neg & -x_pos
        cells.append(c_wall)
        cell_id += 1

        # Track pipe region for water exclusion
        pipe_regions.append(-cyl_outer[i] & +x_neg & -x_pos)

    # Water cell (everything outside pipes, inside bounding box)
    water_region = (
        +x_neg_bound & -x_pos_bound &
        +y_neg_bound & -y_pos_bound &
        +z_neg_bound & -z_pos_bound
    )
    # Exclude all pipe regions from water
    for pipe_region in pipe_regions:
        water_region = water_region & ~pipe_region

    c_env = openmc.Cell(cell_id=cell_id, name="Environment", fill=m_env)
    c_env.region = water_region
    cells.append(c_env)

    # ══════════════════════════════════════════════════════════════════════════
    # GEOMETRY
    # ══════════════════════════════════════════════════════════════════════════

    universe = openmc.Universe(cells=cells)
    geometry = openmc.Geometry(universe)

    # Dimensions for plotting
    dims = {
        "cols": num_pipes,
        "rows": rows,
        "total_pipes": total_pipes,
        "r_inner": r_inner,
        "r_outer": r_outer,
        "length": p["LENGTH"],
        "gap": p["GAP"],
        "pitch": p["PITCH"],
        "total_x": p["TOTAL_X"],
        "total_y": p["TOTAL_Y"],
        "total_z": p["TOTAL_Z"],
        "water_thickness": p["REFLECTOR_THICKNESS"],
        "environment": env_material,
        "fissile_material": fissile_type,
        "fissile_density": m_fissile.density,
        "pipe_z_positions": pipe_z_positions,
        "fill_fraction": fill_fraction,
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

    # Get Z position of first row for XY slice (to show pipes)
    slice_z = 0.0
    if "pipe_z_positions" in dims and len(dims["pipe_z_positions"]) > 0:
        slice_z = dims["pipe_z_positions"][0]

    color_mapping = get_color_mapping(materials)
    plots = openmc.Plots()

    # XY slice (top-down view - slice through first row to show pipes)
    p1 = openmc.Plot(name="xy")
    p1.basis = "xy"
    p1.origin = (0, 0, slice_z)
    p1.width = (total_x * 1.1, total_y * 1.1)
    p1.pixels = (800, 600)
    p1.color_by = "material"
    p1.colors = color_mapping
    plots.append(p1)

    # YZ slice (end view - shows circular cross-sections of all pipes)
    p2 = openmc.Plot(name="xz")
    p2.basis = "yz"
    p2.origin = (0, 0, 0)
    p2.width = (total_y * 1.1, total_z * 1.1)
    p2.pixels = (800, 400)
    p2.color_by = "material"
    p2.colors = color_mapping
    plots.append(p2)

    return plots, get_color_legend(materials)


def print_summary(p, dims):
    """Print case summary."""
    fissile_type = dims.get('fissile_material', 'uf6').upper()
    print(f"""
================================================================================
                         CASE SUMMARY
================================================================================
FISSILE MATERIAL
  Type:               {fissile_type}
  Enrichment:         {p['ENRICHMENT']:>8.2f} wt% U-235
  Density:            {dims.get('fissile_density', 0.0):>8.3f} g/cc
  H/U ratio:          {p.get('H_TO_U', 0.0):>8.1f}
  Fill fraction:      {p.get('FILL_FRACTION', 1.0):>8.1%}

GEOMETRY (cm)
  Array:              {dims['cols']} x {dims['rows']} = {dims['total_pipes']} pipes
  Pipe size:          NPS {p['PIPE_SIZE']}
  Inner radius:       {dims['r_inner']:>8.4f}
  Outer radius:       {dims['r_outer']:>8.4f}
  Length:             {dims['length']:>8.2f}
  Gap (edge-to-edge): {dims['gap']:>8.2f}
  Pitch (center-ctr): {dims['pitch']:>8.4f}

ENVIRONMENT
  Material:           {dims.get('environment', 'humid_air')}
  Reflector:          {dims['water_thickness']:>8.2f} cm

SIMULATION
  {int(p['PARTICLES'])} particles x {int(p['BATCHES'])} batches ({int(p['INACTIVE'])} inactive)
================================================================================
""")
