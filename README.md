# Tracking error as an observation for behavior cloning on low-cost arms

Code, hardware records, and manuscript for a study of one cheap observation:
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
the paper does not attribute the gain to contact sensing. The archived
teleoperation study (16 public datasets, 546 episodes) rejects the idea that
large tracking error at grasp time labels a successful grasp. Full protocol,
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

A standalone browsable gallery with more showcase clips lives in
[`research/portfolio/`](research/portfolio/).

## Repository layout

```
src/so101_bench/    MuJoCo pick-and-place scene, scripted experts, LeRobot-schema collection
scripts/            the experimental record: sim grid, real-data training, hardware trial runner,
                    paper evidence builder and number checks
results/            frozen outcomes: grid JSON per design and seed, hardware trial logs,
                    per-trial trajectories (.npz), corpus study, showcase records
paper/              main.tex, refs.bib, generated tables and the evidence JSON they come from
figures/paper/      only the figures included by main.tex
docs/               findings.md (lab record) and the hardware pre-registrations and diagnostics
media/              the clips and stills used above
scripts/bench/      hardware entry points, servo calibration, bench utilities, lerobot patch snapshot
tests/              simulation environment tests
research/           everything that is not part of the submission: thesis note, working notes,
                    reading notes, the pre-rewrite manuscript, the portfolio gallery
```

`scripts/` and `results/` are paired and are kept complete rather than
tidy: every JSON under `results/` was produced by a script that is still
here, and the paper's tables are rebuilt from those files rather than typed.

## Install

```bash
pip install -e ".[data,video,dev]"
make test
```

Python 3.10 or newer. Rendering uses EGL and works headless. `make test` is
used instead of bare `pytest` because a system ROS install registers pytest
plugins globally that fail on import; the Makefile disables plugin
autoloading. Nothing here uses ROS.

## Reproduce the paper's numbers

Everything the manuscript reports about the hardware trials and the
simulation grid is recomputed from `results/` and checked against the text:

```bash
python scripts/build_paper_evidence.py     # writes paper/generated/*.tex, evidence.json, figures
latexmk -pdf -interaction=nonstopmode -halt-on-error -cd paper/main.tex
python scripts/check_paper_numbers.py      # asserts every reported value matches results/
```

The checker fails if a hardware count, a simulation mean, a corpus count, or a
required disclosure sentence in the manuscript drifts from the data.

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
python scripts/collect.py --episodes 280 --root data/demos_v3 --grip-mode force
python scripts/train_act.py --arm delta --root data/demos_v3 --steps 12000 --image-size 96 \
    --seed 0 --eval-episodes 100 --eval-crush -1 --json results/grid_C_delta_s0.json
```

Designs (`--arm`): `base`, `base_hist`, `delta`, `resid`, `excess`, `token`,
`ghist`. `scripts/run_grid.sh` runs the whole grid; `scripts/modal_grid.py`
runs it on Modal from `scripts/grid_spec.json`. The environment, grip modes,
resolution knob, and the scripted-expert measurements are documented in
[`docs/simulation_bench.md`](docs/simulation_bench.md).

## Hardware pipeline

The real pipeline uses a LeRobot checkout with local patches; see
[`scripts/bench/lerobot-patch/README.md`](scripts/bench/lerobot-patch/README.md) for what changed and how to restore
it. The Jetson-side entry points are:

```bash
scripts/bench/arms.sh record pickplace_real_v0 50        # teleoperate and record demonstrations
python scripts/train_act_real.py --arm delta --root data/real/pickplace_real_v0 \
    --steps 6000 --seed 1 --out checkpoints/real50_delta_v3_s1
bash scripts/bench/run_hw_replication.sh 1                       # 20 paired base/delta trials for seed 1
bash scripts/bench/record_demo.sh                                # one showcase rollout with video
```

Trials are paired by physical reset with alternating order, the operator
enters each outcome, and every trial writes a trajectory to
`results/real_trial_traj/`. The pre-registered decision rules and the
per-session diagnostics are in `docs/real_*.md`. Read the safety notes at the
top of `scripts/run_policy_real.py` before letting a policy command the arm.

## Research material

`research/` holds the material behind the study that a reader of the paper
does not need: the one-sentence thesis the project is organized around, the
reading program and per-thread notes, roadmap and hand-off documents, the
manuscript as it stood before the hardware rewrite with its figures, and the
portfolio gallery. See [`research/README.md`](research/README.md).

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
