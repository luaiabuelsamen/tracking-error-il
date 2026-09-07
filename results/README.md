# results/

Frozen records. Nothing here is edited by hand; the paper's tables and figures
are regenerated from these files by `scripts/paper/`.

## simulation/

`grid_<letter>_<arm>_s<seed>.json`: one trained policy per file, evaluated on
100 shared-seed episodes with the crush threshold disabled (`crush: -1`).
The letter-to-design mapping is in `scripts/README.md`. `grid600_*` are the
600-demonstration screen saved at 26,000 steps; `h100_eval.json` is the
earlier 600-demonstration comparison at 224 pixels and 50,000 steps;
`crush_*` are the post-hoc crush-tier screen; `guard_ab.json` is the runtime
guard comparison; `resolution_sweep.json` is the scripted-expert quantum sweep.

## hardware/

| file | contents |
|---|---|
| `real_delta_v3_trials.json` | seed 0: 40 rollouts, 20 pairs, `base_v2` vs `delta_v3` |
| `real_delta_v3_s1_trials.json` | seed 1: 40 rollouts, 20 pairs |
| `real_delta_v3_s2_trials.json` | seed 2: 12 labeled rollouts, 6 pairs, interrupted |
| `real_delta_v3_s2_trials_pending.json` | the thirteenth seed-2 rollout, completed but never labeled |
| `real_trial_traj/*.npz` | per-rollout trajectories: `pos`, `action` (requested), `applied_action` (after the limiter), `observation_state`, `elapsed_s` |
| `*_manifest.json`, `*_incident.json` | session arguments and hashes at recording time; shutdown incidents |
| `real_delta_v3_*summary.json`, `real_delta_v3_diagnostics.json` | paired counts and the seed-0 trajectory diagnostics |
| `real_observation_audit.json` | offline replay check of training and inference state vectors |
| `real_trials.json` | the earlier position-only vs compensated-residual comparison (2026-09-04 and 05 sessions) |
| `real_delta_replication/` | training logs and the pre-evaluation hash manifest for seeds 1 and 2 |

Each trial row records `session`, `trial`, `pair`, `arm`, `checkpoint`,
`success` (operator-entered), `jumpstart` (replayed commands) and `traj`
(path relative to this directory). Seeds 1 and 2 add `shutdown_error`,
`recovered_outcome` and `trajectory_missing`.

## corpus/

`corpus_delta_outcome.json`: per-dataset rows with `episodes`, `success_rate`,
`cohen_d`, `d_ci` and the medians behind them; rows without `cohen_d` failed
an inclusion gate and carry the reason. `offset_sweep.json`: `cohen_d_by_k`
for assumed command offsets $k=0..5$.

## calibration/

`staircase_channel_j2.npz`: twelve hanging masses at five poses on one
shoulder-lift servo, with `Present_Load`, `Present_Current`, position and goal
logged together.

## showcase/

Trajectory records of the showcase rollouts featured in `media/`. Videos are
not tracked except the one under `media/`.
