# Gripper overload: what is known, what to test, what was found — 2026-11

Status: **prepared, not yet tested at the bench.** The findings section is empty until Luai runs the
diagnostic with the arm powered. Nothing here was measured on 2026-11-10.

## The symptom

The servo library raises `Overload error` from the gripper (STS3215, ID 6) while torque is being
disabled at the end of a completed rollout. It has occurred in 10 of 112 tabulated rollouts
(`paper/generated/overload_table.tex`): never in seed 0, once per policy in seed 1, three and one in
the interrupted seed 2, and four of nine tracking-error against zero of ten position-history rollouts
in the interrupted history session. In that last session the servo also stopped following jaw
commands for about 40 steps in three rollouts. The tracking-error policy is the one that closes and
holds the jaw to the end of the horizon, so the fault most often follows a sustained stall on the
adapter.

## What the configuration says (read from the code, 2026-11-10)

`SO101Follower.configure()` in lerobot 0.3.4 runs at **every** `robot.connect()`, so every trial
rewrites these values. For all six motors it sets position mode, P = 16, I = 0, D = 32. For the
gripper only it sets:

| register | value | meaning |
|---|---|---|
| `Max_Torque_Limit` | 500 | 50% of maximum torque, "to avoid burnout" |
| `Protection_Current` | 250 | 50% of maximum current |
| `Overload_Torque` | 25 | output falls to 25% once the firmware declares an overload |

The other joints keep the servo's EEPROM defaults for these three and for `Protective_Torque` and
`Protection_Time`, which the follower does not touch on any joint. The firmware's overload protection
is the candidate that fits the symptom best: a jaw stalled against the adapter at full command draws
sustained current; when the load exceeds `Protective_Torque` for longer than `Protection_Time` the
servo sets status bit 32 (overload), drops its output to `Overload_Torque`, and keeps reporting the
error on every packet until the condition clears. The library turns that status into an exception on
the next write, which is the torque-disable at shutdown. The 40-step "not following" episodes are
what a servo limited to 25% output looks like.

## The diagnostic

`scripts/real/gripper_diagnostic.py` (operator present; writes to the gripper only):

1. `--phase rest`: no writes. Reads, for all six motors, position, load, current, voltage,
   temperature, the status byte, `Torque_Limit`, `Max_Torque_Limit`, `Protection_Current`,
   `Protective_Torque`, `Protection_Time`, `Overload_Torque`, `Over_Current_Protection_Time`,
   `Unloading_Condition` and the PID coefficients, and prints the gripper's limits beside the other
   joints. Run it twice: before and after one `run_policy_real.py --dry-run` connect, to see the
   reconfiguration happen.
2. `--phase close --hold-seconds 15`: with the adapter between the jaws, closes the gripper from its
   present opening to `--target` (default 2 units, the demonstrations' closed value) at no more than
   `--step` units per 1/30 s, holds, samples every register at `--hz`, then releases torque **while
   still sampling**, so the status byte at the moment the library would raise is on record. Repeat
   with nothing between the jaws (closing on the mechanical stop) and with the supply voltage logged.
3. Power-cycle the servo and repeat `rest`: does the status bit clear only on power cycle?

Each run writes `results/hardware/gripper_diagnostic/<timestamp>_<phase>.jsonl` and a summary JSON.

## Candidates and what would confirm each

| candidate | confirming observation |
|---|---|
| firmware overload protection on a stalled jaw | status bit 32 appears after `Protection_Time` of stall, current near `Protection_Current`, output drops, bit persists until unload or power cycle |
| supply sag under stall | `Present_Voltage` dips below about 11 V during the hold; bit 1 (voltage) rather than 32 |
| thermal | `Present_Temperature` climbing across trials; bit 4 |
| loose horn or binding jaw | position follows command poorly at rest with no load; load register nonzero when free |
| protection threshold that resets on power cycle | bit set after `close`, still set after torque off, cleared after power cycle |

## Findings

*(to be written at the bench; include the JSONL paths, the status byte decoded, and the register
table before and after the follower's reconfiguration)*

## Decision

*(to be written after the findings. If the fix changes `Max_Torque_Limit`, `Protective_Torque`,
`Protection_Time`, the jaw stop or the servo itself, the plant has changed: later sessions are a new
plant version in the records, seeds 0 to 2 are not re-run, and the paper's design-report table gets
a row for it.)*
