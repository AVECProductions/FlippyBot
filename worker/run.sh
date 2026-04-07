#!/usr/bin/env bash
# FLIPPY Worker — Unix launcher
# Run from the worker/ directory or from repo root.

set -e
cd "$(dirname "$0")"

# Activate venv if present
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# Default: continuous mode, 30-minute interval
# Pass --once for a single run, --interval N to change interval.
python main.py "$@"
