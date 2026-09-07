"""Run repeated real-arm policy trials and record a success rate.

One rollout is an anecdote. This runs a paired sequence -- alternating arms from
the same reset scene -- and writes an outcome file you can compute a rate from.

Pairing matters more than trial count here. Alternating two policies over the
same physical resets removes the between-reset variation that would otherwise
swamp the comparison, which is the same reason the simulated grid evaluates on
paired episodes.

You reset the object between trials; the script waits for you. The outcome is
recorded from your keypress, because nothing on this bench can see whether the
adapter ended up in the tape roll.

    python scripts/trial_runner.py --trials 10 --arms base,excess

Outcomes land in results/real_trials.json, appended, so runs accumulate across
sessions rather than overwriting.
"""

import os
import sys

# Re-exec under the project venv if launched with another interpreter. The
# system python has NumPy 2.x and cannot import this pipeline's cv2/torch build,
# which fails deep in an import with a message that does not name the cause.
_VENV = "/home/jetson3/projects/clean_env/venv/bin/python"
if os.path.realpath(sys.executable) != os.path.realpath(_VENV) and os.path.exists(_VENV):
    os.execv(_VENV, [_VENV] + sys.argv)

import argparse
import hashlib
import json
import subprocess
import numpy as np
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
# Always the venv interpreter, never sys.executable: this script is convenient
# to launch with the system python, which has NumPy 2.x and cannot import the
# cv2/torch build the rest of the pipeline uses.
PY = "/home/jetson3/projects/clean_env/venv/bin/python"
CKPT = {"base": "checkpoints/real50_base_s0",
        "base_s1": "checkpoints/real50_base_v3_s1",
        "delta_s1": "checkpoints/real50_delta_v3_s1",
        "base_s2": "checkpoints/real50_base_v3_s2",
        "delta_s2": "checkpoints/real50_delta_v3_s2",
        "delta_v3": "checkpoints/real50_delta_v3_s0",
        "excess": "checkpoints/real50_excess_s0",
        "ghist": "checkpoints/real50_ghist_s0",
        "base_trim": "checkpoints/real50_base_trim",
        # v2 pair: both trimmed of the dead prefix, excess with the load-based
        # k_hat. Matched treatment, so they differ only in the observation.
        "base_v2": "checkpoints/real50_base_v2",
        "excess_v2": "checkpoints/real50_excess_v2"}


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return (max(0.0, c - h), min(1.0, c + h))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", type=int, default=10, help="total rollouts")
    ap.add_argument("--arms", default="base", help="comma-separated, alternated")
    ap.add_argument("--jumpstart", type=int, default=70)
    ap.add_argument("--max-steps", type=int, default=400)
    ap.add_argument("--root", default="data/real/pickplace_real_v0")
    ap.add_argument("--out", default="results/real_trials.json")
    ap.add_argument("--paired", action="store_true",
                    help="two arms, alternating AB/BA pair order; --trials is total rollouts")
    ap.add_argument("--resume", action="store_true", help="resume the most recent recorded session")
    args = ap.parse_args()

    arms = [a.strip() for a in args.arms.split(",")]
    if args.paired and (len(arms) != 2 or args.trials % 2):
        ap.error("--paired requires two arms and an even number of total rollouts")
    for a in arms:
        if a not in CKPT:
            ap.error(f"unknown checkpoint alias: {a}")
        if not (REPO / CKPT[a]).exists():
            raise SystemExit(f"missing checkpoint for {a}: {CKPT[a]}")
        if not (REPO / CKPT[a] / "train_summary.json").exists():
            raise SystemExit(f"training incomplete for {a}")

    out = REPO / args.out
    records = json.loads(out.read_text()) if out.exists() else []
    session = datetime.now().isoformat(timespec="seconds")
    start_trial = 0
    if args.resume:
        if not records:
            ap.error("no saved session to resume")
        session = records[-1]["session"]
        old_manifest = out.with_name(out.stem + "_" + session.replace(":", "") + "_manifest.json")
        old = json.loads(old_manifest.read_text())
        for key in ("arms", "trials", "paired", "jumpstart", "max_steps", "root"):
            if old["args"][key] != getattr(args, key):
                ap.error(f"resume protocol mismatch: {key}")
        for name, digest in old["sha256"].items():
            if name.startswith("checkpoints/") and hashlib.sha256((REPO / name).read_bytes()).hexdigest() != digest:
                ap.error(f"checkpoint changed: {name}")
        start_trial = max(r["trial"] for r in records if r["session"] == session) + 1
        discards = out.with_name(out.stem + "_discards.jsonl")
        if discards.exists():
            for line in discards.read_text().splitlines():
                row = json.loads(line)
                if row["session"] == session:
                    start_trial = max(start_trial, row["trial"] + 1)
    out.parent.mkdir(parents=True, exist_ok=True)
    provenance = {"session": session, "args": vars(args), "sha256": {}}
    paths = [Path(__file__), REPO / "scripts/run_policy_real.py"]
    for a in arms:
        paths.extend(p for p in (REPO / CKPT[a]).iterdir() if p.is_file())
    for p in paths:
        provenance["sha256"][str(p.relative_to(REPO))] = hashlib.sha256(p.read_bytes()).hexdigest()
    suffix = "_resume_" + datetime.now().strftime("%Y%m%dT%H%M%S%f") if args.resume else ""
    out.with_name(out.stem + "_" + session.replace(":", "") + suffix + "_manifest.json").write_text(
        json.dumps(provenance, indent=2))
    traj_dir = REPO / "results" / "real_trial_traj"
    traj_dir.mkdir(parents=True, exist_ok=True)

    print(f"{args.trials} trials, arms {arms}, paired={args.paired}, jumpstart {args.jumpstart} frames.")
    print("Between trials: put the adapter back at its start position and clear the tape roll.\n")

    pending_path = out.with_name(out.stem + "_pending.json")
    pending = json.loads(pending_path.read_text()) if args.resume and pending_path.exists() else None
    if pending and (pending["session"] != session or pending["trial"] != start_trial):
        ap.error("pending incident does not match the next trial; inspect before resuming")
    for t in range(start_trial, args.trials):
        arm = arms[(t % 2) ^ ((t // 2) % 2)] if args.paired else arms[t % len(arms)]
        recovering = pending is not None and pending["trial"] == t
        if recovering and (pending["arm"] != arm or not pending.get("rollout_complete")):
            ap.error("pending trial requires manual incident review")
        tag = f"{session.replace(':','')}_{t:02d}_{arm}"
        cmd = [PY, str(REPO / "scripts" / "run_policy_real.py"),
               "--checkpoint", CKPT[arm], "--arm", arm.split("_")[0],
               "--home", args.root, "--jumpstart", str(args.jumpstart),
               "--max-steps", str(args.max_steps),
               "--out-traj", str(traj_dir / f"{tag}.npz")]
        if recovering:
            print(f"Recovering outcome of trial {t+1}, {arm}; the robot will NOT rerun it.")
            completed = subprocess.CompletedProcess(cmd, pending.get("returncode", -6))
        else:
            input(f"--- trial {t+1}/{args.trials}  arm={arm}  "
                  f"[reset the scene, then press Enter]")
            completed = subprocess.run(cmd, cwd=REPO)
        fault = completed.returncode != 0
        if fault and not recovering:
            trajectory = traj_dir / f"{tag}.npz"
            complete = False
            if trajectory.exists():
                with np.load(trajectory) as z:
                    complete = bool(z.get("rollout_complete", False))
            incident = dict(session=session, trial=t, pair=t // 2 if args.paired else None,
                            arm=arm, returncode=completed.returncode, rollout_complete=complete,
                            trajectory=str(trajectory), reason="rollout subprocess failed")
            pending_path.write_text(json.dumps(incident, indent=2))
            if not complete:
                raise SystemExit("rollout interrupted; incident saved, stop and inspect before resuming")
            print("Rollout completed but shutdown failed. Record the observed outcome; session will stop.")

        while True:
            v = input("    outcome -- [s]uccess (adapter in the tape roll), "
                      "[f]ail, [x] discard this trial: ").strip().lower()
            if v in ("s", "f", "x"):
                break
        if v == "x":
            reason = input("    technical failure reason (policy failures must count): ").strip()
            if not reason:
                raise SystemExit("discard needs a reason; session incomplete")
            discarded = out.with_name(out.stem + "_discards.jsonl")
            with discarded.open("a") as f:
                f.write(json.dumps(dict(session=session, trial=t, arm=arm,
                                       pair=t // 2 if args.paired else None,
                                       reason=reason, traj=f"real_trial_traj/{tag}.npz")) + "\n")
            print("    discarded")
            if pending_path.exists() and (fault or recovering):
                pending_path.rename(pending_path.with_name(out.stem + f"_{session.replace(':', '')}_{t:02d}_incident.json"))
            pending = None
            if fault and not recovering:
                raise SystemExit("Technical exclusion saved; inspect hardware before resuming")
            continue
        records.append(dict(session=session, trial=t, arm=arm,
                            pair=t // 2 if args.paired else None,
                            checkpoint=CKPT[arm],
                            success=(v == "s"), jumpstart=args.jumpstart,
                            shutdown_error=fault,
                            recovered_outcome=recovering,
                            trajectory_missing=not (traj_dir / f"{tag}.npz").exists(),
                            traj=f"real_trial_traj/{tag}.npz"))
        out.write_text(json.dumps(records, indent=2))
        if pending_path.exists() and (fault or recovering):
            pending_path.rename(pending_path.with_name(out.stem + f"_{session.replace(':', '')}_{t:02d}_incident.json"))
        pending = None
        if fault and not recovering:
            raise SystemExit("Outcome saved. Shutdown failed: support the arm, switch off motor power, inspect before resuming.")

        done = [r for r in records if r["arm"] == arm and r["session"] == session]
        k = sum(r["success"] for r in done)
        lo, hi = wilson(k, len(done))
        print(f"    {arm}: {k}/{len(done)}  Wilson 95% [{lo:.2f}, {hi:.2f}]")

    print("\n=== session summary ===")
    for a in arms:
        done = [r for r in records if r["arm"] == a and r["session"] == session]
        k = sum(r["success"] for r in done)
        lo, hi = wilson(k, len(done))
        print(f"  {a:10} {k:3d}/{len(done):<3d}  {100*k/max(len(done),1):5.1f}%  "
              f"Wilson 95% [{lo:.2f}, {hi:.2f}]")
    print(f"\nwrote {out}")
    print("These are jumpstarted rollouts on 50 demonstrations. A rate here is a")
    print("property of this pipeline at this budget, not a result about the channel.")


if __name__ == "__main__":
    main()
