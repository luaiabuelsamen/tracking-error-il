"""Blind outcome labels from the per-trial videos.

The operator who runs a trial knows which policy is running. With ``trial_runner.py --video`` each
rollout's overhead camera is saved, and this script shows those videos in a random order under a
code that carries no policy name (the files themselves are named after the policy, so they are
hard-linked under the code before playing). The labeller answers s / f / u (watch again). Labels go
to ``<trials stem>_video_labels.json`` next to the trial record, with the labeller's name and time.
Agreement with the operator's live labels is printed only once every video is labeled.

    python scripts/real/label_trials.py --trials results/hardware/real_delta_v3_s3_trials.json --labeller <name>
    python scripts/real/label_trials.py --trials ... --compare      # agreement table only

Success means the adapter rests inside the tape roll at the end of the rollout, as in every session.
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]


def code_of(row):
    return hashlib.sha256(f"{row['session']}/{row['trial']}".encode()).hexdigest()[:6]


def agreement(rows, labels):
    both = [(r, labels[f"{r['session']}/{r['trial']}"]["label"]) for r in rows
            if f"{r['session']}/{r['trial']}" in labels]
    agree = sum((lab == "s") == bool(r["success"]) for r, lab in both)
    return agree, len(both)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", required=True, help="trial record written by trial_runner.py")
    ap.add_argument("--labeller", default="unknown")
    ap.add_argument("--compare", action="store_true", help="print agreement with operator labels and exit")
    ap.add_argument("--seed", type=int, default=None, help="shuffle seed (default: random)")
    args = ap.parse_args()
    trials = Path(args.trials)
    rows = [r for r in json.loads(trials.read_text()) if r.get("video")]
    if not rows:
        raise SystemExit("no trial in this record has a video; run the session with --video")
    out = trials.with_name(trials.stem + "_video_labels.json")
    saved = json.loads(out.read_text()) if out.exists() else dict(labels={})
    labels = saved["labels"]
    if args.compare:
        agree, n = agreement(rows, labels)
        print(f"{n} video labels, {agree} agree with the operator's live label")
        return
    todo = [r for r in rows if f"{r['session']}/{r['trial']}" not in labels]
    np.random.default_rng(args.seed).shuffle(todo)
    player = shutil.which("ffplay") if os.environ.get("DISPLAY") else None
    with tempfile.TemporaryDirectory(prefix="blind_labels_") as tmp:
        for i, row in enumerate(todo):
            src = REPO / "results" / "hardware" / row["video"]
            if not src.exists():
                print(f"[{i + 1}/{len(todo)}] video missing for one trial: {src.name}; skipped")
                continue
            code = code_of(row)
            blind = Path(tmp) / f"{code}.mp4"
            try:
                os.link(src, blind)
            except OSError:
                shutil.copyfile(src, blind)
            while True:
                print(f"\n[{i + 1}/{len(todo)}] trial {code}: {blind}")
                if player:
                    subprocess.run([player, "-autoexit", "-loglevel", "error", "-window_title", code, str(blind)])
                else:
                    print("(no display: open the file above in a video player)")
                k = input("    adapter inside the tape roll at the end?  s = success, f = failure, u = watch again: ").strip().lower()
                if k in ("s", "f"):
                    labels[f"{row['session']}/{row['trial']}"] = dict(code=code, label=k,
                                                                     labeller=args.labeller,
                                                                     time=datetime.now().isoformat(timespec="seconds"))
                    out.write_text(json.dumps(dict(trials=trials.name, labels=labels), indent=1))
                    break
    remaining = [r for r in rows if f"{r['session']}/{r['trial']}" not in labels]
    print(f"\n{len(labels)} labels -> {out}")
    if remaining:
        print(f"{len(remaining)} trials still unlabeled; agreement is printed when all are done")
    else:
        agree, n = agreement(rows, labels)
        print(f"all {n} labeled; {agree} agree with the operator's live label")


if __name__ == "__main__":
    main()
