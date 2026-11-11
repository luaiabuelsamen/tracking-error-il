# docs/

| document | contents |
|---|---|
| `simulation.md` | the MuJoCo benchmark: what is recorded, domain randomisation, the three scripted experts and what the gaps between them measure, the resolution cliff |
| `hardware/preregistration_2026-09-04_residual.md` | frozen decision rule for the first paired hardware comparison (position only vs compensated residual) |
| `hardware/preregistration_2026-09-05_tracking_error.md` | frozen decision rule for the seed-0 tracking-error comparison, written before training or evaluation |
| `hardware/replication_plan_2026-09-05.md` | plan for seeds 1 and 2, written after seed 0 and before those seeds were trained |
| `hardware/preregistration_2026-09-07_history_control.md` | frozen plan for the matched position-history control: checkpoints, comparisons, decision rule; written before training |
| `reviews/corl2026_webp.md` | CoRL 2026 WEBP reviews (digest until the verbatim text is pasted) and the numbered list of requested changes that `revision_2026-11.md` works through |
| `revision_2026-11.md` | November 2026 revision plan: arXiv v1 text fixes, then the two hardware items, then arXiv v2 |
| `hardware/preregistration_2026-11_seed_replication.md` | frozen plan for a third completed seed (seed 3), written before training; decision not to continue seed 2 |
| `hardware/preregistration_2026-11_grasp_bit.md` | frozen plan for the binary grasp-state input on hardware: bit definition, two checkpoints, two paired comparisons, decision rules; written before training |
| `hardware/history_control_addendum_2026-11.md` | pooling decision for the position-history control: the nine interrupted pairs stay separate, the confirmatory session is a fresh 20 pairs |
| `hardware/overload_diagnosis_2026-11.md` | the recurring gripper overload: configuration read from the code, the diagnostic procedure, candidates, findings (bench) |
| `hardware/diagnostics.md` | seed-0 paired result and trajectory audit; trial-level record of the seed-1 and seed-2 interruptions |
| `analysis_plans/2026-08-16_corpus.md` | original corpus protocol recovered unchanged from repository history, including its secondary AUC prediction |
| `analysis_plans/2026-08-17_simulation.md` | original simulation design note; three tracking-error results were already known when it was written |

The pre-registration documents are kept as written, including their internal
checkpoint names. Provenance: the replication plan's hash is recorded in
`results/hardware/real_delta_replication/manifest.json` before the seed-1 and
seed-2 sessions; the 2026-09-04 and 2026-09-07 documents were committed before
their sessions (git history); the 2026-09-05 document has no timestamped
artifact that precedes its session and rests on the author's statement.
