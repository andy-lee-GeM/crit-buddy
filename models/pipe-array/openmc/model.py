#!/usr/bin/env python3
"""
OpenMC model for pipe array with multiple pipes.

Geometry:
- N pipes arranged in linear array along x-axis
- Each pipe has UO2F2 solution + gas gap + aluminum wall
- Optional water moderator/reflector surrounding pipes
- Reflective or vacuum boundaries

Default 2-pipe configuration matches MCNP reference case.
"""

import openmc
from critbuddy.core.materials import (
    get_color_legend,
    get_color_mapping,
)


def _create_materials(p):
    """Create materials matching MCNP reference case."""
    enrichment = p["ENRICHMENT_PCT"]

    # Material 5: UO2F2 solution
    uo2f2 = openmc.Material(name="UO2F2_Solution")
    uo2f2.set_density("g/cm3", 6.37)

    u235_frac = enrichment / 100.0
    u238_frac = 1.0 - u235_frac

    # UO2F2 stoichiometry: U:O:F = 1:2:2
    total_atoms = 1.0 + 2.0 + 2.0
    u_frac = 1.0 / total_atoms
    o_frac = 2.0 / total_atoms
    f_frac = 2.0 / total_atoms

    uo2f2.add_nuclide("U235", u235_frac * u_frac, percent_type="ao")
    uo2f2.add_nuclide("U238", u238_frac * u_frac, percent_type="ao")
    uo2f2.add_nuclide("O16", o_frac, percent_type="ao")
    uo2f2.add_nuclide("F19", f_frac, percent_type="ao")

    # Material 1: UF6 gas
    uf6_gas = openmc.Material(name="UF6_Gas")
    uf6_gas.set_density("g/cm3", 0.0127)

    uf6_total = 1.0 + 6.0
    uf6_u_frac = 1.0 / uf6_total
    uf6_f_frac = 6.0 / uf6_total
    uf6_enrich = 60.4

    uf6_gas.add_nuclide("U235", (uf6_enrich / 100.0) * uf6_u_frac, percent_type="ao")
    uf6_gas.add_nuclide("U238", (1.0 - uf6_enrich / 100.0) * uf6_u_frac, percent_type="ao")
    uf6_gas.add_nuclide("F19", uf6_f_frac, percent_type="ao")

    # Material 2: Aluminum
    aluminum = openmc.Material(name="Aluminum")
    aluminum.set_density("g/cm3", 2.70)
    aluminum.add_nuclide("Al27", 1.0, percent_type="ao")

    # Material 3: Water (optional moderator/reflector)
    water = openmc.Material(name="Water")
    water.set_density("g/cm3", 1.0)
    water.add_nuclide("H1", 0.067, percent_type="ao")
    water.add_nuclide("O16", 0.033, percent_type="ao")
    water.add_s_alpha_beta("c_H_in_H2O")

    return (
        openmc.Materials([uo2f2, uf6_gas, aluminum, water]),
        uo2f2,
        uf6_gas,
        aluminum,
        water,
    )


def build_model(p):
    """Build the pipe array model."""
    materials, m_uo2f2, m_uf6, m_aluminum, m_water = _create_materials(p)

    # Geometry parameters
    solution_r = p["SOLUTION_RADIUS_CM"]
    inner_r = p["PIPE_INNER_RADIUS_CM"]
    outer_r = p["PIPE_OUTER_RADIUS_CM"]
    z_min = p["Z_MIN_CM"]
    z_max = p["Z_MAX_CM"]
    fill_z_top = p["FILL_Z_TOP_CM"]
    x_min_val = p["X_MIN_CM"]
    x_max_val = p["X_MAX_CM"]
    y_min_val = p["Y_MIN_CM"]
    y_max_val = p["Y_MAX_CM"]
    pipe_centers = p["PIPE_CENTERS_X"]
    boundary_type = p["BOUNDARY_TYPE"]
    include_water = p["INCLUDE_WATER"]

    # Z-planes (shared by all pipes)
    z_bottom = openmc.ZPlane(z0=z_min, name="z_bottom", boundary_type=boundary_type)
    z_top = openmc.ZPlane(z0=z_max, name="z_top", boundary_type=boundary_type)
    z_fill = openmc.ZPlane(z0=fill_z_top, name="z_fill")

    # Boundary planes
    x_min = openmc.XPlane(x0=x_min_val, name="x_min", boundary_type=boundary_type)
    x_max = openmc.XPlane(x0=x_max_val, name="x_max", boundary_type=boundary_type)
    y_min = openmc.YPlane(y0=y_min_val, name="y_min", boundary_type=boundary_type)
    y_max = openmc.YPlane(y0=y_max_val, name="y_max", boundary_type=boundary_type)

    # System region
    system_region = +x_min & -x_max & +y_min & -y_max & +z_bottom & -z_top

    cells = []
    pipe_outer_surfaces = []  # Store pipe outer surfaces for union calculation

    # Create cells for each pipe
    for i, center_x in enumerate(pipe_centers):
        # Surfaces for this pipe (offset cylinders)
        s_solution = openmc.ZCylinder(
            x0=center_x, y0=0.0, r=solution_r, name=f"solution_{i}"
        )
        s_pipe_inner = openmc.ZCylinder(
            x0=center_x, y0=0.0, r=inner_r, name=f"pipe_inner_{i}"
        )
        s_pipe_outer = openmc.ZCylinder(
            x0=center_x, y0=0.0, r=outer_r, name=f"pipe_outer_{i}"
        )
        pipe_outer_surfaces.append(s_pipe_outer)  # Store for later use

        # Solution (filled region)
        solution_region = -s_solution & +z_bottom & -z_fill
        cells.append(
            openmc.Cell(
                name=f"solution_{i}", fill=m_uo2f2, region=solution_region
            )
        )

        # Headspace (above solution)
        headspace_region = -s_solution & +z_fill & -z_top
        cells.append(
            openmc.Cell(
                name=f"headspace_{i}", fill=m_uf6, region=headspace_region
            )
        )

        # Gas gap
        gap_region = +s_solution & -s_pipe_inner & +z_bottom & -z_top
        cells.append(
            openmc.Cell(name=f"gap_{i}", fill=m_uf6, region=gap_region)
        )

        # Pipe wall
        wall_region = +s_pipe_inner & -s_pipe_outer & +z_bottom & -z_top
        cells.append(
            openmc.Cell(name=f"wall_{i}", fill=m_aluminum, region=wall_region)
        )

    # Compute union of all pipe regions (reuse surfaces created above)
    all_pipes_union = None
    for i, s_pipe_outer in enumerate(pipe_outer_surfaces):
        pipe_region = -s_pipe_outer & +z_bottom & -z_top
        if all_pipes_union is None:
            all_pipes_union = pipe_region
        else:
            all_pipes_union = all_pipes_union | pipe_region

    # Region outside all pipes but inside system boundaries
    outside_pipes = system_region & ~all_pipes_union

    if include_water:
        # Water moderator/reflector
        cells.append(
            openmc.Cell(
                name="water_moderator", fill=m_water, region=outside_pipes
            )
        )
    else:
        # Void
        cells.append(
            openmc.Cell(name="outside_void", fill=None, region=outside_pipes)
        )

    geometry = openmc.Geometry(openmc.Universe(cells=cells))

    dims = {
        "N_PIPES": p["N_PIPES"],
        "PIPE_PITCH_CM": p["PIPE_PITCH_CM"],
        "EDGE_SPACING_CM": p["EDGE_SPACING_CM"],
        "SOLUTION_RADIUS_CM": solution_r,
        "PIPE_INNER_RADIUS_CM": inner_r,
        "PIPE_OUTER_RADIUS_CM": outer_r,
        "PIPE_HEIGHT_CM": p["PIPE_HEIGHT_CM"],
        "FILL_FRACTION": p["FILL_FRACTION"],
        "FILL_HEIGHT_CM": p["FILL_HEIGHT_CM"],
        "FILL_Z_TOP_CM": fill_z_top,
        "Z_MIN_CM": z_min,
        "Z_MAX_CM": z_max,
        "X_MIN_CM": x_min_val,
        "X_MAX_CM": x_max_val,
        "Y_MIN_CM": y_min_val,
        "Y_MAX_CM": y_max_val,
        "PIPE_CENTERS_X": pipe_centers,
        "INCLUDE_WATER": include_water,
    }

    return materials, geometry, dims


def create_settings(p, dims):
    """Create OpenMC settings for criticality calculation."""
    settings = openmc.Settings()
    settings.run_mode = "eigenvalue"
    settings.particles = int(p["PARTICLES"])
    settings.batches = int(p["BATCHES"])
    settings.inactive = int(p["INACTIVE"])

    # Source in middle of first pipe
    first_pipe_x = dims["PIPE_CENTERS_X"][0]
    source_z = (dims["Z_MIN_CM"] + dims["FILL_Z_TOP_CM"]) / 2.0
    settings.source = openmc.IndependentSource(
        space=openmc.stats.Point((first_pipe_x, 0.0, source_z))
    )

    return settings


def create_plots(dims, materials):
    """Create geometry plots for validation."""
    colors = get_color_mapping(materials)

    plots = openmc.Plots()

    # XY cross-section at mid-height
    center_x = (dims["X_MIN_CM"] + dims["X_MAX_CM"]) / 2.0
    center_y = (dims["Y_MIN_CM"] + dims["Y_MAX_CM"]) / 2.0
    width_x = dims["X_MAX_CM"] - dims["X_MIN_CM"]
    width_y = dims["Y_MAX_CM"] - dims["Y_MIN_CM"]

    plot_xy = openmc.Plot(name="xy")
    plot_xy.basis = "xy"
    plot_xy.origin = (center_x, center_y, dims["FILL_Z_TOP_CM"] / 2.0)
    plot_xy.width = (width_x * 1.05, width_y * 1.05)
    plot_xy.pixels = (1600, 1200)
    plot_xy.color_by = "material"
    plot_xy.colors = colors
    plots.append(plot_xy)

    # XZ vertical cross-section through pipes
    plot_xz = openmc.Plot(name="xz")
    plot_xz.basis = "xz"
    plot_xz.origin = (center_x, 0.0, (dims["Z_MIN_CM"] + dims["Z_MAX_CM"]) / 2.0)
    plot_xz.width = (width_x * 1.05, dims["PIPE_HEIGHT_CM"] * 1.1)
    plot_xz.pixels = (1600, 1000)
    plot_xz.color_by = "material"
    plot_xz.colors = colors
    plots.append(plot_xz)

    legend = get_color_legend(materials)
    return plots, legend
