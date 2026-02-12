"""
MCNP model for single cylinder criticality problem.

Generates material cards using the shared materials library.
"""

from critbuddy.core.materials import mcnp_uf6, get_material


def build_materials(p: dict) -> str:
    """
    Build MCNP material cards for single cylinder problem.

    Args:
        p: Parameters dict with ENRICHMENT, UF6_DENSITY, WALL_MATERIAL, REFLECTOR_MATERIAL

    Returns:
        MCNP material card block as string
    """
    materials = []

    # Material 1: UF6
    materials.append(mcnp_uf6(1, p["ENRICHMENT"], density=p["UF6_DENSITY"]))

    # Material 2: Wall (from registry if available)
    wall_mat = p.get("WALL_MATERIAL", "aluminum")
    materials.append(get_material(wall_mat, solver="mcnp", mat_num=2))

    # Material 3: Reflector (from registry if available)
    refl_mat = p.get("REFLECTOR_MATERIAL", "water")
    if refl_mat != "none":
        materials.append(get_material(refl_mat, solver="mcnp", mat_num=3))

    return "".join(materials)
