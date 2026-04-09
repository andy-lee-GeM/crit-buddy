#!/usr/bin/env python3
"""Homogeneous UO2F2-H2O sphere with external water reflection."""

import openmc

from critbuddy.core.materials import get_color_legend, get_color_mapping
from critbuddy.core.materials.builders import uo2f2, water
from critbuddy.models.model_interface import OMCModel


class UO2F2SphereBenchmark(OMCModel):
    def create_materials(self, p):
        fuel = uo2f2(
            enrichment_pct=p["ENRICHMENT_PCT"],
            h_to_u=p["H_TO_U"],
            density=p["UO2F2_DENSITY_G_CM3"],
        )
        fuel.name = "Fuel"

        reflector = water(density_g_cm3=p["REFLECTOR_DENSITY_G_CM3"])
        reflector.name = "Water"

        return openmc.Materials([fuel, reflector]), fuel, reflector

    def build_model(self, p):
        materials, m_fuel, m_reflector = self.create_materials(p)

        fuel_surface = openmc.Sphere(r=p["SPHERE_RADIUS_CM"], name="fuel_surface")
        outer_surface = openmc.Sphere(
            r=p["OUTER_RADIUS_CM"],
            name="outer_surface",
            boundary_type=p["OUTER_BOUNDARY_TYPE"],
        )

        fuel_cell = openmc.Cell(name="fuel", fill=m_fuel, region=-fuel_surface)
        reflector_cell = openmc.Cell(
            name="reflector",
            fill=m_reflector,
            region=+fuel_surface & -outer_surface,
        )

        geometry = openmc.Geometry(openmc.Universe(cells=[fuel_cell, reflector_cell]))
        dims = {
            "SPHERE_RADIUS_CM": p["SPHERE_RADIUS_CM"],
            "REFLECTOR_THICKNESS_CM": p["REFLECTOR_THICKNESS_CM"],
            "OUTER_RADIUS_CM": p["OUTER_RADIUS_CM"],
            "FUEL_VOLUME_CM3": p["FUEL_VOLUME_CM3"],
            "FUEL_VOLUME_L": p["FUEL_VOLUME_L"],
            "OUTER_VOLUME_CM3": p["OUTER_VOLUME_CM3"],
            "OUTER_VOLUME_L": p["OUTER_VOLUME_L"],
            "PLOT_WIDTH_CM": p["PLOT_WIDTH_CM"],
        }
        return materials, geometry, dims

    def create_settings(self, p, dims):
        settings = openmc.Settings()
        settings.run_mode = "eigenvalue"
        settings.particles = int(p["PARTICLES"])
        settings.batches = int(p["BATCHES"])
        settings.inactive = int(p["INACTIVE"])
        settings.source = openmc.IndependentSource(space=openmc.stats.Point((0.0, 0.0, 0.0)))
        return settings

    def create_plots(self, dims, materials):
        colors = get_color_mapping(materials)
        plots = openmc.Plots()

        plot_xy = openmc.Plot(name="xy")
        plot_xy.basis = "xy"
        plot_xy.origin = (0.0, 0.0, 0.0)
        plot_xy.width = (dims["PLOT_WIDTH_CM"], dims["PLOT_WIDTH_CM"])
        plot_xy.pixels = (1600, 1600)
        plot_xy.color_by = "material"
        plot_xy.colors = colors
        plots.append(plot_xy)

        plot_xz = openmc.Plot(name="xz")
        plot_xz.basis = "xz"
        plot_xz.origin = (0.0, 0.0, 0.0)
        plot_xz.width = (dims["PLOT_WIDTH_CM"], dims["PLOT_WIDTH_CM"])
        plot_xz.pixels = (1600, 1600)
        plot_xz.color_by = "material"
        plot_xz.colors = colors
        plots.append(plot_xz)

        return plots, get_color_legend(materials)
