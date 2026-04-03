#!/usr/bin/env python3
"""
Geometry-first OpenMC centrifuge unit-cell model.

Geometry represented here:
- fuel inside r < inner_radius from z = 0 to z = fill_height
- headspace inside r < inner_radius from z = fill_height to z = vessel_height
- water annulus from r = inner_radius to water_outer_radius
- steel wall from r = water_outer_radius to outer_radius
- steel end caps use the same thickness as the wall
- air inside r < outer_radius above and below the capped vessel
- air outside the vessel but inside the square unit cell

Materials represented here:
- ``m1`` UO2F2 fuel from the shared builder path
- ``m2`` wall from the shared material library
- ``m3`` water from the shared material library
- ``m4`` centrifuge air from the shared material library

Canonical boundary setup for validation:
- reflective in x/y
- reflective in z
"""

import openmc
from critbuddy.core.materials import (
    create_fissile_material,
    get_color_legend,
    get_color_mapping,
    get_material,
)
from critbuddy.models.model_interface import OMCModel


class CentrifugeUnitCell(OMCModel):
    def create_materials(self, p):
        fuel = create_fissile_material(
            fissile_material=p["FISSILE_MATERIAL"],
            enrichment_pct=p["ENRICHMENT_PCT"],
            h_to_u=p["H_TO_U"],
        )
        fuel.name = "Fuel"

        wall = get_material(p["WALL_MATERIAL"], solver="openmc")
        wall.name = "Wall"

        water = get_material(p["WATER_MATERIAL"], solver="openmc")
        water.set_density("g/cm3", p["WATER_DENSITY_G_CM3"])
        water.name = "Water"

        air = get_material(p["AIR_MATERIAL"], solver="openmc")
        air.name = "Air"

        return openmc.Materials([fuel, wall, water, air]), fuel, wall, water, air

    def build_model(self, p):
        """Build the centrifuge unit-cell model with parameterized boundary types."""
        materials, m_fuel, m_wall, m_water, m_air = self.create_materials(p)

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
        z_min = openmc.ZPlane(
            z0=z_boundary_bottom,
            name="z_min",
            boundary_type=p["Z_BOUNDARY_TYPE"],
        )
        z_max = openmc.ZPlane(
            z0=z_boundary_top,
            name="z_max",
            boundary_type=p["Z_BOUNDARY_TYPE"],
        )

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
            "INNER_RADIUS_CM": p["INNER_RADIUS_CM"],
            "WATER_FILM_THICKNESS_CM": p["WATER_FILM_THICKNESS_CM"],
            "WALL_THICKNESS_CM": p["WALL_THICKNESS_CM"],
            "FUEL_RADIUS_CM": fuel_radius,
            "WATER_OUTER_RADIUS_CM": water_outer,
            "OUTER_RADIUS_CM": outer_radius,
            "HALF_PITCH_XY_CM": half_pitch,
            "TOTAL_X": p["TOTAL_X"],
            "TOTAL_Y": p["TOTAL_Y"],
            "TOTAL_Z": p["TOTAL_Z"],
            "Z_VESSEL_BOTTOM_CM": z_vessel_bottom,
            "Z_VESSEL_TOP_CM": z_vessel_top,
            "VESSEL_HEIGHT_CM": z_vessel_top - z_vessel_bottom,
            "Z_CAP_BOTTOM_CM": z_cap_bottom,
            "Z_CAP_TOP_CM": z_cap_top,
            "Z_BOUNDARY_BOTTOM_CM": z_boundary_bottom,
            "Z_BOUNDARY_TOP_CM": z_boundary_top,
            "SOURCE_Z_CM": p["SOURCE_Z_CM"],
        }
        return materials, geometry, dims

    def create_settings(self, p, dims):
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

        settings.source = openmc.IndependentSource(space=openmc.stats.Point((0.0, 0.0, source_z)))
        return settings

    def create_plots(self, dims, materials):
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
        plot_xz.origin = (
            0.0,
            0.0,
            0.5 * (dims["Z_BOUNDARY_BOTTOM_CM"] + dims["Z_BOUNDARY_TOP_CM"]),
        )
        plot_xz.width = (dims["TOTAL_X"] * 1.05, dims["TOTAL_Z"] * 1.05)
        plot_xz.pixels = (1600, 1200)
        plot_xz.color_by = "material"
        plot_xz.colors = colors
        plots.append(plot_xz)

        legend = get_color_legend(materials)
        return plots, legend
