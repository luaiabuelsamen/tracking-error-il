# scripts/bench/

Bench operation, not experiments: the hardware entry points, the servo calibration
script, and the snapshot of local lerobot patches (`lerobot-patch/`). Nothing here
produces a result that appears in the paper except `staircase_cal.py`, whose static
load measurements are the appendix's measurement context; the rest exists so a
hardware session does not get wasted on setup.

The rest of `scripts/` is the opposite: it is the experimental record, paired with
`results/`, and should not be tidied by deletion.

| tool | what it is for |
|---|---|
| `validate_record_args.py` | parses the real record config with the exact argv `arms.sh` passes, without opening a serial port or camera. Run it from the desk before a bench session; it is what caught the py3.10 `pyav_utils` crash. |
| `camera_stream.py` | serves the bench camera as MJPEG on a port, for checking framing from a browser over Tailscale. Holds the camera — stop it before teleop or record. |
| `export_episodes.py` | splits a recorded dataset's AV1 chunk into per-episode H.264 clips plus an index page, because lerobot writes one blob of all episodes in a codec Safari will not play. |

```bash
python scripts/bench/validate_record_args.py
python scripts/bench/camera_stream.py                     # then open http://<host>:8000/
python scripts/bench/export_episodes.py --root data/real/<name> --serve 8001
```

## Hardware entry points

| script | what it does |
|---|---|
| `arms.sh` | ports, calibration, teleoperation, and recording for the leader/follower pair |
| `run_hw_replication.sh [1|2]` | 20 paired base/tracking-error trials for one training seed |
| `run_hw_trials.sh` | the seed-0 paired session |
| `record_demo.sh` | one showcase rollout with video into `results/showcase/` |
| `staircase_cal.py` | hanging-mass calibration of tracking error, `Present_Load`, and `Present_Current` on one joint |
