#!/bin/bash
# One entry point for the physical SO-101 pair.
#
#   scripts/bench/arms.sh ports              # list serial ports + which USB device
#   scripts/bench/arms.sh calibrate-leader   # one-time leader calibration (interactive)
#   scripts/bench/arms.sh calibrate-follower # redo follower calibration (interactive)
#   scripts/bench/arms.sh teleop             # leader-follower teleoperation loop
#   scripts/bench/arms.sh teleop-cam         # teleop + front camera preview
#   scripts/bench/arms.sh record NAME N      # record N teleop episodes -> data/real/NAME
#   RESUME=1 scripts/bench/arms.sh record NAME N   # append N more to an existing set
#   scripts/bench/arms.sh staircase          # bench calibration (delta/load/current vs load cell)
#
# Convention (from the original working setup): FOLLOWER=/dev/ttyACM0,
# LEADER=/dev/ttyACM1. If the wrong arm moves in teleop, the USB enumeration
# swapped -- override with:  FOLLOWER=/dev/ttyACM1 LEADER=/dev/ttyACM0 scripts/bench/arms.sh teleop
set -euo pipefail
SELF="$(readlink -f "$0")"

FOLLOWER="${FOLLOWER:-/dev/ttyACM0}"
LEADER="${LEADER:-/dev/ttyACM1}"
FID="${FID:-my_awesome_follower_arm}"
LID="${LID:-my_awesome_leader_arm}"
CAM="${CAM:-/dev/video0}"
# Patched lerobot checkout and the interpreter that has it installed; see
# lerobot-patch/README.md. Override with LEROBOT= and SO101_VENV_PYTHON=.
LEROBOT="${LEROBOT:-$HOME/projects/clean_env/lerobot}"
PY="${SO101_VENV_PYTHON:-python}"
BENCH="$(cd "$(dirname "$SELF")/../.." && pwd)"

cd "$LEROBOT"

cmd="${1:-help}"
cmd="${cmd##--}"        # accept --teleop as teleop, etc.
case "$cmd" in
  ports)
    found=$(ls -l /dev/ttyACM* /dev/ttyUSB* 2>/dev/null || true)
    [ -n "$found" ] && echo "$found" || echo "no serial devices"
    ;;
  calibrate-leader)
    exec $PY src/lerobot/scripts/lerobot_calibrate.py \
      --teleop.type=so101_leader --teleop.port="$LEADER" --teleop.id="$LID"
    ;;
  calibrate-follower)
    exec $PY src/lerobot/scripts/lerobot_calibrate.py \
      --robot.type=so101_follower --robot.port="$FOLLOWER" --robot.id="$FID"
    ;;
  teleop)
    exec $PY src/lerobot/scripts/lerobot_teleoperate.py \
      --robot.type=so101_follower --robot.port="$FOLLOWER" --robot.id="$FID" \
      --teleop.type=so101_leader --teleop.port="$LEADER" --teleop.id="$LID"
    ;;
  teleop-cam)
    exec $PY src/lerobot/scripts/lerobot_teleoperate.py \
      --robot.type=so101_follower --robot.port="$FOLLOWER" --robot.id="$FID" \
      --robot.cameras="{\"front\": {\"type\": \"opencv\", \"index_or_path\": \"$CAM\", \"width\": 640, \"height\": 480, \"fps\": 30}}" \
      --teleop.type=so101_leader --teleop.port="$LEADER" --teleop.id="$LID" \
      --display_data=true
    ;;
  record)
    NAME="${2:?usage: arms.sh record NAME N_EPISODES}"
    N="${3:?usage: arms.sh record NAME N_EPISODES}"
    # keys during recording: RIGHT-ARROW = next episode, LEFT-ARROW = redo,
    # ESC = finish. Local only (push_to_hub=false).
    exec $PY -m lerobot.scripts.lerobot_record \
      --robot.type=so101_follower --robot.port="$FOLLOWER" --robot.id="$FID" \
      --robot.cameras="{\"front\": {\"type\": \"opencv\", \"index_or_path\": \"$CAM\", \"width\": 640, \"height\": 480, \"fps\": 30}}" \
      --teleop.type=so101_leader --teleop.port="$LEADER" --teleop.id="$LID" \
      --dataset.fps=30 \
      --dataset.repo_id="luaia/$NAME" \
      --dataset.root="$BENCH/data/real/$NAME" \
      --dataset.single_task="${TASK:-pick up the white power adapter and place it in the center of the tape roll}" \
      --dataset.num_episodes="$N" \
      --dataset.episode_time_s=25 \
      --dataset.reset_time_s=8 \
      --dataset.push_to_hub=false \
      ${RESUME:+--resume=true}
    ;;
  staircase)
    shift
    cd "$BENCH"
    exec $PY scripts/bench/staircase_cal.py --port "$FOLLOWER" "$@"
    ;;
  *)
    sed -n '2,14p' "$SELF"
    ;;
esac
