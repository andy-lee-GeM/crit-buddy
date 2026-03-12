#!/usr/bin/env python3
"""
Build an OpenMC model for the "Steven film" case from ``mcnp-steven-film.inp``.

This script is intentionally standalone because the existing templates do not
capture the same internal axial layering. The MCNP input appears to describe:

- a cylindrical vessel with inner radius 12.70 cm and outer radius 13.0175 cm
- a thin fissile film from z = 10.0 cm to z = 11.70 cm
- water layers at the bottom and top of the vessel
- air elsewhere in the vessel and in the lattice cell
- an "infinite lattice" treatment in x/y

The original MCNP cell cards are not fully self-consistent, so this OpenMC
model preserves the clear geometric intent and documents the assumptions here:

- x/y boundaries are periodic to approximate an infinite square lattice cell
- z boundaries are vacuum
- bottom water occupies 0.0 <= z < 1.0 inside the vessel
- internal air occupies 1.0 <= z < 10.0 and 11.70 <= z < 99.0 inside the vessel
- top water occupies 99.0 <= z < 100.0 inside the vessel
- the fissile film occupies 10.0 <= z < 11.70 inside the vessel
- the fuel material reproduces the MCNP ``m1`` atom ratios, which correspond to
  about 20 wt% enriched uranium with H/U ~= 6 and O/U ~= 5
"""

from __future__ import annotations

import argparse
from pathlib import Path

import openmc


INNER_RADIUS_CM = 12.70
OUTER_RADIUS_CM = 13.0175
HALF_PITCH_XY_CM = 12.0175
HEIGHT_CM = 100.0

FUEL_Z_MIN_CM = 10.0
FUEL_Z_MAX_CM = 11.70
BOTTOM_WATER_Z_MAX_CM = 1.0
TOP_WATER_Z_MIN_CM = 99.0

FUEL_DENSITY_G_CM3 = 5.59
WALL_DENSITY_G_CM3 = 8.8
WATER_DENSITY_G_CM3 = 0.100283856
AIR_DENSITY_G_CM3 = 3.3e-02

# MCNP m1 atom fractions. These normalize to U-235/U-total ~= 0.202.
FUEL_ATOM_RATIOS = {
    "U235": 1.883e-03,
    "U238": 7.437e-03,
    "O16": 4.664e-02,
    "H1": 5.592e-02,
}

WALL_WEIGHT_FRACTIONS = {
    "Fe": 0.9734,
    "Cr": 0.0253,
    "Mn": 0.0013,
}

AIR_ATOM_RATIOS = {
    "N14": 3.9e-05,
    "O16": 4.3e-04,
    "Ar40": 2.4e-04,
    "H1": 1.1e-06,
    "F19": 1.1e-06,
}


def _normalized(values: dict[str, float]) -> dict[str, float]:
    total = sum(values.values())
    return {key: value / total for key, value in values.items()}


def create_materials() -> openmc.Materials:
    fuel = openmc.Material(name="Steven_Film_Fuel")
    fuel.set_density("g/cm3", FUEL_DENSITY_G_CM3)
    for nuclide, fraction in _normalized(FUEL_ATOM_RATIOS).items():
        fuel.add_nuclide(nuclide, fraction, percent_type="ao")
    fuel.add_s_alpha_beta("c_H_in_H2O")

    wall = openmc.Material(name="Steven_Film_Wall")
    wall.set_density("g/cm3", WALL_DENSITY_G_CM3)
    for element, fraction in WALL_WEIGHT_FRACTIONS.items():
        wall.add_element(element, fraction, percent_type="wo")

    water = openmc.Material(name="Steven_Film_Water")
    water.set_density("g/cm3", WATER_DENSITY_G_CM3)
    water.add_nuclide("H1", 2.0, percent_type="ao")
    water.add_nuclide("O16", 1.0, percent_type="ao")
    water.add_s_alpha_beta("c_H_in_H2O")

    air = openmc.Material(name="Steven_Film_Air")
    air.set_density("g/cm3", AIR_DENSITY_G_CM3)
    for nuclide, fraction in _normalized(AIR_ATOM_RATIOS).items():
        air.add_nuclide(nuclide, fraction, percent_type="ao")

    return openmc.Materials([fuel, wall, water, air])


def create_geometry(materials: openmc.Materials) -> openmc.Geometry:
    material_by_name = {material.name: material for material in materials}

    inner_cyl = openmc.ZCylinder(r=INNER_RADIUS_CM)
    outer_cyl = openmc.ZCylinder(r=OUTER_RADIUS_CM)

    x_min = openmc.XPlane(x0=-HALF_PITCH_XY_CM, boundary_type="periodic")
    x_max = openmc.XPlane(x0=HALF_PITCH_XY_CM, boundary_type="periodic")
    y_min = openmc.YPlane(y0=-HALF_PITCH_XY_CM, boundary_type="periodic")
    y_max = openmc.YPlane(y0=HALF_PITCH_XY_CM, boundary_type="periodic")
    z_min = openmc.ZPlane(z0=0.0, boundary_type="vacuum")
    z_max = openmc.ZPlane(z0=HEIGHT_CM, boundary_type="vacuum")

    x_min.periodic_surface = x_max
    y_min.periodic_surface = y_max

    z_bottom_water_top = openmc.ZPlane(z0=BOTTOM_WATER_Z_MAX_CM)
    z_fuel_bottom = openmc.ZPlane(z0=FUEL_Z_MIN_CM)
    z_fuel_top = openmc.ZPlane(z0=FUEL_Z_MAX_CM)
    z_top_water_bottom = openmc.ZPlane(z0=TOP_WATER_Z_MIN_CM)

    unit_cell_region = +x_min & -x_max & +y_min & -y_max & +z_min & -z_max
    vessel_wall_region = +inner_cyl & -outer_cyl & +z_min & -z_max

    c_fuel = openmc.Cell(
        name="fuel_film",
        fill=material_by_name["Steven_Film_Fuel"],
        region=-inner_cyl & +z_fuel_bottom & -z_fuel_top,
    )
    c_bottom_water = openmc.Cell(
        name="bottom_water",
        fill=material_by_name["Steven_Film_Water"],
        region=-inner_cyl & +z_min & -z_bottom_water_top,
    )
    c_lower_air = openmc.Cell(
        name="lower_internal_air",
        fill=material_by_name["Steven_Film_Air"],
        region=-inner_cyl & +z_bottom_water_top & -z_fuel_bottom,
    )
    c_upper_air = openmc.Cell(
        name="upper_internal_air",
        fill=material_by_name["Steven_Film_Air"],
        region=-inner_cyl & +z_fuel_top & -z_top_water_bottom,
    )
    c_top_water = openmc.Cell(
        name="top_water",
        fill=material_by_name["Steven_Film_Water"],
        region=-inner_cyl & +z_top_water_bottom & -z_max,
    )
    c_wall = openmc.Cell(
        name="wall",
        fill=material_by_name["Steven_Film_Wall"],
        region=vessel_wall_region,
    )
    c_external_air = openmc.Cell(
        name="external_air",
        fill=material_by_name["Steven_Film_Air"],
        region=unit_cell_region & ~(-outer_cyl & +z_min & -z_max),
    )

    root = openmc.Universe(
        cells=[
            c_fuel,
            c_bottom_water,
            c_lower_air,
            c_upper_air,
            c_top_water,
            c_wall,
            c_external_air,
        ]
    )
    return openmc.Geometry(root)


def create_settings(particles: int, batches: int, inactive: int) -> openmc.Settings:
    settings = openmc.Settings()
    settings.run_mode = "eigenvalue"
    settings.particles = particles
    settings.batches = batches
    settings.inactive = inactive
    settings.source = openmc.IndependentSource(
        space=openmc.stats.Box(
            lower_left=(-INNER_RADIUS_CM, -INNER_RADIUS_CM, FUEL_Z_MIN_CM),
            upper_right=(INNER_RADIUS_CM, INNER_RADIUS_CM, FUEL_Z_MAX_CM),
            only_fissionable=True,
        )
    )
    return settings


def create_plots(materials: openmc.Materials) -> openmc.Plots:
    material_by_name = {material.name: material for material in materials}
    plots = openmc.Plots()

    xy = openmc.Plot(name="xy_fuel_plane")
    xy.basis = "xy"
    xy.origin = (0.0, 0.0, 0.5 * (FUEL_Z_MIN_CM + FUEL_Z_MAX_CM))
    xy.width = (2.2 * HALF_PITCH_XY_CM, 2.2 * HALF_PITCH_XY_CM)
    xy.pixels = (900, 900)
    xy.color_by = "material"
    xy.colors = {
        material_by_name["Steven_Film_Fuel"]: (0, 180, 0),
        material_by_name["Steven_Film_Wall"]: (60, 60, 60),
        material_by_name["Steven_Film_Water"]: (100, 170, 255),
        material_by_name["Steven_Film_Air"]: (220, 220, 220),
    }
    plots.append(xy)

    xz = openmc.Plot(name="xz_centerline")
    xz.basis = "xz"
    xz.origin = (0.0, 0.0, HEIGHT_CM / 2.0)
    xz.width = (2.2 * HALF_PITCH_XY_CM, 1.1 * HEIGHT_CM)
    xz.pixels = (900, 1200)
    xz.color_by = "material"
    xz.colors = xy.colors
    plots.append(xz)

    return plots


def export_model(output_dir: Path, particles: int, batches: int, inactive: int, plot: bool) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    materials = create_materials()
    geometry = create_geometry(materials)
    settings = create_settings(particles=particles, batches=batches, inactive=inactive)
    plots = create_plots(materials)

    cwd = Path.cwd()
    try:
        import os

        os.chdir(output_dir)
        materials.export_to_xml()
        geometry.export_to_xml()
        settings.export_to_xml()
        if plot:
            plots.export_to_xml()
    finally:
        os.chdir(cwd)


def main() -> int:
    parser = argparse.ArgumentParser(description="Export the Steven film OpenMC model.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("runs/steven_film_openmc"),
        help="Directory to write XML files into",
    )
    parser.add_argument("--particles", type=int, default=10000)
    parser.add_argument("--batches", type=int, default=150)
    parser.add_argument("--inactive", type=int, default=50)
    parser.add_argument(
        "--no-plots",
        action="store_true",
        help="Do not export plots.xml",
    )
    args = parser.parse_args()

    export_model(
        output_dir=args.output_dir,
        particles=args.particles,
        batches=args.batches,
        inactive=args.inactive,
        plot=not args.no_plots,
    )

    print(f"Exported Steven film OpenMC model to {args.output_dir}")
    print("Fuel basis: MCNP m1 atom ratios, approximately 20 wt% enriched uranium.")
    print("Boundary basis: periodic in x/y, vacuum in z.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
