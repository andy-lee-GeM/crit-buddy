"""
MCNP output parser for crit-buddy.

Extracts k-effective, uncertainty, warnings, and fatal errors from MCNP output.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List


@dataclass
class ParsedMCNPOutput:
    """Parsed results from MCNP output file."""

    keff: Optional[float] = None
    uncertainty: Optional[float] = None
    warnings: List[str] = field(default_factory=list)
    fatal_errors: List[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        """True if k-effective was successfully extracted."""
        return self.keff is not None


class MCNPOutputParser:
    """
    Parser for MCNP output files.

    Example:
        parser = MCNPOutputParser()
        result = parser.parse(Path("inputo"))
        if result.success:
            print(f"k-eff = {result.keff} +/- {result.uncertainty}")
    """

    def parse(self, output_path: Path) -> ParsedMCNPOutput:
        """
        Parse MCNP output file and extract results.

        Args:
            output_path: Path to MCNP output file

        Returns:
            ParsedMCNPOutput with keff, uncertainty, warnings, errors
        """
        output_path = Path(output_path)

        if not output_path.exists():
            return ParsedMCNPOutput(
                fatal_errors=[f"Output file not found: {output_path}"]
            )

        try:
            content = output_path.read_text(errors='ignore')
        except Exception as e:
            return ParsedMCNPOutput(
                fatal_errors=[f"Failed to read output: {e}"]
            )

        warnings = self._extract_warnings(content)
        fatal_errors = self._extract_fatal_errors(content)
        keff, uncertainty = self._parse_keff(content)

        return ParsedMCNPOutput(
            keff=keff,
            uncertainty=uncertainty,
            warnings=warnings,
            fatal_errors=fatal_errors,
        )

    def _parse_keff(self, content: str) -> tuple[Optional[float], Optional[float]]:
        """
        Parse k-effective using regex patterns.

        Returns:
            Tuple of (keff, uncertainty) or (None, None) on failure
        """
        patterns = [
            # Standard format: "final result     0.99234  0.00123"
            r'final\s+result\s+(\d+\.?\d*)\s+(\d+\.?\d*)',
            # Alternative spacing
            r'final result\s+(\d+\.?\d*)\s+(\d+\.?\d*)',
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                try:
                    keff = float(match.group(1))
                    uncertainty = float(match.group(2))
                    return keff, uncertainty
                except (ValueError, IndexError):
                    continue

        # Fallback: Parse from cycle-by-cycle table (last line with combined k(c/a/t))
        # Format: "15  993 | ... |  0.37587 0.00562  13345"
        # The combined k-eff and std dev appear after the last "|" before FOM
        cycle_pattern = r'\|\s+(\d+\.\d+)\s+(\d+\.\d+)\s+\d+\s*$'
        matches = list(re.finditer(cycle_pattern, content, re.MULTILINE))
        if matches:
            last_match = matches[-1]
            try:
                keff = float(last_match.group(1))
                uncertainty = float(last_match.group(2))
                return keff, uncertainty
            except (ValueError, IndexError):
                pass

        return None, None

    def _extract_warnings(self, content: str) -> List[str]:
        """Extract unique warning messages."""
        warnings = []
        pattern = re.compile(r'^\s*warning\.(.*)$', re.MULTILINE | re.IGNORECASE)

        for match in pattern.finditer(content):
            warning = match.group(1).strip()
            if warning and warning not in warnings and len(warning) < 200:
                warnings.append(warning)

        return warnings

    def _extract_fatal_errors(self, content: str) -> List[str]:
        """Extract fatal error and bad trouble messages."""
        errors = []
        patterns = [
            re.compile(r'^\s*fatal\s+error\.(.*)$', re.MULTILINE | re.IGNORECASE),
            re.compile(r'bad\s+trouble[.\s]+(.+?)(?:\n|$)', re.IGNORECASE),
        ]

        for pattern in patterns:
            for match in pattern.finditer(content):
                error = match.group(1).strip()
                if error and error not in errors and len(error) < 200:
                    errors.append(error)

        return errors


def parse_mcnp_output(output_path: Path) -> ParsedMCNPOutput:
    """
    Convenience function to parse MCNP output file.

    Args:
        output_path: Path to MCNP output file

    Returns:
        ParsedMCNPOutput with results
    """
    parser = MCNPOutputParser()
    return parser.parse(output_path)
