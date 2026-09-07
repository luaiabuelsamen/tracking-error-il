# Pre-registration: position-history control on hardware — 2026-09-07

Written before the matched position-history checkpoints were trained and
before any of them touched the arm. Committed to the repository before the
training queue started; the training logs under
`results/hardware/real_delta_replication/ghist_s*.log` record start times.

## Why

The simulation grid finds position history $[q_t, q_{t-8}]$ within 1.5
points of tracking error (20.3% vs 21.8%), so the hardware gain from tracking
error may be a gain from any temporal input. No history policy has run on the
arm. The one existing history checkpoint (`real50_ghist_s0`) was trained on
the untrimmed 21,476 frames and is not a matched control.

## Checkpoints

Train `real50_ghist_v3_s1` and `real50_ghist_v3_s0` with exactly the seed-1/2
recipe: same 50-demonstration recording, stationary-prefix trimming (18,549
frames), 96 px, 6,000 steps, batch 8, learning rate 0.0001, default ACT
architecture, final checkpoint only, `--ghist-k 8` (8 frames at 30 Hz, 0.27 s;
the simulation control used 8 frames at 15 Hz). No selection on training loss
or on hardware outcome; a checkpoint is eligible when training completes and
the offline observation audit passes.

## Comparisons

Primary: seed 1, `delta_s1` (14/20 in the completed evaluation) against
`ghist_s1`, 20 complete pairs, AB/BA order alternating, 115-command replay,
400-step horizon, same runner and limiter as the completed evaluations.
Question: does tracking error add anything beyond position history on this
task?

Secondary, if bench time allows: seed 0, `base_v2` against `ghist_s0`, same
protocol. Question: does history alone improve on the position-only base?

    bash scripts/bench/run_hw_history_control.sh 1
    bash scripts/bench/run_hw_history_control.sh 0

## Registered predictions and decision rule

From the simulation grid, the registered expectation is no resolvable
difference in the primary comparison and a history advantage in the secondary
one. Exact two-sided McNemar on the discordant pairs, $p<0.05$ with a positive
effect, is the criterion for a claimed difference; a non-significant primary
result is reported as "not distinguishable at 20 pairs", not as equivalence.
All outcomes are retained, including completed rollouts whose shutdown reports
a servo fault (labeled by the operator). The operator is not blinded.

## What this can and cannot settle

A significant tracking-error advantage over history in the primary comparison
would argue that the command carries information the position history does
not, for these two checkpoints. It would not show that the information is
contact force. A null leaves the simulation conclusion standing on hardware:
temporal information helps, its representation is unresolved.
