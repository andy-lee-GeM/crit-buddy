#!/usr/bin/env python3
"""
================================================================================
RECTANGULAR BOX CRITICALITY MODEL - OpenMC
================================================================================
Template:   rectangular_box
Problem:    Rectangular parallelepiped (RPP) filled with UF6
Geometry:   Box with steel/aluminum wall and water/concrete reflector
Applications: Chemical traps, HEPA filters, rectangular GEVS components
================================================================================
"""

import openmc
from critbuddy.core.materials import create_uf6, get_material


def build_model(p):
    """
    Build OpenMC model from parameters.

    Coordinate system:
    - Origin at center of box (XY) and bottom of internal cavity (Z=0)
    - X: length direction
    - Y: width direction
    - Z: height direction (vertical)

    Layers (inside to outside):
    1. UF6 region (fissile material)
    2. Wall (6 faces - steel or aluminum)
    3. Reflector (optional - water, concrete, or air)
    """

    # ══════════════════════════════════════════════════════════════════════════
    # MATERIALS (from shared library)
    # ══════════════════════════════════════════════════════════════════════════

    m_uf6 = create_uf6(p["ENRICHMENT"], density=p["UF6_DENSITY"])

    # Wall material
    wall_mat = p.get("WALL_MATERIAL", "steel")
    m_wall = get_material(wall_mat, solver="openmc")

    # Reflector material
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

    # X planes (centered at 0)
    x_inner_neg = openmc.XPlane(x0=-p["X_INNER"], name="x_inner_neg")
    x_inner_pos = openmc.XPlane(x0=p["X_INNER"], name="x_inner_pos")
    x_wall_neg = openmc.XPlane(x0=-p["X_WALL"], name="x_wall_neg")
    x_wall_pos = openmc.XPlane(x0=p["X_WALL"], name="x_wall_pos")

    # Y planes (centered at 0)
    y_inner_neg = openmc.YPlane(y0=-p["Y_INNER"], name="y_inner_neg")
    y_inner_pos = openmc.YPlane(y0=p["Y_INNER"], name="y_inner_pos")
    y_wall_neg = openmc.YPlane(y0=-p["Y_WALL"], name="y_wall_neg")
    y_wall_pos = openmc.YPlane(y0=p["Y_WALL"], name="y_wall_pos")

    # Z planes (bottom of UF6 at Z=0)
    z_uf6_bottom = openmc.ZPlane(z0=p["Z_UF6_BOTTOM"], name="z_uf6_bottom")
    z_uf6_top = openmc.ZPlane(z0=p["Z_UF6_TOP"], name="z_uf6_top")
    z_wall_bottom = openmc.ZPlane(z0=p["Z_WALL_BOTTOM"], name="z_wall_bottom")
    z_wall_top = openmc.ZPlane(z0=p["Z_WALL_TOP"], name="z_wall_top")

    # Outer boundary planes (with vacuum BC if no reflector)
    if refl_mat == "none":
        x_outer_neg = openmc.XPlane(x0=-p["X_WALL"], name="x_outer_neg", boundary_type="vacuum")
        x_outer_pos = openmc.XPlane(x0=p["X_WALL"], name="x_outer_pos", boundary_type="vacuum")
        y_outer_neg = openmc.YPlane(y0=-p["Y_WALL"], name="y_outer_neg", boundary_type="vacuum")
        y_outer_pos = openmc.YPlane(y0=p["Y_WALL"], name="y_outer_pos", boundary_type="vacuum")
        z_outer_bottom = openmc.ZPlane(z0=p["Z_WALL_BOTTOM"], name="z_outer_bottom", boundary_type="vacuum")
        z_outer_top = openmc.ZPlane(z0=p["Z_WALL_TOP"], name="z_outer_top", boundary_type="vacuum")
    else:
        x_outer_neg = openmc.XPlane(x0=-p["X_REFL"], name="x_outer_neg", boundary_type="vacuum")
        x_outer_pos = openmc.XPlane(x0=p["X_REFL"], name="x_outer_pos", boundary_type="vacuum")
        y_outer_neg = openmc.YPlane(y0=-p["Y_REFL"], name="y_outer_neg", boundary_type="vacuum")
        y_outer_pos = openmc.YPlane(y0=p["Y_REFL"], name="y_outer_pos", boundary_type="vacuum")
        z_outer_bottom = openmc.ZPlane(z0=p["Z_REFL_BOTTOM"], name="z_outer_bottom", boundary_type="vacuum")
        z_outer_top = openmc.ZPlane(z0=p["Z_REFL_TOP"], name="z_outer_top", boundary_type="vacuum")

    # ══════════════════════════════════════════════════════════════════════════
    # CELLS
    # ══════════════════════════════════════════════════════════════════════════

    cells = []

    # Define region helpers
    def inside_box(x_neg, x_pos, y_neg, y_pos, z_bot, z_top):
        """Region inside a rectangular box defined by 6 planes."""
        return +x_neg & -x_pos & +y_neg & -y_pos & +z_bot & -z_top

    # Inner box region
    inner_region = inside_box(x_inner_neg, x_inner_pos,
                              y_inner_neg, y_inner_pos,
                              z_uf6_bottom, z_uf6_top)

    # Wall box region (outer surface of wall)
    wall_outer_region = inside_box(x_wall_neg, x_wall_pos,
                                   y_wall_neg, y_wall_pos,
                                   z_wall_bottom, z_wall_top)

    # Cell 1: UF6 (fissile material)
    c_uf6 = openmc.Cell(cell_id=1, name="UF6", fill=m_uf6)
    c_uf6.region = inner_region
    cells.append(c_uf6)

    # Cell 2: Wall (between inner and outer wall surfaces)
    c_wall = openmc.Cell(cell_id=2, name="Wall", fill=m_wall)
    c_wall.region = wall_outer_region & ~inner_region
    cells.append(c_wall)

    # Reflector (if present)
    if refl_mat != "none":
        # Reflector box region
        refl_outer_region = inside_box(x_outer_neg, x_outer_pos,
                                       y_outer_neg, y_outer_pos,
                                       z_outer_bottom, z_outer_top)

        c_refl = openmc.Cell(cell_id=3, name="Reflector", fill=m_refl)
        c_refl.region = refl_outer_region & ~wall_outer_region
        cells.append(c_refl)

    # ══════════════════════════════════════════════════════════════════════════
    # GEOMETRY
    # ══════════════════════════════════════════════════════════════════════════

    universe = openmc.Universe(cells=cells)
    geometry = openmc.Geometry(universe)

    # Return model components and dimensions for plotting
    dims = {
        "length": p["LENGTH"],
        "width": p["WIDTH"],
        "height": p["HEIGHT"],
        "total_x": p["TOTAL_X"],
        "total_y": p["TOTAL_Y"],
        "total_z": p["TOTAL_Z"],
        "z_center": p["HEIGHT"] / 2,
        "wall_thickness": p["WALL_THICKNESS"],
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
    """
    Create visualization plots with explicit material colors.

    Returns:
        plots: openmc.Plots object
        color_legend: dict mapping material name -> RGB tuple
    """
    from critbuddy.core.materials import get_color_mapping, get_color_legend

    total_x = dims["total_x"]
    total_y = dims["total_y"]
    total_z = dims["total_z"]
    z_center = dims["z_center"]

    color_mapping = get_color_mapping(materials)

    plots = openmc.Plots()

    # XY slice (top-down view at mid-height)
    p1 = openmc.Plot(name="xy")
    p1.basis = "xy"
    p1.origin = (0, 0, z_center)
    p1.width = (total_x * 1.1, total_y * 1.1)
    p1.pixels = (600, 600)
    p1.color_by = "material"
    p1.colors = color_mapping
    plots.append(p1)

    # XZ slice (side view through center)
    p2 = openmc.Plot(name="xz")
    p2.basis = "xz"
    p2.origin = (0, 0, z_center)
    p2.width = (total_x * 1.1, total_z * 1.1)
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
  Internal L x W x H: {dims['length']:>6.2f} x {dims['width']:>6.2f} x {dims['height']:>6.2f}
  Wall thickness:     {dims['wall_thickness']:>8.4f}
  Reflector thick:    {dims['refl_thickness']:>8.4f}
  Total L x W x H:    {dims['total_x']:>6.2f} x {dims['total_y']:>6.2f} x {dims['total_z']:>6.2f}

MATERIALS
  Wall:               {p['WALL_MATERIAL']}
  Reflector:          {p['REFLECTOR_MATERIAL']}

SIMULATION
  {int(p['PARTICLES'])} particles x {int(p['BATCHES'])} batches ({int(p['INACTIVE'])} inactive)
================================================================================
""")
