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
from critbuddy.core.materials.builders import (
    uo2f2 as create_uo2f2,
    uf6,
    aluminum as create_aluminum,
)
from critbuddy.core.materials.uo2f2_physics import uo2f2_density


def _create_materials(p):
    """Create materials using standard library."""
    enrichment = p["ENRICHMENT_PCT"]

    # UO2F2 solution (dry UO2F2 at default density 6.37 g/cm³)
    h_to_u = 0.0  # Dry UO2F2
    density = uo2f2_density(h_to_u=h_to_u, enrichment_pct=enrichment)
    uo2f2_mat = create_uo2f2(enrichment_pct=enrichment, h_to_u=h_to_u, density=density)
    uo2f2_mat.name = "UO2F2_Solution"

    # UF6 gas (headspace/gap) - low density gas
    # MCNP reference used 60.4% enrichment at 0.0127 g/cm³
    uf6_enrich = 60.4
    uf6_gas = uf6(enrichment_pct=uf6_enrich, density=0.0127)
    uf6_gas.name = "UF6_Gas"

    # Aluminum wall
    aluminum = create_aluminum()
    aluminum.name = "Aluminum"

    return openmc.Materials([uo2f2_mat, uf6_gas, aluminum]), uo2f2_mat, uf6_gas, aluminum


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
