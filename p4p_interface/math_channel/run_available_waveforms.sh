#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
VENV_ACTIVATE="$REPO_ROOT/.venv/bin/activate"

if [[ ! -f "$VENV_ACTIVATE" ]]; then
  echo "Virtualenv not found at $VENV_ACTIVATE" >&2
  echo "Create it first with: python3 -m venv .venv" >&2
  exit 1
fi

source "$VENV_ACTIVATE"
cd "$REPO_ROOT"

echo "[1/3] Listing available TekHSI sources..."
python p4p_interface/math_channel/list_available_names.py

echo
echo "[2/3] Regenerating Phoebus display..."
python p4p_interface/math_channel/generate_available_waveform_xyplot_client.py

echo
echo "[3/3] Starting P4P server..."
echo "Open p4p_interface/math_channel/available_waveform_xyplot_client.bob in Phoebus."
exec python p4p_interface/math_channel/publish_available_waveforms_server.py
