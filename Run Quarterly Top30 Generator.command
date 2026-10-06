#!/bin/bash
cd "$(dirname "$0")"
echo "M1_B2_QUALITY_VETO_N30 — Quarterly Top 30 Generator"
echo ""

# Use project virtual environment
PYTHON=""
if [ -f ".venv/bin/python3" ]; then
    PYTHON=".venv/bin/python3"
    echo "Using: .venv Python"
elif [ -f ".venv/bin/python" ]; then
    PYTHON=".venv/bin/python"
elif command -v python3 &>/dev/null; then
    PYTHON="python3"
elif command -v python &>/dev/null; then
    PYTHON="python"
fi

if [ -z "$PYTHON" ]; then
    echo "ERROR: Python not found. Set up the project virtual environment first."
    read -p "Press Enter to close..."
    exit 1
fi

echo "Python: $($PYTHON --version 2>&1)"
echo ""

# Ask for as_of_date
read -p "Enter quarter-end date [2026-06-30]: " AS_OF
AS_OF="${AS_OF:-2026-06-30}"

echo ""
echo "============================================================"
echo "QUICK RUN (--skip-fresh): reuses the newest pulled snapshot."
echo "  Valid only if that snapshot is fresh for your as_of date."
echo "  It will HARD STOP if the snapshot is stale for a new quarter."
echo "  Runs in seconds."
echo ""
echo "FULL RUN: pulls fresh market data for a new quarter-end."
echo "  Takes 1-2 hours. Required for a new quarter."
echo ""
echo "  To use the full run, open this file in a text editor:"
echo "    comment line A, uncomment line B below."
echo ""
echo "  A) $PYTHON scripts/run_quarterly_top30_generator.py --as-of \"\$AS_OF\" --skip-fresh"
echo "  B) $PYTHON scripts/run_quarterly_top30_generator.py --as-of \"\$AS_OF\""
echo ""
echo "============================================================"
echo ""
echo "To load in app: use the latest Vercel Preview URL"
echo "  Top 30 -> Load Notebook-Generated Top 30"
echo "  Select m1_b2_quality_veto_targets.csv from output folder"
echo ""

$PYTHON scripts/run_quarterly_top30_generator.py --as-of "$AS_OF" --skip-fresh
# $PYTHON scripts/run_quarterly_top30_generator.py --as-of "$AS_OF"

echo ""
echo "Done. Press Enter to close."
read
