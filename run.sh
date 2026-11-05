#!/bin/sh
# Rebuild every table and figure from canton-foundation/configs.
# Usage: ./run.sh [path to a clone of canton-foundation/configs]
set -e
CONFIGS=${1:-../configs}
cd "$(dirname "$0")"
python3 src/extract.py "$CONFIGS"
python3 src/lifecycle.py
python3 src/deadlines.py > /dev/null
python3 src/dilution.py > /dev/null
python3 src/plot_weight_classes.py > /dev/null
python3 src/plot_escrow_status.py > /dev/null
python3 -m unittest discover -s tests
