#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.."
seed="${1:-1}"
if [[ $# -gt 0 ]]; then shift; fi
case "$seed" in
  1|2) ;;
  *) echo "Usage: bash scripts/bench/run_hw_replication.sh [1|2]" >&2; exit 1 ;;
esac
exec "${SO101_VENV_PYTHON:-python}" scripts/real/trial_runner.py \
  --arms "base_s${seed},delta_s${seed}" --paired --trials 40 \
  --jumpstart 115 --max-steps 400 \
  --out "results/hardware/real_delta_v3_s${seed}_trials.json" "$@"
