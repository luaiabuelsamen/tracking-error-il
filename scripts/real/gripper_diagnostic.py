"""Read the gripper servo's registers at rest, during a scripted close on an object, and at release.

Prepared for docs/hardware/overload_diagnosis_2026-11.md. It is run only with the operator at the
bench (``--operator-present``) and it writes to the gripper servo only; the five arm joints are read,
never commanded. Nothing in this script moves the arm.

Phases
  rest    no writes at all: one full register snapshot of all six motors plus ``--seconds`` of the
          fast set, and a table of the gripper's protection settings beside the other joints
  close   with the adapter (or nothing) between the jaws: enable gripper torque, close from the
          present opening to ``--target`` at no more than ``--step`` units per tick, hold for
          ``--hold-seconds``, then release torque while still sampling (``--after-seconds``), which
          is the moment the trial runner sees the overload error. ``--open-first`` reopens to the
          start opening before releasing instead.

    python scripts/real/gripper_diagnostic.py --phase rest --operator-present
    python scripts/real/gripper_diagnostic.py --phase close --hold-seconds 15 --operator-present

Output: results/hardware/gripper_diagnostic/<timestamp>_<phase>.jsonl (one sample per line) and
<timestamp>_<phase>_summary.json. Positions are reported raw (encoder ticks) and on the runner's
0--100 opening scale when the arm's calibration file is found.
"""

import os
import sys

_VENV = os.environ.get("SO101_VENV_PYTHON", os.path.expanduser("~/projects/clean_env/venv/bin/python"))
if os.path.realpath(sys.executable) != os.path.realpath(_VENV) and os.path.exists(_VENV):
    os.execv(_VENV, [_VENV] + sys.argv)

import argparse
import json
import time
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
GRIPPER = "gripper"
MOTOR_IDS = {"shoulder_pan": 1, "shoulder_lift": 2, "elbow_flex": 3, "wrist_flex": 4, "wrist_roll": 5, "gripper": 6}
# Status byte of the STS3215, as decoded by the servo SDK (protocol_packet_handler.py).
STATUS_BITS = {1: "voltage", 2: "angle", 4: "overheat", 8: "overcurrent", 16: "bit16", 32: "overload"}
CONFIG_REGISTERS = (
    "Torque_Enable", "Operating_Mode", "Goal_Position", "Torque_Limit", "Max_Torque_Limit",
    "Protection_Current", "Protective_Torque", "Protection_Time", "Overload_Torque",
    "Over_Current_Protection_Time", "Unloading_Condition", "Phase",
    "P_Coefficient", "I_Coefficient", "D_Coefficient", "Acceleration", "Lock",
)
FAST_REGISTERS = ("Present_Position", "Goal_Position", "Present_Load", "Present_Current",
                  "Present_Voltage", "Present_Temperature", "Status", "Moving", "Torque_Enable")


def decode_status(value):
    return [name for bit, name in STATUS_BITS.items() if value & bit]


def load_calibration(robot_id):
    from lerobot.motors import MotorCalibration
    path = Path.home() / ".cache/huggingface/lerobot/calibration/robots/so101_follower" / f"{robot_id}.json"
    if not path.exists():
        print(f"no calibration file at {path}; positions are reported raw only")
        return None
    raw = json.loads(path.read_text())
    return {name: MotorCalibration(**values) for name, values in raw.items()}


def read_raw(bus, name, motor):
    try:
        return int(bus.read(name, motor, normalize=False))
    except Exception as exc:  # noqa: BLE001 -- a faulting servo answers with errors; keep sampling
        return f"ERR {type(exc).__name__}: {exc}"


def sample(bus, motors, registers, calibrated, t0, phase):
    row = dict(t=round(time.perf_counter() - t0, 4), phase=phase)
    for motor in motors:
        values = {name: read_raw(bus, name, motor) for name in registers}
        if isinstance(values.get("Status"), int):
            values["status_bits"] = decode_status(values["Status"])
        if calibrated and "Present_Position" in registers:
            try:
                values["position_norm"] = float(bus.read("Present_Position", motor, normalize=True))
            except Exception as exc:  # noqa: BLE001
                values["position_norm"] = f"ERR {type(exc).__name__}: {exc}"
        row[motor] = values
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", choices=("rest", "close"), default="rest")
    ap.add_argument("--port", default="/dev/ttyACM0")
    ap.add_argument("--robot-id", default="my_awesome_follower_arm")
    ap.add_argument("--seconds", type=float, default=5.0, help="rest: sampling duration")
    ap.add_argument("--hz", type=float, default=5.0, help="fast-set sampling rate")
    ap.add_argument("--target", type=float, default=2.0, help="close: jaw target on the 0--100 opening scale")
    ap.add_argument("--step", type=float, default=2.0, help="close: max change of the goal per 1/30 s tick")
    ap.add_argument("--hold-seconds", type=float, default=10.0)
    ap.add_argument("--after-seconds", type=float, default=5.0, help="sampling after torque release")
    ap.add_argument("--open-first", action="store_true", help="reopen to the start opening before releasing torque")
    ap.add_argument("--operator-present", action="store_true", help="required; the operator is at the bench")
    ap.add_argument("--out-dir", default="results/hardware/gripper_diagnostic")
    args = ap.parse_args()
    if not args.operator_present:
        raise SystemExit("refusing to touch the arm without --operator-present")

    from lerobot.motors import Motor, MotorNormMode
    from lerobot.motors.feetech import FeetechMotorsBus

    calibration = load_calibration(args.robot_id)
    motors = {name: Motor(mid, "sts3215", MotorNormMode.RANGE_0_100 if name == GRIPPER else MotorNormMode.DEGREES)
              for name, mid in MOTOR_IDS.items()}
    bus = FeetechMotorsBus(port=args.port, motors=motors, calibration=calibration)
    bus.connect()
    names = list(motors)
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    out_dir = REPO / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    log_path = out_dir / f"{stamp}_{args.phase}.jsonl"
    log = log_path.open("w")
    t0 = time.perf_counter()
    rows = []

    def emit(row):
        rows.append(row)
        log.write(json.dumps(row) + "\n")
        log.flush()

    # Full configuration snapshot, all motors, before anything else.
    snapshot = sample(bus, names, CONFIG_REGISTERS + FAST_REGISTERS, calibration is not None, t0, "config_before")
    emit(snapshot)
    print("\nprotection settings (gripper beside the arm joints):")
    header = ["register"] + names
    print("  " + "  ".join(f"{h:>14}" for h in header))
    for reg in ("Max_Torque_Limit", "Torque_Limit", "Protection_Current", "Protective_Torque", "Protection_Time",
                "Overload_Torque", "Over_Current_Protection_Time", "Unloading_Condition", "P_Coefficient",
                "Present_Voltage", "Present_Temperature", "Status"):
        print("  " + "  ".join(f"{str(v):>14}" for v in [reg] + [snapshot[m].get(reg) for m in names]))
    for m in names:
        bits = snapshot[m].get("status_bits")
        if bits:
            print(f"  status flags already set on {m}: {bits}")

    exception_text = None
    try:
        if args.phase == "rest":
            end = time.perf_counter() + args.seconds
            while time.perf_counter() < end:
                emit(sample(bus, names, FAST_REGISTERS, calibration is not None, t0, "rest"))
                time.sleep(1.0 / args.hz)
        else:
            if calibration is None:
                raise SystemExit("close needs the calibration file to command the jaw on the 0--100 scale")
            start = float(bus.read("Present_Position", GRIPPER, normalize=True))
            print(f"\ngripper at {start:.1f} on the 0--100 scale; will close to {args.target:.1f} at <= {args.step} per tick,"
                  f" hold {args.hold_seconds:.0f} s, then {'reopen and ' if args.open_first else ''}release torque.")
            print("Only the gripper is commanded. Keep hands clear of the jaw.")
            if input("type CLOSE to proceed: ").strip() != "CLOSE":
                raise SystemExit("aborted by operator")
            bus.enable_torque(GRIPPER)
            goal = start
            tick = 1.0 / 30
            while goal > args.target + 1e-6:
                goal = max(args.target, goal - args.step)
                bus.write("Goal_Position", GRIPPER, goal, normalize=True)
                emit(sample(bus, [GRIPPER], FAST_REGISTERS, True, t0, "closing"))
                time.sleep(tick)
            end = time.perf_counter() + args.hold_seconds
            while time.perf_counter() < end:
                emit(sample(bus, names, FAST_REGISTERS, True, t0, "hold"))
                time.sleep(1.0 / args.hz)
            if args.open_first:
                while goal < start - 1e-6:
                    goal = min(start, goal + args.step)
                    bus.write("Goal_Position", GRIPPER, goal, normalize=True)
                    emit(sample(bus, [GRIPPER], FAST_REGISTERS, True, t0, "opening"))
                    time.sleep(tick)
            emit(sample(bus, names, CONFIG_REGISTERS + FAST_REGISTERS, True, t0, "config_before_release"))
            try:
                bus.disable_torque(GRIPPER)
                emit(dict(t=round(time.perf_counter() - t0, 4), phase="release", result="torque disabled without error"))
            except Exception as exc:  # noqa: BLE001 -- this is the fault under study
                exception_text = f"{type(exc).__name__}: {exc}"
                emit(dict(t=round(time.perf_counter() - t0, 4), phase="release", result=exception_text))
                print(f"\nrelease raised: {exception_text}")
            end = time.perf_counter() + args.after_seconds
            while time.perf_counter() < end:
                emit(sample(bus, names, FAST_REGISTERS, True, t0, "after_release"))
                time.sleep(1.0 / args.hz)
            if exception_text:
                for attempt in range(3):
                    try:
                        bus.disable_torque(GRIPPER)
                        emit(dict(t=round(time.perf_counter() - t0, 4), phase="release_retry", attempt=attempt, result="ok"))
                        break
                    except Exception as exc:  # noqa: BLE001
                        emit(dict(t=round(time.perf_counter() - t0, 4), phase="release_retry", attempt=attempt,
                                  result=f"{type(exc).__name__}: {exc}"))
                        time.sleep(0.5)
    finally:
        emit(sample(bus, names, CONFIG_REGISTERS + FAST_REGISTERS, calibration is not None, t0, "config_after"))
        log.close()
        try:
            bus.disconnect(disable_torque=False)
        except Exception as exc:  # noqa: BLE001
            print(f"disconnect raised: {type(exc).__name__}: {exc}")

    grip = [r[GRIPPER] for r in rows if GRIPPER in r and isinstance(r[GRIPPER].get("Present_Current"), int)]
    def _num(key):
        return [r[key] for r in grip if isinstance(r.get(key), int)]
    seen_bits = sorted({b for r in grip for b in r.get("status_bits", [])})
    first_overload = next((r["t"] for r in rows if GRIPPER in r and "overload" in r[GRIPPER].get("status_bits", [])), None)
    summary = dict(phase=args.phase, log=str(log_path.relative_to(REPO)), samples=len(rows),
                   gripper_max_current=max(_num("Present_Current"), default=None),
                   gripper_max_abs_load=max((abs(v) for v in _num("Present_Load")), default=None),
                   gripper_min_voltage_0p1V=min(_num("Present_Voltage"), default=None),
                   gripper_max_temperature_C=max(_num("Present_Temperature"), default=None),
                   gripper_status_bits_seen=seen_bits, first_overload_bit_t=first_overload,
                   release_exception=exception_text,
                   config_before={m: {k: snapshot[m].get(k) for k in CONFIG_REGISTERS} for m in names},
                   args=vars(args))
    summary_path = out_dir / f"{stamp}_{args.phase}_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")
    print(f"\nwrote {log_path}\n      {summary_path}")
    print(json.dumps({k: v for k, v in summary.items() if k not in ("config_before", "args")}, indent=1))


if __name__ == "__main__":
    main()
