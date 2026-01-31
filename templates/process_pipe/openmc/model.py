#!/usr/bin/env python3
"""
================================================================================
PROCESS PIPE CRITICALITY MODEL - OpenMC
================================================================================
Template:   process_pipe
Problem:    Single horizontal pipe filled with UF6
Geometry:   Horizontal cylinder with wall and reflector
Applications: Process piping, cascade lines, pigtails
================================================================================
"""

import openmc
from critbuddy.core.materials import create_uf6, get_material


def build_model(p):
    """
    Build OpenMC model for a horizontal pipe.

    Coordinate system:
    - X: pipe length direction (horizontal)
    - Y: horizontal perpendicular
    - Z: vertical
    - Origin at center of pipe
    """

    # ══════════════════════════════════════════════════════════════════════════
    # MATERIALS
    # ══════════════════════════════════════════════════════════════════════════

    m_uf6 = create_uf6(p["ENRICHMENT"], p["UF6_DENSITY"])
    m_wall = get_material(p["WALL_MATERIAL"], solver="openmc")

    refl_mat = p.get("REFLECTOR_MATERIAL", "water")
    if refl_mat != "none":
        m_refl = get_material(refl_mat, solver="openmc")
        materials = openmc.Materials([m_uf6, m_wall, m_refl])
    else:
        m_refl = None
        materials = openmc.Materials([m_uf6, m_wall])

    # ══════════════════════════════════════════════════════════════════════════
    # SURFACES
    # ══════════════════════════════════════════════════════════════════════════

    # Cylindrical surfaces (pipe along X-axis)
    cyl_inner = openmc.XCylinder(r=p["R_INNER"], name="cyl_inner")
    cyl_outer = openmc.XCylinder(r=p["R_OUTER"], name="cyl_outer")

    # X planes (pipe ends)
    x_neg = openmc.XPlane(x0=-p["X_INNER"], name="x_neg")
    x_pos = openmc.XPlane(x0=p["X_INNER"], name="x_pos")

    # Outer boundaries
    if refl_mat == "none":
        cyl_bound = openmc.XCylinder(r=p["R_OUTER"], name="cyl_bound", boundary_type="vacuum")
        x_neg_bound = openmc.XPlane(x0=-p["X_INNER"], name="x_neg_bound", boundary_type="vacuum")
        x_pos_bound = openmc.XPlane(x0=p["X_INNER"], name="x_pos_bound", boundary_type="vacuum")
    else:
        cyl_refl = openmc.XCylinder(r=p["R_REFL"], name="cyl_refl", boundary_type="vacuum")
        x_neg_refl = openmc.XPlane(x0=-p["X_REFL"], name="x_neg_refl", boundary_type="vacuum")
        x_pos_refl = openmc.XPlane(x0=p["X_REFL"], name="x_pos_refl", boundary_type="vacuum")

    # ══════════════════════════════════════════════════════════════════════════
    # CELLS
    # ══════════════════════════════════════════════════════════════════════════

    cells = []

    # Cell 1: UF6 (fissile material inside pipe)
    c_uf6 = openmc.Cell(cell_id=1, name="UF6", fill=m_uf6)
    c_uf6.region = -cyl_inner & +x_neg & -x_pos
    cells.append(c_uf6)

    # Cell 2: Wall (pipe wall - radial only)
    c_wall = openmc.Cell(cell_id=2, name="Wall", fill=m_wall)
    c_wall.region = +cyl_inner & -cyl_outer & +x_neg & -x_pos
    cells.append(c_wall)

    # Reflector cells (if present)
    if refl_mat != "none":
        # Cell 3: Reflector (radial - around pipe)
        c_refl_radial = openmc.Cell(cell_id=3, name="Refl_radial", fill=m_refl)
        c_refl_radial.region = +cyl_outer & -cyl_refl & +x_neg & -x_pos
        cells.append(c_refl_radial)

        # Cell 4: Reflector (left end cap)
        c_refl_left = openmc.Cell(cell_id=4, name="Refl_left", fill=m_refl)
        c_refl_left.region = -cyl_refl & +x_neg_refl & -x_neg
        cells.append(c_refl_left)

        # Cell 5: Reflector (right end cap)
        c_refl_right = openmc.Cell(cell_id=5, name="Refl_right", fill=m_refl)
        c_refl_right.region = -cyl_refl & +x_pos & -x_pos_refl
        cells.append(c_refl_right)

    # ══════════════════════════════════════════════════════════════════════════
    # GEOMETRY
    # ══════════════════════════════════════════════════════════════════════════

    universe = openmc.Universe(cells=cells)
    geometry = openmc.Geometry(universe)

    # Dimensions for plotting
    dims = {
        "r_inner": p["R_INNER"],
        "r_outer": p["R_OUTER"],
        "r_refl": p["R_REFL"],
        "length": p["LENGTH"],
        "total_x": p["TOTAL_X"],
        "total_yz": p["TOTAL_YZ"],
        "refl_thickness": p["REFL_THICKNESS"],
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
    total_yz = dims["total_yz"]

    color_mapping = get_color_mapping(materials)
    plots = openmc.Plots()

    # XY slice (top-down view - shows pipe length)
    p1 = openmc.Plot(name="xy")
    p1.basis = "xy"
    p1.origin = (0, 0, 0)
    p1.width = (total_x * 1.1, total_yz * 1.1)
    p1.pixels = (800, 400)
    p1.color_by = "material"
    p1.colors = color_mapping
    plots.append(p1)

    # YZ slice (end view - shows circular cross-section)
    p2 = openmc.Plot(name="xz")
    p2.basis = "yz"
    p2.origin = (0, 0, 0)
    p2.width = (total_yz * 1.1, total_yz * 1.1)
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

GEOMETRY (cm)
  Pipe size:          NPS {p['PIPE_SIZE']}
  Inner radius:       {dims['r_inner']:>8.4f}
  Wall thickness:     {p['WALL_THICKNESS']:>8.4f}
  Outer radius:       {dims['r_outer']:>8.4f}
  Length:             {dims['length']:>8.2f}

MATERIALS
  Wall:               {p['WALL_MATERIAL']}
  Reflector:          {p['REFLECTOR_MATERIAL']} ({p['REFL_THICKNESS']} cm)

SIMULATION
  {int(p['PARTICLES'])} particles x {int(p['BATCHES'])} batches ({int(p['INACTIVE'])} inactive)
================================================================================
""")
