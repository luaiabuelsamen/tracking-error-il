# Pre-registration: a binary grasp-state input on hardware — 2026-11-10

Written before the grasp-bit checkpoints were trained and before anything in this plan touched the
arm. Committed before the training queue started (`results/hardware/real_revision_training/queue.log`).

## Why

Reviewer bA2d (`docs/reviews/corl2026_webp.md`, item 1): a policy that benefits from tracking error
may be using it as a one-bit record of "the grasp has happened" rather than as contact information.
The simulation grid already contains this control: the latched seat token, one bit set by a stall
detector and held, reaches the same mean placement as tracking error (21.8%). Hardware has no such
control. This plan adds one.

## The bit

`scripts/real/grasp_bit.py`: 0 until the measured jaw has opened above 8 units and then closed
below 5 units (the 0--100 opening scale), 1 from that frame to the end of the episode. These are the
thresholds and the rule that locate the grasp-closure frame in `demonstration_summary.json`
(median frame 331 of a median 400-frame episode; 48 of the 49 closing demonstrations close after
the 115-command replay). The bit is computed from the measured jaw only, in training from the
recorded `observation.state` and at deployment from the measured positions since the start of the
rollout (replay included), by the same function. It carries task phase and no contact information.

## Checkpoints

Two new observation designs, one seed, the seeds 1 and 2 recipe (50 demonstrations, 18,549 trimmed
frames, 96 px, 6,000 steps, batch 8, learning rate 0.0001, default ACT, final checkpoint only):

| alias | observation | width | checkpoint |
|---|---|---|---|
| `gbit_s1` | $[\widetilde q_t,\ b_t\mathbf 1_6]$ | 12 | `checkpoints/real50_gbit_v3_s1` |
| `delta_gbit_s1` | $[\widetilde q_t,\ \delta_t/8,\ b_t\mathbf 1_6]$ | 18 | `checkpoints/real50_delta_gbit_v3_s1` |

The bit is broadcast to six entries so that `gbit_s1` has the width of the tracking-error policy,
as the simulation token did. Seed 1 is chosen because it is the seed the reviewer named: its
completed comparison is 14/20 against 1/20, so a recovery by the bit is detectable there. Eligibility:
training completes and the offline observation audit passes for both new arms. No selection on
training loss or hardware outcome.

## Comparisons (20 complete pairs each, one session each)

1. **Primary.** `gbit_s1` against `base_s1`: does a one-bit phase signal lift the position-only
   policy? Launcher: `bash scripts/bench/run_hw_grasp_bit.sh 1`.
2. **Secondary.** `delta_gbit_s1` against `delta_s1`: does the bit add anything once tracking error
   is observed? Launcher: `bash scripts/bench/run_hw_grasp_bit.sh 2`.

Protocol as in every completed comparison: AB/BA order alternating between pairs, 115-command replay
from demonstration 0, 400-step horizon, relative-target limit 8, per-trial video, labels from video
by code (`scripts/real/label_trials.py`), operator label kept alongside.

## Registered predictions and decision rules

Exact two-sided McNemar on the discordant pairs, positive effect and $p<0.05$, is the criterion for
a claimed difference; a non-significant result is "not distinguishable at 20 pairs", not equivalence.

- If comparison 1 is significant in favour of `gbit_s1` and its placement count is within the
  seed-1 tracking-error count's Wilson interval (14/20: 48% to 85%), the paper says that a binary
  grasp-phase input recovers the tracking-error gain on this task, and the contact reading of the
  hardware result is withdrawn. That is a result, not a failure.
- If comparison 1 is not significant and `gbit_s1` places far below 14/20, the paper says the gain
  is not explained by grasp-phase memory alone, with the usual caveat that one seed and 20 pairs
  cannot bound the spread.
- Comparison 2 is descriptive either way: it reports whether the bit changes the tracking-error
  policy, and no claim about contact follows from it.

Cross-reading `gbit_s1` against `delta_s1` through their shared base is descriptive; the two
checkpoints are never paired with each other in this plan.

## Rules carried over

As in `preregistration_2026-11_seed_replication.md`: every trained checkpoint is evaluated, technical
failures are recorded and never dropped, missing outcomes stay missing, an interrupted session stays
interrupted and a clean rerun is a new versioned record, and the overload diagnosis must have a
finding before the session.

## Bench cost

Two sessions of 40 rollouts, roughly 2 hours each with setup.
