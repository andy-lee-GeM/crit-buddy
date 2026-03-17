#!/usr/bin/env python3
"""
Exact OpenMC reconstruction of the canonical centrifuge unit cell deck.

Geometry represented here:
- fuel inside r < 11.70 cm from z = 0 to z = fill_z_cm
- headspace inside r < 11.70 cm from z = fill_z_cm to z = 100 cm
- water annulus from r = 11.70 to 12.70 cm for 0 < z < 100 cm
- steel wall from r = 12.70 to 13.0175 cm for 0 < z < 100 cm
- steel end caps from -0.3175 to 0 cm and from 100 to 100.3175 cm
- air inside r < 13.0175 cm above and below the capped vessel
- air outside the vessel but inside the square unit cell

Materials represented here:
- ``m1`` exact fuel card
- ``m2`` exact wall card
- ``m3`` exact water card
- ``m4`` exact air card

Canonical boundary setup for validation:
- reflective in x/y
- reflective in z
"""

import openmc
from critbuddy.core.materials import (
    get_color_legend,
    get_color_mapping,
)

def _create_materials():
    # Reproduce the current centrifuge unit cell material cards directly.
    fuel = openmc.Material(name="Fuel")
    fuel.set_density("g/cm3", 4.33)
    fuel.add_nuclide("U235", 0.001496, percent_type="ao")
    fuel.add_nuclide("U238", 0.00591035, percent_type="ao")
    fuel.add_nuclide("O16", 0.0333, percent_type="ao")
    fuel.add_nuclide("F19", 0.0148, percent_type="ao")
    fuel.add_nuclide("H1", 0.037, percent_type="ao")
    fuel.add_s_alpha_beta("c_H_in_H2O")

    wall = openmc.Material(name="Wall")
    wall.set_density("g/cm3", 8.0)
    wall.add_nuclide("Ni58", 0.0017, percent_type="ao")
    wall.add_nuclide("Fe56", 0.0777, percent_type="ao")
    wall.add_nuclide("Mn55", 4.30e-04, percent_type="ao")
    wall.add_nuclide("Mo96", 2.08e-04, percent_type="ao")
    wall.add_nuclide("Cr52", 0.0138, percent_type="ao")

    water = openmc.Material(name="Water")
    water.set_density("g/cm3", 1.0)
    water.add_nuclide("H1", 0.067, percent_type="ao")
    water.add_nuclide("O16", 0.033, percent_type="ao")
    water.add_s_alpha_beta("c_H_in_H2O")

    air = openmc.Material(name="Air")
    air.set_density("atom/b-cm", 3.3e-02)
    air.add_nuclide("N14", 3.9e-05, percent_type="ao")
    air.add_nuclide("O16", 1.05e-05, percent_type="ao")
    air.add_nuclide("Ar40", 2.4e-04, percent_type="ao")
    air.add_nuclide("H1", 1.1e-06, percent_type="ao")

    return openmc.Materials([fuel, wall, water, air]), fuel, wall, water, air


def build_model(p):
    """Build the centrifuge unit-cell model with parameterized boundary types."""
    materials, m_fuel, m_wall, m_water, m_air = _create_materials()

    fuel_radius = p["FUEL_RADIUS_CM"]
    water_outer = p["WATER_OUTER_RADIUS_CM"]
    outer_radius = p["OUTER_RADIUS_CM"]
    half_pitch = p["HALF_PITCH_XY_CM"]
    z_vessel_bottom = p["Z_VESSEL_BOTTOM_CM"]
    z_vessel_top = p["Z_VESSEL_TOP_CM"]
    z_cap_bottom = p["Z_CAP_BOTTOM_CM"]
    z_cap_top = p["Z_CAP_TOP_CM"]
    z_boundary_bottom = p["Z_BOUNDARY_BOTTOM_CM"]
    z_boundary_top = p["Z_BOUNDARY_TOP_CM"]
    fill_z = p["FILL_Z_CM"]

    s_fuel = openmc.ZCylinder(r=fuel_radius, name="s_fuel")
    s_water_outer = openmc.ZCylinder(r=water_outer, name="s_water_outer")
    s_outer = openmc.ZCylinder(r=outer_radius, name="s_outer")

    z0 = openmc.ZPlane(z0=z_vessel_bottom, name="z0")
    z100 = openmc.ZPlane(z0=z_vessel_top, name="z100")
    z_fill = openmc.ZPlane(z0=fill_z, name="z_fill")
    z_cap_bottom_plane = openmc.ZPlane(z0=z_cap_bottom, name="z_cap_bottom")
    z_cap_top_plane = openmc.ZPlane(z0=z_cap_top, name="z_cap_top")

    x_min = openmc.XPlane(x0=-half_pitch, name="x_min", boundary_type=p["X_BOUNDARY_TYPE"])
    x_max = openmc.XPlane(x0=half_pitch, name="x_max", boundary_type=p["X_BOUNDARY_TYPE"])
    y_min = openmc.YPlane(y0=-half_pitch, name="y_min", boundary_type=p["Y_BOUNDARY_TYPE"])
    y_max = openmc.YPlane(y0=half_pitch, name="y_max", boundary_type=p["Y_BOUNDARY_TYPE"])
    z_min = openmc.ZPlane(z0=z_boundary_bottom, name="z_min", boundary_type=p["Z_BOUNDARY_TYPE"])
    z_max = openmc.ZPlane(z0=z_boundary_top, name="z_max", boundary_type=p["Z_BOUNDARY_TYPE"])

    system_region = +x_min & -x_max & +y_min & -y_max & +z_min & -z_max

    cells = [
        openmc.Cell(name="fuel", fill=m_fuel, region=-s_fuel & +z0 & -z_fill),
        openmc.Cell(name="headspace", fill=m_air, region=-s_fuel & +z_fill & -z100),
        openmc.Cell(
            name="water_annulus",
            fill=m_water,
            region=+s_fuel & -s_water_outer & +z0 & -z100,
        ),
        openmc.Cell(
            name="material_wall",
            fill=m_wall,
            region=+s_water_outer & -s_outer & +z0 & -z100,
        ),
        openmc.Cell(
            name="top_cap",
            fill=m_wall,
            region=-s_outer & +z100 & -z_cap_top_plane,
        ),
        openmc.Cell(
            name="bottom_cap",
            fill=m_wall,
            region=-s_outer & +z_cap_bottom_plane & -z0,
        ),
        openmc.Cell(
            name="top_internal_air",
            fill=m_air,
            region=-s_outer & +z_cap_top_plane & -z_max,
        ),
        openmc.Cell(
            name="bottom_internal_air",
            fill=m_air,
            region=-s_outer & +z_min & -z_cap_bottom_plane,
        ),
        # The literal MCNP cells 7-10 overlap awkwardly; this is their intended union.
        openmc.Cell(
            name="outer_air",
            fill=m_air,
            region=system_region & ~(-s_outer & +z_min & -z_max),
        ),
    ]

    geometry = openmc.Geometry(openmc.Universe(cells=cells))

    dims = {
        "FILL_FRACTION": p["FILL_FRACTION"],
        "FILL_HEIGHT_CM": p["FILL_HEIGHT_CM"],
        "FILL_Z_CM": fill_z,
        "FUEL_RADIUS_CM": fuel_radius,
        "WATER_OUTER_RADIUS_CM": water_outer,
        "OUTER_RADIUS_CM": outer_radius,
        "HALF_PITCH_XY_CM": half_pitch,
        "TOTAL_X": p["TOTAL_X"],
        "TOTAL_Y": p["TOTAL_Y"],
        "TOTAL_Z": p["TOTAL_Z"],
        "Z_VESSEL_BOTTOM_CM": z_vessel_bottom,
        "Z_VESSEL_TOP_CM": z_vessel_top,
        "Z_CAP_BOTTOM_CM": z_cap_bottom,
        "Z_CAP_TOP_CM": z_cap_top,
        "Z_BOUNDARY_BOTTOM_CM": z_boundary_bottom,
        "Z_BOUNDARY_TOP_CM": z_boundary_top,
        "SOURCE_Z_CM": p["SOURCE_Z_CM"],
    }
    return materials, geometry, dims


def create_settings(p, dims):
    """Create OpenMC settings matching the MCNP kcode setup."""
    settings = openmc.Settings()
    settings.run_mode = "eigenvalue"
    settings.particles = int(p["PARTICLES"])
    settings.batches = int(p["BATCHES"])
    settings.inactive = int(p["INACTIVE"])

    z_lo = dims["Z_VESSEL_BOTTOM_CM"] + 1.0e-6
    z_hi = dims["FILL_Z_CM"] - 1.0e-6
    if z_hi <= z_lo:
        source_z = z_lo
    else:
        source_z = min(max(dims["SOURCE_Z_CM"], z_lo), z_hi)

    settings.source = openmc.IndependentSource(
        space=openmc.stats.Point((0.0, 0.0, source_z))
    )
    return settings


def create_plots(dims, materials):
    """Create XY and XZ geometry plots for validation."""
    colors = get_color_mapping(materials)

    plots = openmc.Plots()

    plot_xy = openmc.Plot(name="xy")
    plot_xy.basis = "xy"
    plot_xy.origin = (0.0, 0.0, 0.5 * dims["FILL_Z_CM"])
    plot_xy.width = (dims["TOTAL_X"] * 1.05, dims["TOTAL_Y"] * 1.05)
    plot_xy.pixels = (1600, 1600)
    plot_xy.color_by = "material"
    plot_xy.colors = colors
    plots.append(plot_xy)

    plot_xz = openmc.Plot(name="xz")
    plot_xz.basis = "xz"
    plot_xz.origin = (0.0, 0.0, 0.5 * (dims["Z_BOUNDARY_BOTTOM_CM"] + dims["Z_BOUNDARY_TOP_CM"]))
    plot_xz.width = (dims["TOTAL_X"] * 1.05, dims["TOTAL_Z"] * 1.05)
    plot_xz.pixels = (1600, 1200)
    plot_xz.color_by = "material"
    plot_xz.colors = colors
    plots.append(plot_xz)

    legend = get_color_legend(materials)
    return plots, legend
