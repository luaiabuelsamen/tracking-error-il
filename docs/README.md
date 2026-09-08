# docs/

| document | contents |
|---|---|
| `simulation.md` | the MuJoCo benchmark: what is recorded, domain randomisation, the three scripted experts and what the gaps between them measure, the resolution cliff |
| `hardware/preregistration_2026-09-04_residual.md` | frozen decision rule for the first paired hardware comparison (position only vs compensated residual) |
| `hardware/preregistration_2026-09-05_tracking_error.md` | frozen decision rule for the seed-0 tracking-error comparison, written before training or evaluation |
| `hardware/replication_plan_2026-09-05.md` | plan for seeds 1 and 2, written after seed 0 and before those seeds were trained |
| `hardware/preregistration_2026-09-07_history_control.md` | frozen plan for the matched position-history control: checkpoints, comparisons, decision rule; written before training |
| `hardware/diagnostics.md` | seed-0 paired result and trajectory audit; trial-level record of the seed-1 and seed-2 interruptions |

The pre-registration documents are kept as written, including their internal
checkpoint names. Provenance: the replication plan's hash is recorded in
`results/hardware/real_delta_replication/manifest.json` before the seed-1 and
seed-2 sessions; the 2026-09-04 and 2026-09-07 documents were committed before
their sessions (git history); the 2026-09-05 document has no timestamped
artifact that precedes its session and rests on the author's statement.
