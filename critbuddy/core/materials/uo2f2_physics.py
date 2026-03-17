"""
UO2F2 physical-property helpers derived from ORNL/TM-12292, Appendix A.

The implementation uses the uranium-compound density relationship from Eq. (A.1)
and the uranyl-fluoride-specific piecewise fit discussed in Appendix A for the
low-H/U hydrated-salt region. Callers provide enrichment and H/U; the module
computes uranium density first and then converts it to bulk mixture density
using the requested UO2F2-H2O stoichiometry.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IsotopicMasses:
    """Atomic or molecular masses used by the density model."""

    u235_g_per_mol: float = 235.044
    u238_g_per_mol: float = 238.051
    o16_g_per_mol: float = 15.999
    f19_g_per_mol: float = 18.998403163
    h2o_g_per_mol: float = 18.015


@dataclass(frozen=True)
class UranylFluorideModel:
    """Constants for the Appendix A uranyl-fluoride density relationship."""

    u_atoms_per_formula_unit: float = 1.0
    h_atoms_per_water: float = 2.0
    waters_of_hydration: float = 2.0
    hydrated_salt_branch_limit_h_over_u: float = 4.0
    hydrated_salt_intercept_g_cm3: float = 4.96
    hydrated_salt_slope_g_cm3_per_h_over_u: float = 0.32
    uo2f2_dihydrate_molar_volume_cm3_per_mol: float = 72.2809
    h2o_molar_volume_cm3_per_mol: float = 18.0574


ATOMIC_MASSES = IsotopicMasses()
UO2F2_MODEL = UranylFluorideModel()


@dataclass(frozen=True)
class UO2F2Stoichiometry:
    """Derived chemistry properties for one requested enrichment/H/U case."""

    enrichment_pct: float
    h_to_u: float
    water_moles_per_u: float
    uo2f2_weight_fraction: float
    molar_mass_g_per_mol: float
    molar_volume_cm3_per_mol: float
    density_g_cm3: float
    oxygen_atoms_per_u: float
    fluorine_atoms_per_u: float
    hydrogen_atoms_per_u: float
    water_weight_fraction: float


def _uranium_atom_fractions(enrichment_pct: float) -> tuple[float, float]:
    """Convert U-235 weight percent to uranium atom fractions."""
    w235 = enrichment_pct / 100.0
    w238 = 1.0 - w235

    n235 = w235 / ATOMIC_MASSES.u235_g_per_mol
    n238 = w238 / ATOMIC_MASSES.u238_g_per_mol
    total = n235 + n238

    return n235 / total, n238 / total


def _uranium_molar_mass(enrichment_pct: float) -> float:
    """Return the average uranium molar mass for the requested enrichment."""
    x235, x238 = _uranium_atom_fractions(enrichment_pct)
    return (
        x235 * ATOMIC_MASSES.u235_g_per_mol
        + x238 * ATOMIC_MASSES.u238_g_per_mol
    )


def uranium_density(
    Mu: float,
    Vuc: float,
    N: float,
    H_over_U: float,
    M: float,
    Y: float,
    Vm: float,
) -> float:
    """
    Calculate uranium density in a homogeneous mixture from ORNL/TM-12292 Eq. (A.1).
    """
    specific_uc = Vuc / N
    specific_m = Vm / M
    denominator = specific_uc + (H_over_U - M * Y) * specific_m
    return Mu / denominator


def uranyl_fluoride_density(
    H_over_U: float,
    Mu: float,
    V_uc: float = UO2F2_MODEL.uo2f2_dihydrate_molar_volume_cm3_per_mol,
    V_H2O: float = UO2F2_MODEL.h2o_molar_volume_cm3_per_mol,
) -> float:
    """
    Return uranium density for uranyl-fluoride mixtures.

    For H/U below 4, use the Appendix A hydrated-salt linear fit.
    For H/U of 4 and above, use the ORNL/TM-12292 Eq. (A.1) aqueous-solution
    form with the UO2F2·2H2O and H2O molar volumes captured in ``UO2F2_MODEL``.
    """
    if H_over_U < UO2F2_MODEL.hydrated_salt_branch_limit_h_over_u:
        return (
            UO2F2_MODEL.hydrated_salt_intercept_g_cm3
            - UO2F2_MODEL.hydrated_salt_slope_g_cm3_per_h_over_u * H_over_U
        )

    return uranium_density(
        Mu=Mu,
        Vuc=V_uc,
        N=UO2F2_MODEL.u_atoms_per_formula_unit,
        H_over_U=H_over_U,
        M=UO2F2_MODEL.h_atoms_per_water,
        Y=UO2F2_MODEL.waters_of_hydration,
        Vm=V_H2O,
    )


def _uo2f2_molar_mass(mu: float) -> float:
    """Return the molar mass of dry UO2F2 for one mole of uranium."""
    return mu + 2.0 * ATOMIC_MASSES.o16_g_per_mol + 2.0 * ATOMIC_MASSES.f19_g_per_mol


def uo2f2_density(h_to_u: float = 0.0, enrichment_pct: float = 20.0) -> float:
    """
    Return bulk UO2F2 mixture density for a requested enrichment and H/U.
    """
    if h_to_u < 0.0:
        raise ValueError("H/U ratio must be non-negative")
    if enrichment_pct <= 0.0:
        raise ValueError("Enrichment must be positive")

    mu = _uranium_molar_mass(enrichment_pct)
    rho_u = uranyl_fluoride_density(h_to_u, mu)
    total_mass = _uo2f2_molar_mass(mu) + (
        h_to_u / UO2F2_MODEL.h_atoms_per_water
    ) * ATOMIC_MASSES.h2o_g_per_mol

    return rho_u * total_mass / mu


def uo2f2_stoichiometry(
    h_to_u: float = 0.0,
    enrichment_pct: float = 20.0,
) -> UO2F2Stoichiometry:
    """Calculate UO2F2 mixture properties from enrichment and H/U."""
    if h_to_u < 0.0:
        raise ValueError("H/U ratio must be non-negative")
    if enrichment_pct <= 0.0:
        raise ValueError("Enrichment must be positive")

    mu = _uranium_molar_mass(enrichment_pct)
    n_water = h_to_u / UO2F2_MODEL.h_atoms_per_water
    dry_uo2f2_mass = _uo2f2_molar_mass(mu)
    total_mass = dry_uo2f2_mass + n_water * ATOMIC_MASSES.h2o_g_per_mol
    water_mass = n_water * ATOMIC_MASSES.h2o_g_per_mol
    density = uo2f2_density(h_to_u, enrichment_pct=enrichment_pct)
    total_volume = total_mass / density if density > 0.0 else 0.0

    return UO2F2Stoichiometry(
        enrichment_pct=enrichment_pct,
        h_to_u=h_to_u,
        water_moles_per_u=n_water,
        uo2f2_weight_fraction=dry_uo2f2_mass / total_mass if total_mass > 0.0 else 0.0,
        molar_mass_g_per_mol=total_mass,
        molar_volume_cm3_per_mol=total_volume,
        density_g_cm3=density,
        oxygen_atoms_per_u=2.0 + n_water,
        fluorine_atoms_per_u=2.0,
        hydrogen_atoms_per_u=h_to_u,
        water_weight_fraction=water_mass / total_mass if total_mass > 0.0 else 0.0,
    )
