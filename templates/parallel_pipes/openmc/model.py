#!/usr/bin/env python3
"""
================================================================================
PARALLEL PIPES CRITICALITY MODEL - OpenMC
================================================================================
Template:   parallel_pipes
Problem:    1-3 horizontal pipes running side by side, filled with UF6
Geometry:   Horizontal cylinders arranged along Y-axis
Applications: Process piping runs, cascade line spacing studies
================================================================================
"""

import openmc
from critbuddy.core.materials import create_uf6, create_water, get_material


def build_model(p):
    """
    Build OpenMC model for parallel horizontal pipes.

    Coordinate system:
    - X: pipe length direction (horizontal)
    - Y: pipe arrangement direction (side by side)
    - Z: vertical
    - Origin at center of pipe array
    """

    # ══════════════════════════════════════════════════════════════════════════
    # MATERIALS
    # ══════════════════════════════════════════════════════════════════════════

    m_uf6 = create_uf6(p["ENRICHMENT"], density=p["UF6_DENSITY"])
    m_wall = get_material(p["WALL_MATERIAL"], solver="openmc")

    # Water environment (variable density for mist/fog/flooded scenarios)
    water_density = p.get("WATER_DENSITY", 1.0)
    m_water = create_water(density=water_density)

    materials = openmc.Materials([m_uf6, m_wall, m_water])

    # ══════════════════════════════════════════════════════════════════════════
    # SURFACES
    # ══════════════════════════════════════════════════════════════════════════

    num_pipes = p["NUM_PIPES"]
    r_inner = p["R_INNER"]
    r_outer = p["R_OUTER"]
    pipe_y_positions = p["PIPE_Y_POSITIONS"]

    # X planes (pipe ends - shared by all pipes)
    x_neg = openmc.XPlane(x0=-p["X_INNER"], name="x_neg")
    x_pos = openmc.XPlane(x0=p["X_INNER"], name="x_pos")

    # Create cylindrical surfaces for each pipe
    cyl_inner = []
    cyl_outer = []
    for i, y_pos in enumerate(pipe_y_positions):
        cyl_inner.append(openmc.XCylinder(r=r_inner, y0=y_pos, z0=0.0, name=f"cyl_inner_{i}"))
        cyl_outer.append(openmc.XCylinder(r=r_outer, y0=y_pos, z0=0.0, name=f"cyl_outer_{i}"))

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

    # Create UF6 and wall cells for each pipe
    pipe_regions = []  # Track all pipe regions for water exclusion
    for i in range(num_pipes):
        # UF6 cell
        c_uf6 = openmc.Cell(cell_id=cell_id, name=f"UF6_{i}", fill=m_uf6)
        c_uf6.region = -cyl_inner[i] & +x_neg & -x_pos
        cells.append(c_uf6)
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

    c_water = openmc.Cell(cell_id=cell_id, name="Water", fill=m_water)
    c_water.region = water_region
    cells.append(c_water)

    # ══════════════════════════════════════════════════════════════════════════
    # GEOMETRY
    # ══════════════════════════════════════════════════════════════════════════

    universe = openmc.Universe(cells=cells)
    geometry = openmc.Geometry(universe)

    # Dimensions for plotting
    dims = {
        "num_pipes": num_pipes,
        "r_inner": r_inner,
        "r_outer": r_outer,
        "length": p["LENGTH"],
        "gap": p["GAP"],
        "pitch": p["PITCH"],
        "total_x": p["TOTAL_X"],
        "total_y": p["TOTAL_Y"],
        "total_z": p["TOTAL_Z"],
        "water_thickness": p["WATER_THICKNESS"],
        "water_density": water_density,
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

    color_mapping = get_color_mapping(materials)
    plots = openmc.Plots()

    # XY slice (top-down view - shows all pipes and their arrangement)
    p1 = openmc.Plot(name="xy")
    p1.basis = "xy"
    p1.origin = (0, 0, 0)
    p1.width = (total_x * 1.1, total_y * 1.1)
    p1.pixels = (800, 600)
    p1.color_by = "material"
    p1.colors = color_mapping
    plots.append(p1)

    # YZ slice (end view - shows circular cross-sections side by side)
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
    print(f"""
================================================================================
                         CASE SUMMARY
================================================================================
FISSILE MATERIAL
  Enrichment:         {p['ENRICHMENT']:>8.2f} wt% U-235
  Density:            {p['UF6_DENSITY']:>8.3f} g/cc

GEOMETRY (cm)
  Number of pipes:    {dims['num_pipes']}
  Pipe size:          NPS {p['PIPE_SIZE']}
  Inner radius:       {dims['r_inner']:>8.4f}
  Outer radius:       {dims['r_outer']:>8.4f}
  Length:             {dims['length']:>8.2f}
  Gap (edge-to-edge): {dims['gap']:>8.2f}
  Pitch (center-ctr): {dims['pitch']:>8.4f}

WATER
  Density:            {dims['water_density']:>8.3f} g/cc
  Thickness:          {dims['water_thickness']:>8.2f} cm

SIMULATION
  {int(p['PARTICLES'])} particles x {int(p['BATCHES'])} batches ({int(p['INACTIVE'])} inactive)
================================================================================
""")
