# Raw delta replication plan — 2026-09-05

Written after seed-0 hardware results (base 5/20, delta 9/20, exact paired
p=0.2890625), before training seeds 1 and 2. The seed-0 result remains
inconclusive under its registered rule. Do not add trials to that session
until significance appears or merge the older excess session into it.

Train four checkpoints: base and delta at seeds 1 and 2. Keep the seed-0
recipe: same 50-demo recording, 18,549 retained frames after prefix trimming,
96 px, 6,000 steps, batch 8, LR 0.0001, default ACT architecture, same action
and observation normalization. No hyperparameter or checkpoint selection
based on hardware outcomes. Save final checkpoints only. No new data or
compensation fit. Raw action/position history controls remain future work;
this replication cannot establish channel specificity.

Queue runs serially, logs each cell, records source/data hashes and runtime
package versions before training, and refuses existing checkpoint directories.
Four cells are expected to take roughly 2–4 hours on this device, depending
on load. This queue never connects to the robot.

Hardware evaluation is not started by the queue. If the operator proceeds,
use 20 complete pairs per new training seed, the same corrected runner,
115-frame jumpstart, 400-step horizon and AB/BA counterbalancing. Keep all
outcomes, identify every training seed, and report each seed's paired table
and effect separately. Record technical exclusions as in real_delta_prereg.md.
Training completion and offline validation determine eligibility, not a
favourable training loss or selected rollout.

The next study asks whether seed-0's direction reproduces. Report all three
seed effects and their equal-weight mean; do not treat episodes as independent
training-seed replicates. Three seeds still give a weak estimate of training
variance. A broad method claim needs adequate seed-level uncertainty and
history controls; a pooled episode p-value is not a substitute.

Trajectory diagnostics are exploratory. They are not new success criteria or
evidence of contact regulation. No object pose, video or ground-truth force is
saved in the current trial traces. Collection-time command clipping remains
unverified, so the correspondence of demonstration action labels to applied
commands is still a limitation.
