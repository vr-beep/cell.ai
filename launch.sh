#!/bin/bash
# Cell.ai Closed Loop Launcher
set -e

cd "$(dirname "$0")"

# Load environment
set -a
source .env 2>/dev/null || true
set +a

export SIMULATION_MODE=1
export AUTO_APPROVE=1

PLATE_ID="${1:-PLT145RIEW6K4ZTEUG4OOFQJQAXHL4}"

echo "🧫 Cell.ai Closed Loop"
echo "   Plate: $PLATE_ID"
echo "   Mode: simulation"
echo ""

source .venv/bin/activate

cd POC/closed-loop
python scripts/orchestrator.py --plate-id "$PLATE_ID" --auto-approve
