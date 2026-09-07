#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
exec /home/jetson3/projects/clean_env/venv/bin/python scripts/trial_runner.py \
  --arms base_v2,delta_v3 --paired --trials 40 \
  --jumpstart 115 --max-steps 400 \
  --out results/real_delta_v3_trials.json
