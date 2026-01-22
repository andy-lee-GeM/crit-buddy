"""
Shared utilities for crit-buddy.

Provides:
- Logging configuration
- Working directory context manager
- Status enum for solver results
"""

import logging
import os
import sys
from contextlib import contextmanager
from enum import Enum
from pathlib import Path


# =============================================================================
# STATUS ENUM
# =============================================================================

class Status(Enum):
    """Solver result status codes."""

    SAFE = "SAFE"           # k_eff + 2*sigma < safety_limit
    MARGINAL = "MARGINAL"   # k_eff < safety_limit but k_eff + 2*sigma >= safety_limit
    CRITICAL = "CRITICAL"   # k_eff >= safety_limit
    FAILED = "FAILED"       # Solver execution failed
    SKIPPED = "SKIPPED"     # Solver not available or skipped


# =============================================================================
# WORKING DIRECTORY CONTEXT MANAGER
# =============================================================================

@contextmanager
def working_directory(path: Path):
    """
    Context manager for temporarily changing working directory.

    Safely changes to the specified directory and restores the original
    directory on exit, even if an exception occurs.

    Args:
        path: Directory to change to

    Example:
        with working_directory(case_dir):
            openmc.run()
        # Back to original directory
    """
    original = Path.cwd()
    try:
        os.chdir(path)
        yield path
    finally:
        os.chdir(original)


# =============================================================================
# LOGGING
# =============================================================================

def setup_logging(verbose: bool = False, quiet: bool = False) -> logging.Logger:
    """
    Configure logging for crit-buddy.

    Args:
        verbose: If True, set DEBUG level
        quiet: If True, set WARNING level (overrides verbose)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger("critbuddy")

    # Determine log level
    if quiet:
        level = logging.WARNING
    elif verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO

    logger.setLevel(level)

    # Only add handler if none exist (avoid duplicates)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)

        # Format: simple for INFO, detailed for DEBUG
        if level == logging.DEBUG:
            fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        else:
            fmt = "%(message)s"

        handler.setFormatter(logging.Formatter(fmt))
        logger.addHandler(handler)

    return logger


def get_logger(name: str = "critbuddy") -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)
