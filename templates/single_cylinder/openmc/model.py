#!/usr/bin/env python3
"""
================================================================================
SINGLE CYLINDER CRITICALITY MODEL - OpenMC
================================================================================
Template:   single_cylinder
Problem:    Single vertical cylinder filled with UF6
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

    m1 = create_uf6(p["ENRICHMENT"], p["UF6_DENSITY"])

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

    cells = []

    # Cell 1: UF6
    c1 = openmc.Cell(cell_id=1, name="UF6", fill=m1)
    c1.region = -s1 & +s4 & -s5
    cells.append(c1)

    # Cell 2: Wall
    c2 = openmc.Cell(cell_id=2, name="Wall", fill=m2)
    c2.region = +s1 & -s2 & +s4 & -s5
    cells.append(c2)

    # Cell 3: Reflector (radial)
    c3 = openmc.Cell(cell_id=3, name="Refl_radial", fill=m3)
    c3.region = +s2 & -s3 & +s4 & -s5
    cells.append(c3)

    # Cell 4: Reflector (bottom)
    c4 = openmc.Cell(cell_id=4, name="Refl_bottom", fill=m3)
    c4.region = -s3 & +s6 & -s4
    cells.append(c4)

    # Cell 5: Reflector (top)
    c5 = openmc.Cell(cell_id=5, name="Refl_top", fill=m3)
    c5.region = -s3 & +s5 & -s7
    cells.append(c5)

    # ══════════════════════════════════════════════════════════════════════════
    # GEOMETRY
    # ══════════════════════════════════════════════════════════════════════════

    universe = openmc.Universe(cells=cells)
    geometry = openmc.Geometry(universe)

    # Return model components and dimensions for plotting
    dims = {
        "r1": p["R1"],
        "r2": p["R2"],
        "r3": p["R3"],
        "h": p["HEIGHT_CM"],
        "rt": p["REFL_THICKNESS"],
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
    r3, h, rt = dims["r3"], dims["h"], dims["rt"]

    # Define colors for each material
    color_mapping = {}
    for mat in materials:
        if mat.name == "UF6":
            color_mapping[mat] = (127, 255, 0)      # Chartreuse green
        elif mat.name == "Aluminum":
            color_mapping[mat] = (147, 112, 219)    # Medium purple
        elif mat.name == "Water":
            color_mapping[mat] = (30, 144, 255)     # Dodger blue
        else:
            color_mapping[mat] = (200, 200, 200)    # Gray default

    plots = openmc.Plots()

    # XY slice (top-down)
    p1 = openmc.Plot(name="xy")
    p1.basis = "xy"
    p1.origin = (0, 0, h / 2)
    p1.width = (r3 * 2.2, r3 * 2.2)
    p1.pixels = (600, 600)
    p1.color_by = "material"
    p1.colors = color_mapping
    plots.append(p1)

    # XZ slice (side view)
    p2 = openmc.Plot(name="xz")
    p2.basis = "xz"
    p2.origin = (0, 0, h / 2)
    p2.width = (r3 * 2.2, (h + 2 * rt) * 1.1)
    p2.pixels = (400, 800)
    p2.color_by = "material"
    p2.colors = color_mapping
    plots.append(p2)

    # Legend for validation plot
    legend_colors = {mat.name: rgb for mat, rgb in color_mapping.items()}

    return plots, legend_colors


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
  Inner radius:       {dims['r1']:>8.4f}
  Wall outer:         {dims['r2']:>8.4f}
  Reflector outer:    {dims['r3']:>8.4f}
  Height:             {dims['h']:>8.2f}

SIMULATION
  {int(p['PARTICLES'])} particles x {int(p['BATCHES'])} batches ({int(p['INACTIVE'])} inactive)
================================================================================
""")
