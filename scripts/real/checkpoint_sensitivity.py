"""Offline checks on the six evaluated real-data checkpoints; never touches hardware.

Two questions the hardware trials cannot answer on their own:

1. Does offline imitation error predict hardware success?  Teacher-forcing L1
   error of each checkpoint's predicted 30-command chunk against the recorded
   chunk, on the frames it was trained on (there is no held-out demonstration
   set; the number is a fit diagnostic, not a generalization estimate).
2. Do the tracking-error policies actually read the tracking-error input?  The
   same frames are re-scored with the six tracking-error dimensions set to zero
   and with them permuted across frames.  The mean absolute change in the
   predicted commands, overall and for the jaw, measures how much the network
   depends on that block.  Position-only checkpoints have no such block and
   serve as the reference for the error metric only.

Frames are split by whether the recorded gripper load register sits at its
configured limit (|Present_Load| >= 500), the closest available proxy for the
jaw pressing on something.

    SO101_VENV_PYTHON=... python scripts/real/checkpoint_sensitivity.py
"""
from __future__ import annotations

import glob
import json
import os
import sys
from pathlib import Path

import numpy as np

_VENV = os.environ.get("SO101_VENV_PYTHON", os.path.expanduser("~/projects/clean_env/venv/bin/python"))
if os.path.realpath(sys.executable) != os.path.realpath(_VENV) and os.path.exists(_VENV):
    os.execv(_VENV, [_VENV] + sys.argv)

import torch  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import train_act_real as train  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data/real/pickplace_real_v0"
CHECKPOINTS = [  # alias, observation design, checkpoint, training seed, hardware placements / pairs
    ("base_v2", "base", "checkpoints/real50_base_v2", 0, (5, 20)),
    ("delta_v3", "delta", "checkpoints/real50_delta_v3_s0", 0, (9, 20)),
    ("base_s1", "base", "checkpoints/real50_base_v3_s1", 1, (1, 20)),
    ("delta_s1", "delta", "checkpoints/real50_delta_v3_s1", 1, (14, 20)),
    ("base_s2", "base", "checkpoints/real50_base_v3_s2", 2, (0, 6)),
    ("delta_s2", "delta", "checkpoints/real50_delta_v3_s2", 2, (0, 6)),
]
STRIDE, BATCH, SEED = 4, 64, 0
DEV = "cuda" if torch.cuda.is_available() else "cpu"


def load_register():
    import pyarrow as pa
    import pyarrow.parquet as pq
    files = sorted(glob.glob(str(DATA / "data" / "**" / "*.parquet"), recursive=True))
    t = pa.concat_tables([pq.read_table(f) for f in files])
    return np.array(t["observation.state"].to_pylist(), np.float32)[:, 6:12]


def chunks(policy, ds, idx, state_override=None):
    """Denormalized predicted chunks for dataset positions idx, optionally replacing states."""
    out = []
    for start in range(0, len(idx), BATCH):
        sel = idx[start:start + BATCH]
        items = [ds[int(i)] for i in sel]
        state = torch.stack([it["observation.state"] for it in items])
        if state_override is not None:
            state = torch.from_numpy(state_override[start:start + len(sel)])
        img = torch.stack([it["observation.images.front"] for it in items])
        with torch.inference_mode():
            pred = policy.predict_action_chunk({"observation.state": state.to(DEV),
                                                "observation.images.front": img.to(DEV)})
        out.append(pred.cpu().numpy())
    pred = np.concatenate(out) * ds.a_std + ds.a_mean
    return pred


def main():
    from lerobot.policies.act.modeling_act import ACTPolicy
    load = load_register()
    results = {}
    for alias, arm, ckpt, seed, (succ, pairs) in CHECKPOINTS:
        ds = train.RealChunkDataset(DATA, arm)
        stats = dict(np.load(ROOT / ckpt / "norm_stats.npz"))
        np.testing.assert_allclose(stats["s_mean"], ds.s_mean, rtol=1e-5)
        np.testing.assert_allclose(stats["a_mean"], ds.a_mean, rtol=1e-5)
        policy = ACTPolicy.from_pretrained(str(ROOT / ckpt)).to(DEV).eval()
        # positions into ds.index (trimmed frames), every STRIDE-th
        pos = np.arange(0, len(ds), STRIDE)
        frames = ds.index[pos]
        truth = np.stack([ds.A[i:i + train.CHUNK] if ds.ep_end[i] - i >= train.CHUNK else
                          np.concatenate([ds.A[i:ds.ep_end[i]], np.repeat(ds.A[ds.ep_end[i] - 1:ds.ep_end[i]], train.CHUNK - (ds.ep_end[i] - i), 0)])
                          for i in frames])
        valid = np.stack([np.arange(train.CHUNK) < ds.ep_end[i] - i for i in frames])
        saturated = np.abs(load[frames, 5]) >= 499.5
        pred = chunks(policy, ds, pos)
        err = np.abs(pred - truth)
        def masked(e, m=None):
            w = valid if m is None else valid & m[:, None]
            return dict(all=float(e[w].mean()), jaw=float(e[..., 5][w].mean()))
        rec = dict(arm=arm, checkpoint=ckpt, seed=seed, hardware=dict(placed=succ, pairs=pairs),
                   frames=int(len(frames)), saturated_frames=int(saturated.sum()),
                   teacher_forcing_l1=dict(overall=masked(err), saturated=masked(err, saturated),
                                           free=masked(err, ~saturated)))
        if arm == "delta":
            states = np.stack([ds[int(i)]["observation.state"].numpy() for i in pos])
            zero = states.copy()
            zero[:, 6:] = 0.0
            perm = states.copy()
            perm[:, 6:] = states[np.random.default_rng(SEED).permutation(len(states)), 6:]
            for name, alt in (("zeroed", zero), ("permuted", perm)):
                p2 = chunks(policy, ds, pos, alt)
                change = np.abs(p2 - pred)
                e2 = np.abs(p2 - truth)
                rec[f"delta_{name}"] = dict(
                    change=dict(overall=masked(change), saturated=masked(change, saturated),
                                free=masked(change, ~saturated)),
                    teacher_forcing_l1=dict(overall=masked(e2), saturated=masked(e2, saturated),
                                            free=masked(e2, ~saturated)))
            # the same scale, for reference: how large the recorded first command step is
            rec["reference_step_l1"] = masked(np.abs(truth[:, 1:] - truth[:, :-1]).mean(1, keepdims=True).repeat(train.CHUNK, 1))
        results[alias] = rec
        print(alias, json.dumps({k: v for k, v in rec.items() if k not in ("arm", "checkpoint")}, default=float)[:400])
    out = ROOT / "results/hardware/checkpoint_sensitivity.json"
    out.write_text(json.dumps(dict(stride=STRIDE, permutation_seed=SEED, device=DEV, checkpoints=results),
                              indent=2, default=float) + "\n")
    print("wrote", out)


if __name__ == "__main__":
    main()
