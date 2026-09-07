"""Capture inputs before the replication queue starts; requires CUDA."""
import hashlib
import importlib.metadata
import json
from datetime import datetime, timezone
from pathlib import Path

import torch

if not torch.cuda.is_available():
    raise SystemExit("CUDA unavailable; refusing an accidental CPU training queue")

paths = [Path("scripts/train_act_real.py"), Path("scripts/run_real_delta_replication.sh"),
         Path("docs/real_delta_replication.md")]
root = Path("data/real/pickplace_real_v0")
paths += sorted((root / "data").rglob("*.parquet"))
paths += [root / "frames_96.npy", root / "meta/info.json"]
hashes = {}
for path in paths:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    hashes[str(path)] = h.hexdigest()
packages = {}
for package in ("torch", "torchvision", "lerobot", "numpy", "pyarrow"):
    packages[package] = importlib.metadata.version(package)
out = Path("results/real_delta_replication/manifest.json")
with out.open("x") as f:
    json.dump(dict(created_utc=datetime.now(timezone.utc).isoformat(),
                   sha256=hashes, packages=packages, gpu=torch.cuda.get_device_name(0)), f, indent=2)
print(f"Recorded {out}", flush=True)
