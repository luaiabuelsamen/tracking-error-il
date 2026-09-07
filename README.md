# Tracking error as an observation for behavior cloning on low-cost arms

Code, evaluation records, and manuscript for a study of one cheap observation:
the difference between the position a servo was told to reach and the
position it actually reached. On a position-controlled hobby servo that
difference is present in every recorded dataset, costs nothing at inference
time, and carries information about load and contact. This repository asks
whether giving it to a behavior-cloning policy helps.

Platform: the SO-101 arm (STS3215 servos), one overhead camera, ACT policies
trained with LeRobot. The Python package `so101_bench` is the MuJoCo
simulation benchmark used for the controlled comparison.

<p align="center">
  <a href="media/real_rollout_delta_s1.mp4">
    <img src="figures/paper/fig_real_teaser.png" alt="Three frames of an autonomous SO-101 rollout: the arm approaches a white adapter, lifts it, and places it inside a tape roll." width="100%">
  </a>
</p>

*Autonomous rollout of a tracking-error policy (training seed 1) on the
physical arm, after a fixed demonstration replay brings the arm near the
grasp. Click the image for the clip. This is a showcase recording. It is
not one of the evaluated trials and its outcome is not in any count below.*

## Result

<p align="center">
  <img src="figures/paper/fig_observation_evidence.png" alt="Left: simulation placement success per observation design, bars are means and dots are training seeds. Right: hardware placement counts for base and tracking-error policies in two completed paired evaluations." width="100%">
</p>

| setting | position only | with tracking error | notes |
|---|---|---|---|
| simulation, 280 scripted demos, 100 eval episodes | 6.2% | 21.8% | means over 5 training seeds; position history alone reaches 20.3% (3 seeds) |
| hardware, seed 0, 20 paired trials | 5/20 | 9/20 | exact McNemar p = 0.29 |
| hardware, seed 1, 20 paired trials | 1/20 | 14/20 | exact McNemar p = 0.001 |
| hardware, seed 2 | 0/6 | 0/6 | interrupted by recurring servo overload faults |

Tracking error helps in simulation and in both completed hardware
comparisons, and the size of the hardware effect depends strongly on the
training seed. The simulation grid also shows that a position-history input
without any command information performs about as well as tracking error, so
the paper does not attribute the gain to contact sensing. A study of 16
public teleoperation datasets (546 episodes) rejects the idea that large
tracking error at grasp time labels a successful grasp. Full protocol,
statistics, and limitations are in [`paper/main.tex`](paper/main.tex)
([PDF](paper/main.pdf)).

## Media

Each clip is labeled by what controls the arm. Nothing here was edited beyond
trimming.

| clip | what it shows | control |
|---|---|---|
| [`media/real_rollout_delta_s1.mp4`](media/real_rollout_delta_s1.mp4) | Adapter placed in a tape roll on the physical SO-101, seed 1 tracking-error checkpoint, 400 policy steps after replay of 115 demonstration commands. Showcase recording, outcome not annotated. | autonomous policy |
| [`media/teleoperation.mp4`](media/teleoperation.mp4) | One of the 50 training demonstrations. A human drives the leader arm. | human teleoperation |
| [`media/simulation_delta.mp4`](media/simulation_delta.mp4) | An ACT policy with tracking-error observations in the MuJoCo benchmark. Rendered forces describe the simulator, not the robot. | autonomous policy, simulation |

## Repository layout

```
src/so101_bench/   MuJoCo pick-and-place scene, scripted experts, LeRobot-schema collection
scripts/
  sim/             demonstration collection, ACT training, the observation-design grid, crush and guard screens
  real/            real-data training, policy execution on the arm, paired trial runner, trajectory analysis
  corpus/          the archived-teleoperation study
  paper/           evidence builder, supplementary analyses, number checks
  bench/           hardware setup: teleoperation and recording, servo calibration, lerobot patch snapshot
results/
  simulation/      one JSON per trained policy (design x seed), crush-tier and guard screens
  hardware/        trial outcomes, per-trial trajectories, session manifests and incident records
  corpus/          per-dataset effect sizes and the command-offset sweep
  calibration/     static load measurements on one servo
  showcase/        trajectory records of the showcase rollouts
paper/             main.tex, refs.bib, generated tables and the evidence JSON they come from
figures/paper/     the figures included by main.tex
docs/              simulation benchmark notes, hardware pre-registrations and diagnostics
media/             the clips and stills used above
tests/             simulation environment tests
```

Every file under `results/` was produced by a script that is still in
`scripts/`, and the paper's tables and figures are rebuilt from those files
rather than typed. [`scripts/README.md`](scripts/README.md) and
[`results/README.md`](results/README.md) index both trees and give the
mapping between the design names in the paper and the identifiers in the code.

## Install

```bash
pip install -e ".[data,video,analysis,dev]"
make test
```

Python 3.10 or newer. Rendering uses EGL and works headless. `make test` is
used instead of bare `pytest` because a system ROS install registers pytest
plugins globally that fail on import; the Makefile disables plugin
autoloading. Nothing here uses ROS.

## Reproduce the paper's numbers

Everything the manuscript reports about the hardware trials, the simulation
grid, and the corpus study is recomputed from `results/` and checked against
the text:

```bash
make paper
```

which runs, in order:

```bash
python scripts/paper/build_paper_evidence.py     # tables, evidence.json, the two main figures
python scripts/paper/supplementary_analysis.py   # supplementary statistics, tables and figures
latexmk -pdf -interaction=nonstopmode -halt-on-error -cd paper/main.tex
python scripts/paper/check_paper_numbers.py      # every reported value must match results/
```

The checker fails if a hardware count, a simulation mean, a corpus count, a
supplementary statistic, or a required disclosure sentence in the manuscript
drifts from the data.

## Simulation benchmark

The package exposes a randomized pick-and-place task, three scripted experts
that differ only in the grip signal they read, and dataset collection in the
same schema as the public SO-100/101 datasets, so that
`delta = action[t-1] - state[t]` is reconstructable downstream exactly as it
is from real data.

```python
from so101_bench import DemoEnv

env = DemoEnv(seed=0)
result, frames = env.rollout()                # one scripted episode
env.collect(200, root="~/data/pick_place")    # LeRobotDataset
```

The learning grid in the paper trains one ACT policy per observation design
and seed on 280 scripted demonstrations:

```bash
python scripts/sim/collect_guarded.py --episodes 280 --root data/demos_v3
python scripts/sim/train_act.py --arm delta --root data/demos_v3 --steps 12000 --image-size 96 \
    --seed 0 --eval-episodes 100 --eval-crush -1 --json results/simulation/grid_C_delta_s0.json
```

`scripts/sim/run_grid.sh` runs the whole grid; `scripts/sim/modal_grid.py`
runs it on Modal from `scripts/sim/grid_spec.json`. The environment, grip
modes, resolution knob, and the scripted-expert measurements are documented
in [`docs/simulation.md`](docs/simulation.md).

## Hardware pipeline

The real pipeline uses a LeRobot checkout with local patches; see
[`scripts/bench/lerobot-patch/README.md`](scripts/bench/lerobot-patch/README.md)
for what changed and how to restore it. Set `LEROBOT` to that checkout and
`SO101_VENV_PYTHON` to the interpreter it is installed in. The entry points
are:

```bash
scripts/bench/arms.sh record pickplace_real_v0 50     # teleoperate and record demonstrations
python scripts/real/train_act_real.py --arm delta --root data/real/pickplace_real_v0 \
    --steps 6000 --seed 1 --out checkpoints/real50_delta_v3_s1
bash scripts/bench/run_hw_replication.sh 1            # 20 paired base/tracking-error trials, seed 1
bash scripts/bench/record_demo.sh                     # one showcase rollout with video
```

Trials are paired by physical reset with alternating order, the operator
enters each outcome, and every trial writes a trajectory to
`results/hardware/real_trial_traj/`. The pre-registered decision rules and the
per-session diagnostics are in [`docs/hardware/`](docs/hardware/). Read the
safety notes at the top of `scripts/real/run_policy_real.py` before letting a
policy command the arm.

## Citation

```bibtex
@misc{abuelsamen2026trackingerror,
  title  = {Tracking Error as an Observation for Behavior Cloning on Low-Cost Arms},
  author = {Abuelsamen, Luai},
  year   = {2026},
  note   = {Preprint. Code and evaluation records: https://github.com/luaiabuelsamen/tracking-error-il}
}
```

## License

Apache-2.0.
