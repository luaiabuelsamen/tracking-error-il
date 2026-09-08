"""Offline parity check on every recorded frame; never connects to hardware."""
import sys

if "-h" in sys.argv[1:] or "--help" in sys.argv[1:]:
    print(__doc__)
    raise SystemExit(0)
import json
from pathlib import Path

import numpy as np
import train_act_real as train
from run_policy_real import build_observation


def main():
    # Images do not enter the numerical state comparison. Avoid decoding them.
    train.decode_video_cache = lambda root, size, n: np.broadcast_to(
        np.zeros((1, 1, 1, 3), np.uint8), (n, 1, 1, 3))
    results = {}
    for arm in ("base", "delta", "excess", "ghist", "hist"):
        ds = train.RealChunkDataset(Path("data/real/pickplace_real_v0"), arm,
                                    trim_static=False)
        stats = {k: getattr(ds, k) for k in ("s_mean", "s_std", "a_mean", "a_std")}
        history, prev, prev2 = [], None, None
        worst = 0.0
        for i in range(len(ds)):
            if ds.first[i]:
                history, prev, prev2 = [], None, None
            history.append(ds.S[i])
            actual = build_observation(arm, ds.S[i], prev, prev2, stats,
                                       getattr(ds, "k_hat", np.zeros(6)), history)
            expected = ds[i]["observation.state"].numpy()
            worst = max(worst, float(np.max(np.abs(actual - expected))))
            np.testing.assert_allclose(actual, expected, rtol=0, atol=1e-6)
            prev2, prev = prev, ds.A[i]
        results[arm] = {"frames": len(ds), "max_abs_error": worst}
    path = Path("results/hardware/real_observation_audit.json")
    path.write_text(json.dumps(results, indent=2) + "\n")
    print(path.read_text())


if __name__ == "__main__":
    main()
