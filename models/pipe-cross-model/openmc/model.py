#!/usr/bin/env python3
"""
Reflected offset pipe crossing for AD-7 parity checks.

Geometry represented here:
- canonical ``xz`` mode: a z-directed pipe at the origin plus an x-directed pipe
  offset in +y by ``pipe_center_offset_cm``
- optional ``xyz`` mode: adds a y-directed pipe offset in +x by the same amount
- reflective box bounds follow the literal MCNP-style asymmetric unit cell
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
from critbuddy.core.materials.uo2f2_physics import uo2f2_density


def _create_materials(p):
    fuel_density = p.get("UO2F2_DENSITY_G_CM3")
    if fuel_density is None:
        fuel_density = uo2f2_density(
            h_to_u=p.get("H_TO_U", 0.0),
            enrichment_pct=p["ENRICHMENT_PCT"],
        )
    fuel = uo2f2(
        enrichment_pct=p["ENRICHMENT_PCT"],
        h_to_u=p.get("H_TO_U", 0.0),
        density=fuel_density,
    )
    fuel.name = "Fuel"

    gas = uf6(enrichment_pct=p["ENRICHMENT_PCT"], density=p["UF6_DENSITY_G_CM3"])
    gas.name = "Gas"

    if p["WALL_MATERIAL"] == "aluminum":
        wall = aluminum()
    elif p["WALL_MATERIAL"] == "ss304":
        wall = stainless_steel_304()
    else:
        raise ValueError(f"Unsupported wall material: {p['WALL_MATERIAL']}")
    wall.name = "Wall"

    moderator = water(density_g_cm3=p["MODERATOR_DENSITY_G_CM3"])
    moderator.name = "Water"
    return openmc.Materials([fuel, gas, wall, moderator]), fuel, gas, wall, moderator


def _union_regions(regions):
    if not regions:
        raise ValueError("At least one region is required")
    result = regions[0]
    for region in regions[1:]:
        result = result | region
    return result


def _build_xz_cells(
    system_region,
    m_gas,
    m_fuel,
    m_wall,
    m_water,
    s_z_gas,
    s_z_fuel_outer,
    s_z_outer,
    s_x_gas,
    s_x_fuel_outer,
    s_x_outer,
):
    """Build the literal z-pipe/x-pipe partition used by the MCNP reference deck."""
    z_outer_region = -s_z_outer
    x_outer_region = -s_x_outer

    cells = [
        openmc.Cell(name="z_gas_core", fill=m_gas, region=-s_z_gas & system_region),
        openmc.Cell(
            name="z_fuel",
            fill=m_fuel,
            region=+s_z_gas & -s_z_fuel_outer & system_region,
        ),
        openmc.Cell(
            name="z_wall",
            fill=m_wall,
            region=+s_z_fuel_outer & -s_z_outer & system_region,
        ),
        openmc.Cell(name="x_gas_core", fill=m_gas, region=-s_x_gas & system_region),
        openmc.Cell(
            name="x_fuel",
            fill=m_fuel,
            region=+s_x_gas & -s_x_fuel_outer & system_region,
        ),
        openmc.Cell(
            name="x_wall",
            fill=m_wall,
            region=+s_x_fuel_outer & -s_x_outer & system_region,
        ),
        openmc.Cell(
            name="moderator",
            fill=m_water,
            region=system_region & ~_union_regions([z_outer_region, x_outer_region]),
        ),
    ]
    return cells, [z_outer_region, x_outer_region]


def build_model(p):
    """Build the orthogonal crossing unit cell."""
    materials, m_fuel, m_gas, m_wall, m_water = _create_materials(p)

    gas_core_radius = p["GAS_CORE_RADIUS_CM"]
    fuel_outer_radius = p["FUEL_OUTER_RADIUS_CM"]
    outer_radius = p["PIPE_OUTER_RADIUS_CM"]
    center_offset = p["PIPE_CENTER_OFFSET_CM"]

    x_min = openmc.XPlane(x0=p["X_MIN_CM"], name="x_min", boundary_type=p["X_BOUNDARY_TYPE"])
    x_max = openmc.XPlane(x0=p["X_MAX_CM"], name="x_max", boundary_type=p["X_BOUNDARY_TYPE"])
    y_min = openmc.YPlane(y0=p["Y_MIN_CM"], name="y_min", boundary_type=p["Y_BOUNDARY_TYPE"])
    y_max = openmc.YPlane(y0=p["Y_MAX_CM"], name="y_max", boundary_type=p["Y_BOUNDARY_TYPE"])
    z_min = openmc.ZPlane(z0=p["Z_MIN_CM"], name="z_min", boundary_type=p["Z_BOUNDARY_TYPE"])
    z_max = openmc.ZPlane(z0=p["Z_MAX_CM"], name="z_max", boundary_type=p["Z_BOUNDARY_TYPE"])

    system_region = +x_min & -x_max & +y_min & -y_max & +z_min & -z_max

    s_z_gas = openmc.ZCylinder(r=gas_core_radius, name="s_z_gas")
    s_z_fuel_outer = openmc.ZCylinder(r=fuel_outer_radius, name="s_z_fuel_outer")
    s_z_outer = openmc.ZCylinder(r=outer_radius, name="s_z_outer")

    s_x_gas = openmc.XCylinder(y0=center_offset, z0=0.0, r=gas_core_radius, name="s_x_gas")
    s_x_fuel_outer = openmc.XCylinder(
        y0=center_offset, z0=0.0, r=fuel_outer_radius, name="s_x_fuel_outer"
    )
    s_x_outer = openmc.XCylinder(y0=center_offset, z0=0.0, r=outer_radius, name="s_x_outer")

    cells, outer_regions = _build_xz_cells(
        system_region,
        m_gas,
        m_fuel,
        m_wall,
        m_water,
        s_z_gas,
        s_z_fuel_outer,
        s_z_outer,
        s_x_gas,
        s_x_fuel_outer,
        s_x_outer,
    )

    if p["CROSS_MODE"] == "xyz":
        s_y_gas = openmc.YCylinder(x0=center_offset, z0=0.0, r=gas_core_radius, name="s_y_gas")
        s_y_fuel_outer = openmc.YCylinder(
            x0=center_offset, z0=0.0, r=fuel_outer_radius, name="s_y_fuel_outer"
        )
        s_y_outer = openmc.YCylinder(x0=center_offset, z0=0.0, r=outer_radius, name="s_y_outer")
        outer_regions.append(-s_y_outer)
        cells.extend(
            [
                openmc.Cell(name="y_gas_core", fill=m_gas, region=-s_y_gas & system_region),
                openmc.Cell(
                    name="y_fuel",
                    fill=m_fuel,
                    region=+s_y_gas & -s_y_fuel_outer & system_region,
                ),
                openmc.Cell(
                    name="y_wall",
                    fill=m_wall,
                    region=+s_y_fuel_outer & -s_y_outer & system_region,
                ),
            ]
        )
        outer_union = _union_regions(outer_regions)
        cells = [cell for cell in cells if cell.name != "moderator"]
        cells.append(
            openmc.Cell(name="moderator", fill=m_water, region=system_region & ~outer_union)
        )

    geometry = openmc.Geometry(openmc.Universe(cells=cells))
    dims = {
        "CROSS_MODE": p["CROSS_MODE"],
        "GAS_CORE_RADIUS_CM": gas_core_radius,
        "FUEL_OUTER_RADIUS_CM": fuel_outer_radius,
        "PIPE_OUTER_RADIUS_CM": outer_radius,
        "SEPARATION_CM": p["SEPARATION_CM"],
        "HALF_PITCH_CM": p["HALF_PITCH_CM"],
        "PIPE_CENTER_OFFSET_CM": center_offset,
        "X_MIN_CM": p["X_MIN_CM"],
        "X_MAX_CM": p["X_MAX_CM"],
        "Y_MIN_CM": p["Y_MIN_CM"],
        "Y_MAX_CM": p["Y_MAX_CM"],
        "Z_MIN_CM": p["Z_MIN_CM"],
        "Z_MAX_CM": p["Z_MAX_CM"],
        "TOTAL_X": p["TOTAL_X"],
        "TOTAL_Y": p["TOTAL_Y"],
        "TOTAL_Z": p["TOTAL_Z"],
    }
    return materials, geometry, dims


def create_settings(p, dims):
    settings = openmc.Settings()
    settings.run_mode = "eigenvalue"
    settings.particles = int(p["PARTICLES"])
    settings.batches = int(p["BATCHES"])
    settings.inactive = int(p["INACTIVE"])
    settings.source = openmc.IndependentSource(space=openmc.stats.Point((0.0, 0.0, 0.0)))
    return settings


def create_plots(dims, materials):
    colors = get_color_mapping(materials)
    plots = openmc.Plots()

    plot_xy = openmc.Plot(name="xy")
    plot_xy.basis = "xy"
    plot_xy.origin = (0.5 * (dims["X_MIN_CM"] + dims["X_MAX_CM"]), 0.5 * (dims["Y_MIN_CM"] + dims["Y_MAX_CM"]), 0.0)
    plot_xy.width = (dims["TOTAL_X"] * 1.05, dims["TOTAL_Y"] * 1.05)
    plot_xy.pixels = (1600, 1600)
    plot_xy.color_by = "material"
    plot_xy.colors = colors
    plots.append(plot_xy)

    plot_xz = openmc.Plot(name="xz")
    plot_xz.basis = "xz"
    plot_xz.origin = (0.5 * (dims["X_MIN_CM"] + dims["X_MAX_CM"]), 0.0, 0.5 * (dims["Z_MIN_CM"] + dims["Z_MAX_CM"]))
    plot_xz.width = (dims["TOTAL_X"] * 1.05, dims["TOTAL_Z"] * 1.05)
    plot_xz.pixels = (1600, 1200)
    plot_xz.color_by = "material"
    plot_xz.colors = colors
    plots.append(plot_xz)

    return plots, get_color_legend(materials)
