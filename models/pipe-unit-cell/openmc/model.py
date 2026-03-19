#!/usr/bin/env python3
"""
OpenMC model for a single pipe unit cell with UO2F2 fill.

Geometry:
- Cylindrical pipe with aluminum wall
- UO2F2 solution in center (parametric radius)
- UF6 gas gap between solution and wall
- Optional partial fill with gas headspace
- Reflective boundaries for unit cell (infinite lattice)

Materials (matching MCNP reference):
- m5: UO2F2 solution at 6.37 g/cm³
- m1: UF6 gas at 0.0127 g/cm³ (headspace)
- m2: Aluminum wall at 2.70 g/cm³
"""

import openmc
from critbuddy.core.materials import (
    get_color_legend,
    get_color_mapping,
)


def _create_materials(p):
    """Create materials matching MCNP reference case."""
    enrichment = p["ENRICHMENT_PCT"]

    # Material 5: UO2F2 solution (fixed density from MCNP)
    # MCNP: U-235: 0.00252, U-238: 0.00996, O-16: 0.02496, F-19: 0.02496 atom/b-cm
    uo2f2 = openmc.Material(name="UO2F2_Solution")
    uo2f2.set_density("g/cm3", 6.37)

    # Calculate atom fractions from MCNP atomic densities
    # Enrichment ~20.19% from MCNP
    u235_frac = enrichment / 100.0
    u238_frac = 1.0 - u235_frac

    # From MCNP total: U=0.01248, O=0.02496, F=0.02496 atom/b-cm
    # Normalized: U:O:F = 1:2:2 (UO2F2 stoichiometry)
    total_atoms = 1.0 + 2.0 + 2.0  # U + O + F
    u_frac = 1.0 / total_atoms
    o_frac = 2.0 / total_atoms
    f_frac = 2.0 / total_atoms

    uo2f2.add_nuclide("U235", u235_frac * u_frac, percent_type="ao")
    uo2f2.add_nuclide("U238", u238_frac * u_frac, percent_type="ao")
    uo2f2.add_nuclide("O16", o_frac, percent_type="ao")
    uo2f2.add_nuclide("F19", f_frac, percent_type="ao")

    # Material 1: UF6 gas (headspace/gap)
    # MCNP: U-235: 5.06e-5, U-238: 3.32e-5, F-19: 1.5e-4 atom/b-cm
    # Enrichment ~60.4%, density 0.0127 g/cm³
    uf6_gas = openmc.Material(name="UF6_Gas")
    uf6_gas.set_density("g/cm3", 0.0127)

    # UF6 stoichiometry: 1 U : 6 F
    uf6_total = 1.0 + 6.0
    uf6_u_frac = 1.0 / uf6_total
    uf6_f_frac = 6.0 / uf6_total

    # Use high enrichment for headspace gas (from MCNP)
    uf6_enrich = 60.4
    uf6_gas.add_nuclide("U235", (uf6_enrich / 100.0) * uf6_u_frac, percent_type="ao")
    uf6_gas.add_nuclide("U238", (1.0 - uf6_enrich / 100.0) * uf6_u_frac, percent_type="ao")
    uf6_gas.add_nuclide("F19", uf6_f_frac, percent_type="ao")
    # No thermal scattering for UF6 gas (no hydrogen)

    # Material 2: Aluminum wall
    # MCNP: Al-27: 0.06022 atom/b-cm, density 2.70 g/cm³
    aluminum = openmc.Material(name="Aluminum")
    aluminum.set_density("g/cm3", 2.70)
    aluminum.add_nuclide("Al27", 1.0, percent_type="ao")

    return openmc.Materials([uo2f2, uf6_gas, aluminum]), uo2f2, uf6_gas, aluminum


def build_model(p):
    """Build the single pipe unit cell model."""
    materials, m_uo2f2, m_uf6, m_aluminum = _create_materials(p)

    # Geometry parameters
    solution_r = p["SOLUTION_RADIUS_CM"]
    inner_r = p["PIPE_INNER_RADIUS_CM"]
    outer_r = p["PIPE_OUTER_RADIUS_CM"]
    z_min = p["Z_MIN_CM"]
    z_max = p["Z_MAX_CM"]
    fill_z_top = p["FILL_Z_TOP_CM"]
    half_pitch = p["HALF_PITCH_CM"]
    boundary_type = p["BOUNDARY_TYPE"]

    # Surfaces
    s_solution = openmc.ZCylinder(r=solution_r, name="solution_outer")
    s_pipe_inner = openmc.ZCylinder(r=inner_r, name="pipe_inner")
    s_pipe_outer = openmc.ZCylinder(r=outer_r, name="pipe_outer")

    z_bottom = openmc.ZPlane(z0=z_min, name="z_bottom")
    z_top = openmc.ZPlane(z0=z_max, name="z_top")
    z_fill = openmc.ZPlane(z0=fill_z_top, name="z_fill")

    # Boundary planes (reflective for unit cell)
    x_min = openmc.XPlane(x0=-half_pitch, name="x_min", boundary_type=boundary_type)
    x_max = openmc.XPlane(x0=half_pitch, name="x_max", boundary_type=boundary_type)
    y_min = openmc.YPlane(y0=-half_pitch, name="y_min", boundary_type=boundary_type)
    y_max = openmc.YPlane(y0=half_pitch, name="y_max", boundary_type=boundary_type)
    z_bottom.boundary_type = boundary_type
    z_top.boundary_type = boundary_type

    # System region (all space within boundaries)
    system_region = +x_min & -x_max & +y_min & -y_max & +z_bottom & -z_top

    # Cells - ensure complete coverage
    cells = [
        # UO2F2 solution (bottom, filled region)
        openmc.Cell(name="uo2f2_solution", fill=m_uo2f2,
                   region=-s_solution & +z_bottom & -z_fill),

        # Headspace (UF6 gas above solution)
        openmc.Cell(name="headspace", fill=m_uf6,
                   region=-s_solution & +z_fill & -z_top),

        # Gas gap (UF6 between solution and pipe wall)
        openmc.Cell(name="gas_gap", fill=m_uf6,
                   region=+s_solution & -s_pipe_inner & +z_bottom & -z_top),

        # Pipe wall (aluminum)
        openmc.Cell(name="pipe_wall", fill=m_aluminum,
                   region=+s_pipe_inner & -s_pipe_outer & +z_bottom & -z_top),

        # Void outside pipe (everything outside pipe within system bounds)
        openmc.Cell(name="outside_void", fill=None,
                   region=+s_pipe_outer & +x_min & -x_max & +y_min & -y_max & +z_bottom & -z_top),
    ]

    geometry = openmc.Geometry(openmc.Universe(cells=cells))

    dims = {
        "SOLUTION_RADIUS_CM": solution_r,
        "PIPE_INNER_RADIUS_CM": inner_r,
        "PIPE_OUTER_RADIUS_CM": outer_r,
        "PIPE_HEIGHT_CM": p["PIPE_HEIGHT_CM"],
        "FILL_FRACTION": p["FILL_FRACTION"],
        "FILL_HEIGHT_CM": p["FILL_HEIGHT_CM"],
        "FILL_Z_TOP_CM": fill_z_top,
        "Z_MIN_CM": z_min,
        "Z_MAX_CM": z_max,
        "HALF_PITCH_CM": half_pitch,
    }

    return materials, geometry, dims


def create_settings(p, dims):
    """Create OpenMC settings for criticality calculation."""
    settings = openmc.Settings()
    settings.run_mode = "eigenvalue"
    settings.particles = int(p["PARTICLES"])
    settings.batches = int(p["BATCHES"])
    settings.inactive = int(p["INACTIVE"])

    # Source in middle of solution region
    source_z = (dims["Z_MIN_CM"] + dims["FILL_Z_TOP_CM"]) / 2.0
    settings.source = openmc.IndependentSource(
        space=openmc.stats.Point((0.0, 0.0, source_z))
    )

    return settings


def create_plots(dims, materials):
    """Create geometry plots for validation."""
    colors = get_color_mapping(materials)

    plots = openmc.Plots()

    # XY cross-section at mid-height
    plot_xy = openmc.Plot(name="xy")
    plot_xy.basis = "xy"
    plot_xy.origin = (0.0, 0.0, dims["FILL_Z_TOP_CM"] / 2.0)
    plot_xy.width = (dims["HALF_PITCH_CM"] * 2.1, dims["HALF_PITCH_CM"] * 2.1)
    plot_xy.pixels = (1200, 1200)
    plot_xy.color_by = "material"
    plot_xy.colors = colors
    plots.append(plot_xy)

    # XZ vertical cross-section
    plot_xz = openmc.Plot(name="xz")
    plot_xz.basis = "xz"
    plot_xz.origin = (0.0, 0.0, (dims["Z_MIN_CM"] + dims["Z_MAX_CM"]) / 2.0)
    plot_xz.width = (dims["HALF_PITCH_CM"] * 2.1, dims["PIPE_HEIGHT_CM"] * 1.1)
    plot_xz.pixels = (1200, 1200)
    plot_xz.color_by = "material"
    plot_xz.colors = colors
    plots.append(plot_xz)

    legend = get_color_legend(materials)
    return plots, legend
