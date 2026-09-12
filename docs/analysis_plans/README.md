# Analysis-plan provenance

These are unedited historical plans recovered from repository history on
2026-09-09. Their predictions and preliminary interpretations are historical,
not conclusions of the current manuscript. Paths refer to the old layout.

| Archived file | Source | What was already known |
|---|---|---|
| `2026-08-16_corpus.md` | `7b7a818`, `docs/phase3.md`, 2026-08-16 | Written before the corpus run; includes operational definitions, the directional prediction, and secondary pooled AUC. |
| `2026-08-17_simulation.md` | `d4077d5`, `docs/task2_arms.md`, 2026-08-17 | Three tracking-error results already existed. New auxiliary-target, residual and token definitions were fixed before their implementations. |

The simulation plan specifies approximately 15 percentage points at three
seeds. It does not specify the later `15 * sqrt(3/n)` extrapolation, the
position-history control, or Welch tests with Holm adjustment across all
pairs. Those are retrospective analyses. Its directional predictions concern
the new designs versus action history, not every design versus position only.

The corpus code averages eight frames `[T, T+8)`, resolving the plan's
ambiguous interval notation. Eligible episodes each have a detected closure,
so the implementation's median closure count of at most one matches the
plan's single-grasp gate. The proxy labels gripper retention and transport;
it has not been validated against independent object outcomes.

Hardware plans remain in `../hardware/`. The replication plan requests the
equal-weight mean over all three seeds. The manuscript now reports that
descriptive mean (28.3 points, including the interrupted seed's observed zero)
as well as the completed-seed mean (42.5 points), with their different
denominators and limitations. The stratified hardware test is post hoc.

The anonymous review artifact omits this provenance index's source hashes
and retains the dated plan contents. The public repository keeps the source
mapping above so the recovery can be checked with `git show`.
