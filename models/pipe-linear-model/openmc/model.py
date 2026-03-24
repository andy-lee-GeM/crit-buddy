#!/usr/bin/env python3
"""
Exact reflected single-pipe unit cell for AD-7 parity checks.

Geometry represented here, matching the original MCNP deck style:
- central UF6 gas core inside ``r < gas_core_radius``
- annular UO2F2 layer from ``gas_core_radius`` to ``fuel_outer_radius``
- wall annulus from ``fuel_outer_radius`` to ``pipe_outer_radius``
- water moderator everywhere else inside the reflected box
"""

import openmc

from critbuddy.core.materials import get_color_legend, get_color_mapping
from critbuddy.core.materials.builders import (
    aluminum,
    stainless_steel_304,
    uo2f2,
    uf6,
    water,
)


def _create_materials(p):
    fuel = uo2f2(
        enrichment_pct=p["ENRICHMENT_PCT"],
        h_to_u=0.0,
        density=p["UO2F2_DENSITY_G_CM3"],
    )
    fuel.name = "Fuel"

    gas = uf6(enrichment_pct=p["ENRICHMENT_PCT"], density=p["UF6_DENSITY_G_CM3"])
    gas.name = "Gas"

    if p["WALL_MATERIAL"] == "ss304":
        wall = stainless_steel_304()
    else:
        wall = aluminum()
    wall.name = "Wall"

    moderator = water(density_g_cm3=p["MODERATOR_DENSITY_G_CM3"])
    moderator.name = "Water"
    return openmc.Materials([fuel, gas, wall, moderator]), fuel, gas, wall, moderator


def build_model(p):
    """Build the reflected single-pipe unit cell."""
    materials, m_fuel, m_gas, m_wall, m_water = _create_materials(p)

    gas_core_radius = p["GAS_CORE_RADIUS_CM"]
    fuel_outer_radius = p["FUEL_OUTER_RADIUS_CM"]
    outer_radius = p["PIPE_OUTER_RADIUS_CM"]
    half_pitch = p["HALF_PITCH_CM"]
    half_height = p["HALF_HEIGHT_CM"]

    s_gas = openmc.ZCylinder(r=gas_core_radius, name="s_gas")
    s_fuel_outer = openmc.ZCylinder(r=fuel_outer_radius, name="s_fuel_outer")
    s_outer = openmc.ZCylinder(r=outer_radius, name="s_outer")

    x_min = openmc.XPlane(x0=-half_pitch, name="x_min", boundary_type=p["X_BOUNDARY_TYPE"])
    x_max = openmc.XPlane(x0=half_pitch, name="x_max", boundary_type=p["X_BOUNDARY_TYPE"])
    y_min = openmc.YPlane(y0=-half_pitch, name="y_min", boundary_type=p["Y_BOUNDARY_TYPE"])
    y_max = openmc.YPlane(y0=half_pitch, name="y_max", boundary_type=p["Y_BOUNDARY_TYPE"])
    z_min = openmc.ZPlane(z0=-half_height, name="z_min", boundary_type=p["Z_BOUNDARY_TYPE"])
    z_max = openmc.ZPlane(z0=half_height, name="z_max", boundary_type=p["Z_BOUNDARY_TYPE"])

    system_region = +x_min & -x_max & +y_min & -y_max & +z_min & -z_max

    cells = [
        openmc.Cell(name="gas_core", fill=m_gas, region=-s_gas & system_region),
        openmc.Cell(name="fuel", fill=m_fuel, region=+s_gas & -s_fuel_outer & system_region),
        openmc.Cell(name="wall", fill=m_wall, region=+s_fuel_outer & -s_outer & system_region),
        openmc.Cell(name="moderator", fill=m_water, region=system_region & ~(-s_outer)),
    ]

    geometry = openmc.Geometry(openmc.Universe(cells=cells))
    dims = {
        "GAS_CORE_RADIUS_CM": gas_core_radius,
        "FUEL_OUTER_RADIUS_CM": fuel_outer_radius,
        "PIPE_OUTER_RADIUS_CM": outer_radius,
        "SEPARATION_CM": p["SEPARATION_CM"],
        "HALF_PITCH_CM": half_pitch,
        "HALF_HEIGHT_CM": half_height,
        "TOTAL_X": p["TOTAL_X"],
        "TOTAL_Y": p["TOTAL_Y"],
        "TOTAL_Z": p["TOTAL_Z"],
        "SOURCE_Z_CM": p["SOURCE_Z_CM"],
    }
    return materials, geometry, dims


def create_settings(p, dims):
    """Create OpenMC settings for the parity unit cell."""
    settings = openmc.Settings()
    settings.run_mode = "eigenvalue"
    settings.particles = int(p["PARTICLES"])
    settings.batches = int(p["BATCHES"])
    settings.inactive = int(p["INACTIVE"])
    settings.source = openmc.IndependentSource(space=openmc.stats.Point((0.0, 0.0, dims["SOURCE_Z_CM"])))
    return settings


def create_plots(dims, materials):
    """Create XY and XZ plots following the centrifuge model convention."""
    colors = get_color_mapping(materials)
    plots = openmc.Plots()

    plot_xy = openmc.Plot(name="xy")
    plot_xy.basis = "xy"
    plot_xy.origin = (0.0, 0.0, 0.0)
    plot_xy.width = (dims["TOTAL_X"] * 1.05, dims["TOTAL_Y"] * 1.05)
    plot_xy.pixels = (1600, 1600)
    plot_xy.color_by = "material"
    plot_xy.colors = colors
    plots.append(plot_xy)

    plot_xz = openmc.Plot(name="xz")
    plot_xz.basis = "xz"
    plot_xz.origin = (0.0, 0.0, 0.0)
    plot_xz.width = (dims["TOTAL_X"] * 1.05, dims["TOTAL_Z"] * 1.05)
    plot_xz.pixels = (1600, 1200)
    plot_xz.color_by = "material"
    plot_xz.colors = colors
    plots.append(plot_xz)

    return plots, get_color_legend(materials)
