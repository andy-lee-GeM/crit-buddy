#!/usr/bin/env bash
set -euo pipefail

source /home/gem/.local/miniforge3/etc/profile.d/conda.sh
conda activate openmc-env

cd /home/gem/Projects/crit-buddy
python scripts/steven_film_openmc.py --output-dir reports/steven-film-review/runs/steven_film_openmc
