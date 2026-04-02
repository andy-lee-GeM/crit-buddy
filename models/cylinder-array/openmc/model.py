#!/usr/bin/env python3
"""
Finite OpenMC array of capped centrifuge-style cylinders.

Geometry:
- one reusable closed cylinder universe centered in a local pitch cell
- finite x/y/z array assembled with a rectangular lattice
- user-facing axes:
  - x: horizontal
  - y: vertical
  - z: depth

Internal OpenMC axis mapping:
- user x -> OpenMC x
- user y -> OpenMC z
- user z -> OpenMC y
"""

import openmc

from critbuddy.core.materials import (
    create_fissile_material,
    get_color_legend,
    get_color_mapping,
    get_material,
)


def _create_materials(p):
    fuel = create_fissile_material(
        fissile_material=p["FISSILE_MATERIAL"],
        enrichment_pct=p["ENRICHMENT_PCT"],
        fissile_density=p.get("FISSILE_DENSITY_G_CM3"),
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


def _build_single_cylinder_universe(p, m_fuel, m_wall, m_water, m_air):
    """Build one local lattice universe centered on a single closed cylinder."""
    fuel_radius = p["FUEL_RADIUS_CM"]
    water_outer = p["WATER_OUTER_RADIUS_CM"]
    outer_radius = p["OUTER_RADIUS_CM"]

    local_z_vessel_bottom = p["LOCAL_Z_VESSEL_BOTTOM_CM"]
    local_z_vessel_top = p["LOCAL_Z_VESSEL_TOP_CM"]
    local_z_cap_bottom = p["LOCAL_Z_CAP_BOTTOM_CM"]
    local_z_cap_top = p["LOCAL_Z_CAP_TOP_CM"]
    local_fill_z = p["LOCAL_FILL_Z_CM"]

    half_pitch_x = 0.5 * p["PITCH_X_CM"]
    half_pitch_depth = 0.5 * p["PITCH_Z_CM"]
    half_pitch_vertical = 0.5 * p["PITCH_Y_CM"]

    s_fuel = openmc.ZCylinder(r=fuel_radius, name="s_fuel")
    s_water_outer = openmc.ZCylinder(r=water_outer, name="s_water_outer")
    s_outer = openmc.ZCylinder(r=outer_radius, name="s_outer")

    z_vessel_bottom = openmc.ZPlane(z0=local_z_vessel_bottom, name="z_vessel_bottom")
    z_vessel_top = openmc.ZPlane(z0=local_z_vessel_top, name="z_vessel_top")
    z_fill = openmc.ZPlane(z0=local_fill_z, name="z_fill")
    z_cap_bottom = openmc.ZPlane(z0=local_z_cap_bottom, name="z_cap_bottom")
    z_cap_top = openmc.ZPlane(z0=local_z_cap_top, name="z_cap_top")

    x_min = openmc.XPlane(x0=-half_pitch_x, name="x_pitch_min")
    x_max = openmc.XPlane(x0=half_pitch_x, name="x_pitch_max")
    y_min = openmc.YPlane(y0=-half_pitch_depth, name="depth_pitch_min")
    y_max = openmc.YPlane(y0=half_pitch_depth, name="depth_pitch_max")
    z_min = openmc.ZPlane(z0=-half_pitch_vertical, name="vertical_pitch_min")
    z_max = openmc.ZPlane(z0=half_pitch_vertical, name="vertical_pitch_max")

    local_region = +x_min & -x_max & +y_min & -y_max & +z_min & -z_max
    vessel_envelope = -s_outer & +z_cap_bottom & -z_cap_top

    cells = [
        openmc.Cell(name="fuel", fill=m_fuel, region=-s_fuel & +z_vessel_bottom & -z_fill),
        openmc.Cell(name="headspace", fill=m_air, region=-s_fuel & +z_fill & -z_vessel_top),
        openmc.Cell(
            name="water_annulus",
            fill=m_water,
            region=+s_fuel & -s_water_outer & +z_vessel_bottom & -z_vessel_top,
        ),
        openmc.Cell(
            name="material_wall",
            fill=m_wall,
            region=+s_water_outer & -s_outer & +z_vessel_bottom & -z_vessel_top,
        ),
        openmc.Cell(
            name="top_cap",
            fill=m_wall,
            region=-s_outer & +z_vessel_top & -z_cap_top,
        ),
        openmc.Cell(
            name="bottom_cap",
            fill=m_wall,
            region=-s_outer & +z_cap_bottom & -z_vessel_bottom,
        ),
        openmc.Cell(
            name="local_air",
            fill=m_air,
            region=local_region & ~vessel_envelope,
        ),
    ]
    return openmc.Universe(cells=cells)


def _build_lattice(p, unit_universe, m_air):
    """Build the finite rectangular lattice of repeated cylinder universes."""
    lattice = openmc.RectLattice(name="cylinder_array")
    lattice.lower_left = (
        -0.5 * p["LATTICE_SPAN_X_CM"],
        -0.5 * p["LATTICE_SPAN_Z_CM"],
        -0.5 * p["LATTICE_SPAN_Y_CM"],
    )
    lattice.pitch = (p["PITCH_X_CM"], p["PITCH_Z_CM"], p["PITCH_Y_CM"])

    nx = int(p["NUM_CYLINDERS_X"])
    ny = int(p["NUM_CYLINDERS_Y"])
    nz = int(p["NUM_CYLINDERS_Z"])
    lattice.universes = [
        [[unit_universe for _ in range(nx)] for _ in range(nz)] for _ in range(ny)
    ]
    lattice.outer = openmc.Universe(cells=[openmc.Cell(fill=m_air)])
    return lattice


def build_model(p):
    """Build the finite cylinder-array model."""
    materials, m_fuel, m_wall, m_water, m_air = _create_materials(p)
    unit_universe = _build_single_cylinder_universe(p, m_fuel, m_wall, m_water, m_air)
    lattice = _build_lattice(p, unit_universe, m_air)

    array_x_min = openmc.XPlane(x0=-0.5 * p["ARRAY_X_CM"], name="array_x_min")
    array_x_max = openmc.XPlane(x0=0.5 * p["ARRAY_X_CM"], name="array_x_max")
    array_depth_min = openmc.YPlane(y0=-0.5 * p["ARRAY_Z_CM"], name="array_depth_min")
    array_depth_max = openmc.YPlane(y0=0.5 * p["ARRAY_Z_CM"], name="array_depth_max")
    array_vertical_min = openmc.ZPlane(z0=-0.5 * p["ARRAY_Y_CM"], name="array_vertical_min")
    array_vertical_max = openmc.ZPlane(z0=0.5 * p["ARRAY_Y_CM"], name="array_vertical_max")

    x_min = openmc.XPlane(
        x0=-0.5 * p["TOTAL_X_CM"],
        name="x_min",
        boundary_type=p["X_BOUNDARY_TYPE"],
    )
    x_max = openmc.XPlane(
        x0=0.5 * p["TOTAL_X_CM"],
        name="x_max",
        boundary_type=p["X_BOUNDARY_TYPE"],
    )
    depth_min = openmc.YPlane(
        y0=-0.5 * p["TOTAL_Z_CM"],
        name="depth_min",
        boundary_type=p["Z_BOUNDARY_TYPE"],
    )
    depth_max = openmc.YPlane(
        y0=0.5 * p["TOTAL_Z_CM"],
        name="depth_max",
        boundary_type=p["Z_BOUNDARY_TYPE"],
    )
    vertical_min = openmc.ZPlane(
        z0=-0.5 * p["TOTAL_Y_CM"],
        name="vertical_min",
        boundary_type=p["Y_BOUNDARY_TYPE"],
    )
    vertical_max = openmc.ZPlane(
        z0=0.5 * p["TOTAL_Y_CM"],
        name="vertical_max",
        boundary_type=p["Y_BOUNDARY_TYPE"],
    )

    array_region = (
        +array_x_min
        & -array_x_max
        & +array_depth_min
        & -array_depth_max
        & +array_vertical_min
        & -array_vertical_max
    )
    system_region = +x_min & -x_max & +depth_min & -depth_max & +vertical_min & -vertical_max
    shell_region = system_region & ~array_region
    root = openmc.Universe(
        cells=[
            openmc.Cell(name="array_region", fill=lattice, region=array_region),
            openmc.Cell(name="edge_moderator", fill=m_water, region=shell_region),
        ]
    )
    geometry = openmc.Geometry(root)

    dims = {
        "FISSILE_MATERIAL": p["FISSILE_MATERIAL"],
        "FISSILE_DENSITY_G_CM3": p.get("FISSILE_DENSITY_G_CM3"),
        "FILL_FRACTION": p["FILL_FRACTION"],
        "FILL_HEIGHT_CM": p["FILL_HEIGHT_CM"],
        "INNER_RADIUS_CM": p["INNER_RADIUS_CM"],
        "WATER_FILM_THICKNESS_CM": p["WATER_FILM_THICKNESS_CM"],
        "WALL_THICKNESS_CM": p["WALL_THICKNESS_CM"],
        "FUEL_RADIUS_CM": p["FUEL_RADIUS_CM"],
        "WATER_OUTER_RADIUS_CM": p["WATER_OUTER_RADIUS_CM"],
        "OUTER_RADIUS_CM": p["OUTER_RADIUS_CM"],
        "OUTER_DIAMETER_CM": p["OUTER_DIAMETER_CM"],
        "VESSEL_HEIGHT_CM": p["VESSEL_HEIGHT_CM"],
        "OUTER_HEIGHT_CM": p["OUTER_HEIGHT_CM"],
        "NUM_CYLINDERS_X": p["NUM_CYLINDERS_X"],
        "NUM_CYLINDERS_Y": p["NUM_CYLINDERS_Y"],
        "NUM_CYLINDERS_Z": p["NUM_CYLINDERS_Z"],
        "TOTAL_CYLINDERS": p["TOTAL_CYLINDERS"],
        "WALL_TO_WALL_GAP_CM": p["WALL_TO_WALL_GAP_CM"],
        "EDGE_MODERATOR_THICKNESS_CM": p["EDGE_MODERATOR_THICKNESS_CM"],
        "PITCH_X_CM": p["PITCH_X_CM"],
        "PITCH_Y_CM": p["PITCH_Y_CM"],
        "PITCH_Z_CM": p["PITCH_Z_CM"],
        "ARRAY_X_CM": p["ARRAY_X_CM"],
        "ARRAY_Y_CM": p["ARRAY_Y_CM"],
        "ARRAY_Z_CM": p["ARRAY_Z_CM"],
        "TOTAL_X_CM": p["TOTAL_X_CM"],
        "TOTAL_Y_CM": p["TOTAL_Y_CM"],
        "TOTAL_Z_CM": p["TOTAL_Z_CM"],
        "LOCAL_Z_VESSEL_BOTTOM_CM": p["LOCAL_Z_VESSEL_BOTTOM_CM"],
        "LOCAL_Z_VESSEL_TOP_CM": p["LOCAL_Z_VESSEL_TOP_CM"],
        "LOCAL_Z_CAP_BOTTOM_CM": p["LOCAL_Z_CAP_BOTTOM_CM"],
        "LOCAL_Z_CAP_TOP_CM": p["LOCAL_Z_CAP_TOP_CM"],
        "LOCAL_FILL_Z_CM": p["LOCAL_FILL_Z_CM"],
    }
    return materials, geometry, dims


def create_settings(p, dims):
    """Create OpenMC settings with a distributed source over the fuel envelope."""
    settings = openmc.Settings()
    settings.run_mode = "eigenvalue"
    settings.particles = int(p["PARTICLES"])
    settings.batches = int(p["BATCHES"])
    settings.inactive = int(p["INACTIVE"])

    x_half_span = 0.5 * (dims["NUM_CYLINDERS_X"] - 1) * dims["PITCH_X_CM"] + dims["FUEL_RADIUS_CM"]
    depth_half_span = 0.5 * (dims["NUM_CYLINDERS_Z"] - 1) * dims["PITCH_Z_CM"] + dims["FUEL_RADIUS_CM"]

    z_lower = (
        -0.5 * (dims["NUM_CYLINDERS_Y"] - 1) * dims["PITCH_Y_CM"]
        + dims["LOCAL_Z_VESSEL_BOTTOM_CM"]
        + 1.0e-6
    )
    z_upper = (
        0.5 * (dims["NUM_CYLINDERS_Y"] - 1) * dims["PITCH_Y_CM"]
        + dims["LOCAL_FILL_Z_CM"]
        - 1.0e-6
    )

    settings.source = openmc.IndependentSource(
        space=openmc.stats.Box(
            lower_left=(-x_half_span, -depth_half_span, z_lower),
            upper_right=(x_half_span, depth_half_span, z_upper),
        )
    )
    return settings


def create_plots(dims, materials):
    """Create horizontal and vertical geometry plots for validation."""
    colors = get_color_mapping(materials)
    plots = openmc.Plots()

    def _centerline(count, pitch):
        centers = [(idx - 0.5 * (count - 1)) * pitch for idx in range(count)]
        return min(centers, key=abs)

    x_slice = _centerline(dims["NUM_CYLINDERS_X"], dims["PITCH_X_CM"])
    depth_slice = _centerline(dims["NUM_CYLINDERS_Z"], dims["PITCH_Z_CM"])
    vertical_center = _centerline(dims["NUM_CYLINDERS_Y"], dims["PITCH_Y_CM"])

    z_slice = (
        vertical_center
        + dims["LOCAL_Z_VESSEL_BOTTOM_CM"]
        + 0.5 * dims["FILL_HEIGHT_CM"]
    )

    plot_xy = openmc.Plot(name="xy")
    plot_xy.basis = "xy"
    plot_xy.origin = (0.0, 0.0, z_slice)
    plot_xy.width = (dims["TOTAL_X_CM"] * 1.05, dims["TOTAL_Z_CM"] * 1.05)
    plot_xy.pixels = (1600, 1600)
    plot_xy.color_by = "material"
    plot_xy.colors = colors
    plots.append(plot_xy)

    plot_xz = openmc.Plot(name="xz")
    plot_xz.basis = "xz"
    plot_xz.origin = (0.0, depth_slice, 0.0)
    plot_xz.width = (dims["TOTAL_X_CM"] * 1.05, dims["TOTAL_Y_CM"] * 1.05)
    plot_xz.pixels = (1600, 1200)
    plot_xz.color_by = "material"
    plot_xz.colors = colors
    plots.append(plot_xz)

    plot_yz = openmc.Plot(name="yz")
    plot_yz.basis = "yz"
    plot_yz.origin = (x_slice, 0.0, 0.0)
    plot_yz.width = (dims["TOTAL_Z_CM"] * 1.05, dims["TOTAL_Y_CM"] * 1.05)
    plot_yz.pixels = (1600, 1200)
    plot_yz.color_by = "material"
    plot_yz.colors = colors
    plots.append(plot_yz)

    return plots, get_color_legend(materials)
