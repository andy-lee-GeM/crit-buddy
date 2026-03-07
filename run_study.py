#!/usr/bin/env python3
"""
Crit-buddy entry point.

Usage:
    python run_study.py <experiment.yaml>
    python run_study.py <experiment.yaml> --solver openmc
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from critbuddy.runner import main

if __name__ == "__main__":
    main()
