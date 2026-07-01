#!/bin/bash
cd "$(dirname "$0")"
echo "M1_B2_QUALITY_VETO_N30 — Quarterly Top 30 Generator"
echo ""

# Find Python
PYTHON=""
for py in python3 python; do
    if command -v "$py" &>/dev/null; then
        PYTHON="$py"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    echo "ERROR: Python not found. Install Python 3."
    read -p "Press Enter to close..."
    exit 1
fi

echo "Using: $($PYTHON --version)"
echo ""

# Ask for as_of_date
read -p "Enter quarter-end date [2026-06-30]: " AS_OF
AS_OF="${AS_OF:-2026-06-30}"

echo ""
echo "Running generator with as_of_date=$AS_OF"
echo "This may take 1–2 hours."
echo ""

$PYTHON scripts/run_quarterly_top30_generator.py --as-of "$AS_OF"

echo ""
echo "Done. Press Enter to close."
read
