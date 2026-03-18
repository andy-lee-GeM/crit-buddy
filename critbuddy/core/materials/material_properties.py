"""
Derived material properties and composition conversions for OpenMC materials.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

import openmc
from openmc.data import atomic_mass, atomic_weight


AVOGADRO = 6.02214076e23
ATOMS_PER_CM3_TO_ATOMS_PER_BARN_CM = 1.0e-24
ATOMS_PER_BARN_CM_TO_ATOMS_PER_CM3 = 1.0e24


@dataclass(frozen=True)
class MaterialNuclideSummary:
    """Resolved density and fraction data for one nuclide."""

    nuclide: str
    atomic_mass_g_mol: float
    atom_density_bcm: float
    mass_density_g_cm3: float
    atom_fraction: float
    weight_fraction: float


@dataclass(frozen=True)
class MaterialSummary:
    """Resolved composition summary for an OpenMC material."""

    name: str
    density_g_cm3: float
    total_atom_density_bcm: float
    nuclides: list[MaterialNuclideSummary]


def normalize_fractions(values: Mapping[str, float]) -> dict[str, float]:
    """Normalize a mapping of positive values to fractions that sum to 1.0."""
    total = sum(values.values())
    if total <= 0.0:
        raise ValueError("Cannot normalize empty or zero-sum values")
    return {name: value / total for name, value in values.items()}


def get_atomic_masses(nuclides: Mapping[str, float]) -> dict[str, float]:
    """Look up g/mol masses for nuclide or element keys."""
    return {nuclide: species_mass_g_mol(nuclide) for nuclide in nuclides}


def _is_nuclide_species(name: str) -> bool:
    """Return True when the species key names a specific nuclide."""
    return any(char.isdigit() for char in name)


def species_mass_g_mol(name: str) -> float:
    """Return g/mol mass for either a nuclide key or an element key.

    Nuclides are specific isotopes like Fe56, U235, or O16.
    Elements are symbols like Fe, O, or AL with no isotope attached.
    """
    if _is_nuclide_species(name):
        return atomic_mass(name)
    return atomic_weight(name)


def weight_to_atom_fractions(weight_fractions: Mapping[str, float]) -> dict[str, float]:
    """Convert normalized or relative weight fractions to atom fractions."""
    masses = get_atomic_masses(weight_fractions)
    relative_atoms = {
        nuclide: weight / masses[nuclide]
        for nuclide, weight in weight_fractions.items()
    }
    return normalize_fractions(relative_atoms)


def atom_to_weight_fractions(atom_fractions: Mapping[str, float]) -> dict[str, float]:
    """Convert normalized or relative atom fractions to weight fractions."""
    masses = get_atomic_masses(atom_fractions)
    relative_mass = {
        nuclide: atoms * masses[nuclide]
        for nuclide, atoms in atom_fractions.items()
    }
    return normalize_fractions(relative_mass)


def average_atomic_mass(atom_fractions: Mapping[str, float]) -> float:
    """Compute the average atomic mass for a normalized atom-fraction mixture."""
    normalized = normalize_fractions(atom_fractions)
    masses = get_atomic_masses(normalized)
    return sum(normalized[nuclide] * masses[nuclide] for nuclide in normalized)


def atom_fractions_to_atom_densities(
    atom_fractions: Mapping[str, float],
    density_g_cm3: float,
) -> dict[str, float]:
    """Convert atom fractions and bulk density into atom densities in atoms/b-cm."""
    normalized = normalize_fractions(atom_fractions)
    avg_mass = average_atomic_mass(normalized)
    total_atom_density_cm3 = density_g_cm3 * AVOGADRO / avg_mass
    total_atom_density_bcm = total_atom_density_cm3 * ATOMS_PER_CM3_TO_ATOMS_PER_BARN_CM
    return {
        nuclide: fraction * total_atom_density_bcm
        for nuclide, fraction in normalized.items()
    }


def weight_fractions_to_atom_densities(
    weight_fractions: Mapping[str, float],
    density_g_cm3: float,
) -> dict[str, float]:
    """Convert weight fractions and bulk density into atom densities in atoms/b-cm."""
    normalized = normalize_fractions(weight_fractions)
    masses = get_atomic_masses(normalized)
    return {
        nuclide: density_g_cm3
        * weight_fraction
        * AVOGADRO
        / masses[nuclide]
        * ATOMS_PER_CM3_TO_ATOMS_PER_BARN_CM
        for nuclide, weight_fraction in normalized.items()
    }


def atom_densities_to_atom_fractions(
    atom_densities_bcm: Mapping[str, float],
) -> dict[str, float]:
    """Convert atom densities in atoms/b-cm to normalized atom fractions."""
    return normalize_fractions(atom_densities_bcm)


def atom_densities_to_mass_densities(
    atom_densities_bcm: Mapping[str, float],
) -> dict[str, float]:
    """Convert atom densities in atoms/b-cm to per-nuclide mass densities in g/cm3."""
    masses = get_atomic_masses(atom_densities_bcm)
    return {
        nuclide: atom_density
        * ATOMS_PER_BARN_CM_TO_ATOMS_PER_CM3
        * masses[nuclide]
        / AVOGADRO
        for nuclide, atom_density in atom_densities_bcm.items()
    }


def atom_densities_to_weight_fractions(
    atom_densities_bcm: Mapping[str, float],
) -> dict[str, float]:
    """Convert atom densities in atoms/b-cm to normalized weight fractions."""
    mass_densities = atom_densities_to_mass_densities(atom_densities_bcm)
    return normalize_fractions(mass_densities)


def summarize_openmc_material(mat: openmc.Material) -> MaterialSummary:
    """Generate a resolved nuclide-level summary for an OpenMC material."""
    atom_densities = dict(mat.get_nuclide_atom_densities())
    density_g_cm3 = mat.get_mass_density()
    total_atom_density_bcm = sum(atom_densities.values())

    atom_fractions = atom_densities_to_atom_fractions(atom_densities)
    weight_fractions = atom_densities_to_weight_fractions(atom_densities)
    mass_densities = atom_densities_to_mass_densities(atom_densities)
    masses = get_atomic_masses(atom_densities)

    rows = [
        MaterialNuclideSummary(
            nuclide=nuclide,
            atomic_mass_g_mol=masses[nuclide],
            atom_density_bcm=atom_densities[nuclide],
            mass_density_g_cm3=mass_densities[nuclide],
            atom_fraction=atom_fractions[nuclide],
            weight_fraction=weight_fractions[nuclide],
        )
        for nuclide in atom_densities
    ]

    rows.sort(key=lambda row: row.nuclide)

    return MaterialSummary(
        name=mat.name,
        density_g_cm3=density_g_cm3,
        total_atom_density_bcm=total_atom_density_bcm,
        nuclides=rows,
    )
