#!/usr/bin/env python3
"""
================================================================================
UF6 SHIPPING CYLINDER CRITICALITY MODEL - OpenMC
================================================================================
Template:   uf6_cylinder
Problem:    Generic UF6 shipping/storage cylinder (5A, 5B, 30B, 48X, 48Y, etc.)
Geometry:   Cylinder with wall (Monel or carbon steel) and optional reflector
================================================================================
"""

import openmc
from critbuddy.core.materials import create_uf6, get_material


def build_model(p):
    """
    Build OpenMC model from parameters.

    Geometry layers (inside to outside):
    1. UF6 fissile region
    2. Cylinder wall (material determined by cylinder type)
    3. External reflector (optional)
    """

    # ══════════════════════════════════════════════════════════════════════════
    # MATERIALS
    # ══════════════════════════════════════════════════════════════════════════

    materials_list = []

    # UF6 fissile material
    m_uf6 = create_uf6(p["ENRICHMENT"], p["UF6_DENSITY"])
    materials_list.append(m_uf6)

    # Wall material (from cylinder registry via template)
    m_wall = get_material(p["WALL_MATERIAL"], solver="openmc")
    materials_list.append(m_wall)

    # External reflector (if present)
    m_refl = None
    if p["REFLECTOR_MATERIAL"] != "none" and p["REFL_THICKNESS"] > 0:
        m_refl = get_material(p["REFLECTOR_MATERIAL"], solver="openmc")
        materials_list.append(m_refl)

    materials = openmc.Materials(materials_list)

    # ══════════════════════════════════════════════════════════════════════════
    # SURFACES
    # ══════════════════════════════════════════════════════════════════════════

    # Radial surfaces (cylinders)
    s_inner = openmc.ZCylinder(r=p["R_INNER"], name="s_inner")
    s_wall_outer = openmc.ZCylinder(r=p["R_WALL_OUTER"], name="s_wall_outer")

    # Outermost boundary
    if p["REFL_THICKNESS"] > 0:
        s_refl_outer = openmc.ZCylinder(
            r=p["R_REFL_OUTER"], name="s_refl_outer", boundary_type="vacuum"
        )
    else:
        s_wall_outer.boundary_type = "vacuum"
        s_refl_outer = None

    # Axial surfaces (z-planes)
    s_z_bottom = openmc.ZPlane(z0=p["Z_BOTTOM"], name="s_z_bottom")
    s_z_top = openmc.ZPlane(z0=p["Z_TOP"], name="s_z_top")
    s_z_uf6_bottom = openmc.ZPlane(z0=p["Z_UF6_BOTTOM"], name="s_z_uf6_bottom")
    s_z_uf6_top = openmc.ZPlane(z0=p["Z_UF6_TOP"], name="s_z_uf6_top")

    # Reflector z-boundaries
    if p["REFL_THICKNESS"] > 0:
        s_z_refl_bottom = openmc.ZPlane(
            z0=p["Z_REFL_BOTTOM"], name="s_z_refl_bottom", boundary_type="vacuum"
        )
        s_z_refl_top = openmc.ZPlane(
            z0=p["Z_REFL_TOP"], name="s_z_refl_top", boundary_type="vacuum"
        )
    else:
        s_z_bottom.boundary_type = "vacuum"
        s_z_top.boundary_type = "vacuum"
        s_z_refl_bottom = None
        s_z_refl_top = None

    # ══════════════════════════════════════════════════════════════════════════
    # CELLS
    # ══════════════════════════════════════════════════════════════════════════

    cells = []
    cell_id = 1

    # --- UF6 region ---
    c_uf6 = openmc.Cell(cell_id=cell_id, name="UF6", fill=m_uf6)
    c_uf6.region = -s_inner & +s_z_uf6_bottom & -s_z_uf6_top
    cells.append(c_uf6)
    cell_id += 1

    # --- Wall (radial) ---
    c_wall_radial = openmc.Cell(cell_id=cell_id, name="Wall_Radial", fill=m_wall)
    c_wall_radial.region = +s_inner & -s_wall_outer & +s_z_bottom & -s_z_top
    cells.append(c_wall_radial)
    cell_id += 1

    # --- Wall (bottom cap) ---
    c_wall_bottom = openmc.Cell(cell_id=cell_id, name="Wall_Bottom", fill=m_wall)
    c_wall_bottom.region = -s_inner & +s_z_bottom & -s_z_uf6_bottom
    cells.append(c_wall_bottom)
    cell_id += 1

    # --- Wall (top cap) ---
    c_wall_top = openmc.Cell(cell_id=cell_id, name="Wall_Top", fill=m_wall)
    c_wall_top.region = -s_inner & +s_z_uf6_top & -s_z_top
    cells.append(c_wall_top)
    cell_id += 1

    # --- External Reflector (if present) ---
    if m_refl is not None and s_refl_outer is not None:
        # Radial reflector
        c_refl_radial = openmc.Cell(cell_id=cell_id, name="Refl_Radial", fill=m_refl)
        c_refl_radial.region = +s_wall_outer & -s_refl_outer & +s_z_bottom & -s_z_top
        cells.append(c_refl_radial)
        cell_id += 1

        # Bottom reflector
        c_refl_bottom = openmc.Cell(cell_id=cell_id, name="Refl_Bottom", fill=m_refl)
        c_refl_bottom.region = -s_refl_outer & +s_z_refl_bottom & -s_z_bottom
        cells.append(c_refl_bottom)
        cell_id += 1

        # Top reflector
        c_refl_top = openmc.Cell(cell_id=cell_id, name="Refl_Top", fill=m_refl)
        c_refl_top.region = -s_refl_outer & +s_z_top & -s_z_refl_top
        cells.append(c_refl_top)
        cell_id += 1

    # ══════════════════════════════════════════════════════════════════════════
    # GEOMETRY
    # ══════════════════════════════════════════════════════════════════════════

    universe = openmc.Universe(cells=cells)
    geometry = openmc.Geometry(universe)

    # Dimensions for plotting (standardized keys)
    dims = {
        "r_inner": p["R_INNER"],
        "r_wall": p["R_WALL_OUTER"],
        "r_outer": p["R_REFL_OUTER"],
        "height": p["HEIGHT_CM"],
        "uf6_height": p["UF6_HEIGHT"],
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
        space=openmc.stats.Point((0, 0, p["KSRC_Z"]))
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

    r_outer = dims["r_outer"]
    height = dims["height"]
    refl_thickness = dims["refl_thickness"]

    color_mapping = get_color_mapping(materials)

    plots = openmc.Plots()

    # XY slice (top-down at mid-height)
    p1 = openmc.Plot(name="xy")
    p1.basis = "xy"
    p1.origin = (0, 0, height / 2)
    p1.width = (r_outer * 2.2, r_outer * 2.2)
    p1.pixels = (600, 600)
    p1.color_by = "material"
    p1.colors = color_mapping
    plots.append(p1)

    # XZ slice (side view)
    p2 = openmc.Plot(name="xz")
    p2.basis = "xz"
    p2.origin = (0, 0, height / 2)
    p2.width = (r_outer * 2.2, (height + 2 * refl_thickness) * 1.1)
    p2.pixels = (600, 800)
    p2.color_by = "material"
    p2.colors = color_mapping
    plots.append(p2)

    return plots, get_color_legend(materials)


def print_summary(p, dims):
    """Print case summary."""
    print(f"""
================================================================================
                    {p['CYLINDER_NAME']} - CASE SUMMARY
================================================================================
CYLINDER TYPE
  Type:               {p['CYLINDER_TYPE']}
  Wall material:      {p['WALL_MATERIAL']}

FISSILE MATERIAL
  Enrichment:         {p['ENRICHMENT']:>8.2f} wt% U-235
  UF6 Density:        {p['UF6_DENSITY']:>8.3f} g/cc
  Fill fraction:      {p['FILL_FRACTION']:>8.2f}

CYLINDER GEOMETRY (cm)
  Inner radius:       {dims['r_inner']:>8.4f}
  Outer radius:       {dims['r_outer']:>8.4f}
  Internal height:    {dims['height']:>8.2f}
  UF6 height:         {dims['uf6_height']:>8.2f}
  Wall thickness:     {p['WALL_THICKNESS']:>8.4f}

REFLECTOR
  Material:           {p['REFLECTOR_MATERIAL']}
  Thickness:          {dims['refl_thickness']:>8.2f} cm

SIMULATION
  {int(p['PARTICLES'])} particles x {int(p['BATCHES'])} batches ({int(p['INACTIVE'])} inactive)
================================================================================
""")
