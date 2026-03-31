"""OpenMC to MCNP material conversion.

This module provides the MCNPMaterial class for converting OpenMC materials
to MCNP format with all necessary densities, ZAIDs, and fractions.

Example:
    >>> from critbuddy.core.materials.builders import water
    >>> from critbuddy.core.materials.mcnp_conversion import MCNPMaterial
    >>> mat = water()
    >>> mcnp = MCNPMaterial.from_openmc(mat)
    >>> print(mcnp.cell_density_g_cm3)
    -1.0
    >>> print(mcnp.nuclides[0].zaid)
    "1001.80c"
"""

from __future__ import annotations

from dataclasses import dataclass

import openmc
from openmc.data import zam

from critbuddy.core.materials.material_properties import (
    MaterialNuclideSummary,
    summarize_openmc_material,
)


@dataclass(frozen=True)
class MCNPNuclide:
    """MCNP data for a single nuclide within a material.

    Contains all information needed for MCNP material cards.

    Attributes:
        nuclide: OpenMC nuclide name (e.g., "U235", "H1")
        zaid: MCNP ZAID identifier (e.g., "92235.80c")
        atomic_mass_g_mol: Atomic mass in g/mol
        atom_density_bcm: Atom density in atoms/barn-cm (use in MCNP material card)
        atom_fraction: Normalized atom fraction (0-1, sums to 1 across material)
        mass_density_g_cm3: Mass density contribution of this nuclide in g/cm³
        weight_fraction: Normalized weight fraction (0-1, sums to 1 across material)
    """

    nuclide: str
    zaid: str
    atomic_mass_g_mol: float
    atom_density_bcm: float
    atom_fraction: float
    mass_density_g_cm3: float
    weight_fraction: float

    def to_dict(self) -> dict:
        """Export to dictionary for serialization.

        Returns:
            Dictionary with all nuclide data
        """
        return {
            "nuclide": self.nuclide,
            "zaid": self.zaid,
            "atomic_mass_g_mol": self.atomic_mass_g_mol,
            "atom_density_bcm": self.atom_density_bcm,
            "atom_fraction": self.atom_fraction,
            "mass_density_g_cm3": self.mass_density_g_cm3,
            "weight_fraction": self.weight_fraction,
        }


@dataclass(frozen=True)
class MCNPMaterial:
    """Complete MCNP representation of an OpenMC material.

    This class encapsulates all conversions from OpenMC to MCNP format.
    Create using the factory method: MCNPMaterial.from_openmc(material)

    Attributes:
        name: Material name from OpenMC
        bulk_density_g_cm3: Total bulk density in g/cm³ (positive)
        total_atom_density_bcm: Total atom density in atoms/barn-cm (positive)
        xs_suffix: Cross-section library suffix (e.g., "80c")
        nuclides: Tuple of MCNPNuclide objects

    Example:
        >>> mat = uo2f2(enrichment_pct=5.0, h_to_u=10.0, density=1.52)
        >>> mcnp = MCNPMaterial.from_openmc(mat, xs_suffix="80c")
        >>> print(mcnp.cell_density_g_cm3)
        -1.52
        >>> print(mcnp.nuclides[0].zaid)
        "92235.80c"
    """

    name: str
    bulk_density_g_cm3: float
    total_atom_density_bcm: float
    xs_suffix: str
    nuclides: tuple[MCNPNuclide, ...]

    @property
    def cell_density_g_cm3(self) -> float:
        """MCNP cell card density in g/cm³ (negative sign).

        Use in MCNP cell card: `1  1  -1.52  ...`

        Returns:
            Negative bulk density for MCNP cell card
        """
        return -self.bulk_density_g_cm3

    @property
    def cell_density_bcm(self) -> float:
        """MCNP cell card density in atoms/barn-cm (positive).

        Use in MCNP cell card: `1  1  +0.067234  ...`

        Returns:
            Total atom density for MCNP cell card
        """
        return self.total_atom_density_bcm

    @classmethod
    def from_openmc(
        cls,
        material: openmc.Material,
        xs_suffix: str = "80c",
    ) -> MCNPMaterial:
        """Create MCNPMaterial from an OpenMC material.

        This is the main entry point for converting OpenMC materials
        to MCNP format. All conversions are performed here.

        Args:
            material: OpenMC material to convert
            xs_suffix: MCNP cross-section library suffix (default: "80c")
                Common values: "80c" (ENDF/B-VIII.0), "70c" (VII.0), "31c" (VII.1)

        Returns:
            MCNPMaterial with all MCNP-ready data

        Example:
            >>> from critbuddy.core.materials.builders import water
            >>> mat = water()
            >>> mcnp = MCNPMaterial.from_openmc(mat)
            >>> print(mcnp.name)
            "Water"
        """
        # Step 1: Use existing summarize_openmc_material to get all densities/fractions
        summary = summarize_openmc_material(material)

        # Step 2: Convert each nuclide to MCNP format (add ZAID)
        nuclides = tuple(
            _convert_nuclide(nuc_summary, xs_suffix) for nuc_summary in summary.nuclides
        )

        # Step 3: Build MCNPMaterial
        return cls(
            name=summary.name,
            bulk_density_g_cm3=summary.density_g_cm3,
            total_atom_density_bcm=summary.total_atom_density_bcm,
            xs_suffix=xs_suffix,
            nuclides=nuclides,
        )

    def get_nuclide_by_zaid(self, zaid: str) -> MCNPNuclide | None:
        """Find nuclide by ZAID (e.g., "92235.80c").

        Args:
            zaid: MCNP ZAID identifier

        Returns:
            MCNPNuclide if found, None otherwise
        """
        for nuc in self.nuclides:
            if nuc.zaid == zaid:
                return nuc
        return None

    def get_nuclide_by_name(self, name: str) -> MCNPNuclide | None:
        """Find nuclide by OpenMC name (e.g., "U235").

        Args:
            name: OpenMC nuclide name

        Returns:
            MCNPNuclide if found, None otherwise
        """
        for nuc in self.nuclides:
            if nuc.nuclide == name:
                return nuc
        return None

    def to_dict(self) -> dict:
        """Export to dictionary for serialization.

        Returns:
            Dictionary with all material data including nuclides
        """
        return {
            "name": self.name,
            "bulk_density_g_cm3": self.bulk_density_g_cm3,
            "total_atom_density_bcm": self.total_atom_density_bcm,
            "cell_density_g_cm3": self.cell_density_g_cm3,
            "cell_density_bcm": self.cell_density_bcm,
            "xs_suffix": self.xs_suffix,
            "nuclides": [nuc.to_dict() for nuc in self.nuclides],
        }


# ============================================================================
# Internal Helpers
# ============================================================================


def _convert_nuclide(
    nuc_summary: MaterialNuclideSummary,
    xs_suffix: str,
) -> MCNPNuclide:
    """Convert MaterialNuclideSummary to MCNPNuclide (internal helper).

    Args:
        nuc_summary: OpenMC nuclide summary with densities and fractions
        xs_suffix: MCNP cross-section suffix

    Returns:
        MCNPNuclide with ZAID added
    """
    zaid = _to_zaid(nuc_summary.nuclide, xs_suffix)

    return MCNPNuclide(
        nuclide=nuc_summary.nuclide,
        zaid=zaid,
        atomic_mass_g_mol=nuc_summary.atomic_mass_g_mol,
        atom_density_bcm=nuc_summary.atom_density_bcm,
        atom_fraction=nuc_summary.atom_fraction,
        mass_density_g_cm3=nuc_summary.mass_density_g_cm3,
        weight_fraction=nuc_summary.weight_fraction,
    )


def _to_zaid(nuclide: str, xs_suffix: str) -> str:
    """Convert OpenMC nuclide name to MCNP ZAID format.

    ZAID format: ZZZAAA.xxc where ZZZ is atomic number, AAA is mass number,
    and xxc is the cross-section library suffix.

    Args:
        nuclide: OpenMC nuclide name (e.g., "U235", "H1", "O16")
        xs_suffix: MCNP cross-section library suffix (e.g., "80c")

    Returns:
        MCNP ZAID string (e.g., "92235.80c")

    Raises:
        ValueError: If nuclide is in a metastable state (not supported by MCNP ZAID)

    Examples:
        >>> _to_zaid("U235", "80c")
        "92235.80c"
        >>> _to_zaid("H1", "70c")
        "1001.70c"
        >>> _to_zaid("O16", "80c")
        "8016.80c"
    """
    z, a, m = zam(nuclide)
    if m != 0:
        raise ValueError(
            f"Metastable nuclide '{nuclide}' not supported for MCNP ZAID. "
            f"MCNP ZAID format does not handle metastable states (m={m})."
        )
    zaid_number = 1000 * z + a
    return f"{zaid_number}.{xs_suffix}"
