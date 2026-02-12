#!/usr/bin/env python3
"""
================================================================================
CYLINDER CRITICALITY MODEL - OpenMC
================================================================================
Template:   cylinder
Problem:    Single vertical cylinder filled with UF6 (user-specified dimensions)
Geometry:   Cylinder with aluminum wall and water reflector
================================================================================
"""

import openmc
from critbuddy.core.materials import create_uf6, get_material


def build_model(p):
    """
    Build OpenMC model from parameters.

    Parameters like ENRICHMENT, UF6_DENSITY, and geometry values come from the
    template's derive_params() function or legacy study.yaml.
    Materials are created using the shared materials library.
    """

    # ══════════════════════════════════════════════════════════════════════════
    # MATERIALS (from shared library)
    # ══════════════════════════════════════════════════════════════════════════

    m1 = create_uf6(p["ENRICHMENT"], density=p["UF6_DENSITY"])

    # Wall material (from registry if available, else default to aluminum)
    wall_mat = p.get("WALL_MATERIAL", "aluminum")
    m2 = get_material(wall_mat, solver="openmc")

    # Reflector material (from registry if available)
    refl_mat = p.get("REFLECTOR_MATERIAL", "water")
    if refl_mat != "none":
        m3 = get_material(refl_mat, solver="openmc")
        materials = openmc.Materials([m1, m2, m3])
    else:
        materials = openmc.Materials([m1, m2])

    # ══════════════════════════════════════════════════════════════════════════
    # SURFACES (radii and z-planes pre-computed in study.yaml)
    # ══════════════════════════════════════════════════════════════════════════

    s1 = openmc.ZCylinder(r=p["R1"], name="s1")                          # Inner
    s2 = openmc.ZCylinder(r=p["R2"], name="s2")                          # Wall outer
    s3 = openmc.ZCylinder(r=p["R3"], name="s3", boundary_type="vacuum")  # Refl outer

    s4 = openmc.ZPlane(z0=p["Z_BOTTOM"], name="s4")                      # Bottom
    s5 = openmc.ZPlane(z0=p["Z_TOP"], name="s5")                         # Top
    s6 = openmc.ZPlane(z0=p["Z_REFL_BOTTOM"], name="s6", boundary_type="vacuum")
    s7 = openmc.ZPlane(z0=p["Z_REFL_TOP"], name="s7", boundary_type="vacuum")

    # ══════════════════════════════════════════════════════════════════════════
    # CELLS
    # ══════════════════════════════════════════════════════════════════════════

    # Wall thickness for caps (same as radial wall)
    wall_thickness = p["WALL_THICKNESS"]
    z_uf6_bottom = p["Z_BOTTOM"] + wall_thickness
    z_uf6_top = p["Z_TOP"] - wall_thickness

    # Additional z-planes for wall caps
    s_uf6_bottom = openmc.ZPlane(z0=z_uf6_bottom, name="s_uf6_bottom")
    s_uf6_top = openmc.ZPlane(z0=z_uf6_top, name="s_uf6_top")

    cells = []

    # Cell 1: UF6 (inside wall caps)
    c1 = openmc.Cell(cell_id=1, name="UF6", fill=m1)
    c1.region = -s1 & +s_uf6_bottom & -s_uf6_top
    cells.append(c1)

    # Cell 2: Wall (radial - sides)
    c2 = openmc.Cell(cell_id=2, name="Wall", fill=m2)
    c2.region = +s1 & -s2 & +s4 & -s5
    cells.append(c2)

    # Cell 3: Wall (bottom cap)
    c3 = openmc.Cell(cell_id=3, name="Wall_bottom", fill=m2)
    c3.region = -s1 & +s4 & -s_uf6_bottom
    cells.append(c3)

    # Cell 4: Wall (top cap)
    c4 = openmc.Cell(cell_id=4, name="Wall_top", fill=m2)
    c4.region = -s1 & +s_uf6_top & -s5
    cells.append(c4)

    # Cell 5: Reflector (radial)
    c5 = openmc.Cell(cell_id=5, name="Refl_radial", fill=m3)
    c5.region = +s2 & -s3 & +s4 & -s5
    cells.append(c5)

    # Cell 6: Reflector (bottom)
    c6 = openmc.Cell(cell_id=6, name="Refl_bottom", fill=m3)
    c6.region = -s3 & +s6 & -s4
    cells.append(c6)

    # Cell 7: Reflector (top)
    c7 = openmc.Cell(cell_id=7, name="Refl_top", fill=m3)
    c7.region = -s3 & +s5 & -s7
    cells.append(c7)

    # ══════════════════════════════════════════════════════════════════════════
    # GEOMETRY
    # ══════════════════════════════════════════════════════════════════════════

    universe = openmc.Universe(cells=cells)
    geometry = openmc.Geometry(universe)

    # Return model components and dimensions for plotting (standardized keys)
    dims = {
        "r_inner": p["R1"],           # Inner radius (UF6 region)
        "r_wall": p["R2"],            # Wall outer radius
        "r_outer": p["R3"],           # Outermost radius (including reflector)
        "height": p["HEIGHT_CM"],     # Cylinder height
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

    # XY slice (top-down)
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
    p2.pixels = (400, 800)
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
  Inner radius:       {dims['r_inner']:>8.4f}
  Wall outer:         {dims['r_wall']:>8.4f}
  Reflector outer:    {dims['r_outer']:>8.4f}
  Height:             {dims['height']:>8.2f}

SIMULATION
  {int(p['PARTICLES'])} particles x {int(p['BATCHES'])} batches ({int(p['INACTIVE'])} inactive)
================================================================================
""")
