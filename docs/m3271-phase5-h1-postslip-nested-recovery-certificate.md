# M3271 Phase-5 H1 Post-Slip Nested Recovery Certificate

Date: 2026-07-10

## Decision

**Completed / inconclusive at canonical quick; full was not run.** The action,
set-nesting, matched-reset, runtime tire-telemetry, weak-inclusion, and exact-
replay gates passed. The initialized-slide truth gate and both mirrored strict-
witness gates failed, so the preregistered stop rule blocks full.

## Corrected action semantics

M3271 correctly maps physical `(steer, throttle, brake)=(0,0,0)` to normalized
`(0,-1,-1)`. All six zero-steer baseline policies are members of the expanded
30-policy set, and no candidate uses simultaneous pedals. Uniform braking is
not labeled ESC.

The older `scripts/audits/chrono_recovery.py` and
`scripts/audits/recovery_reachability.py` counts remain inadmissible: they used
normalized pedal zero as though it meant physical zero, when it commands 50%
pedal in this model contract.

## Quick results

| initialized state | reset beta | reset rear slip | baseline recovers | expanded recovers | strict witness |
|---|---:|---:|---|---|---|
| beta +0.8, yaw +3.5 | +0.8001 | 0.00136 | no | no | no |
| beta -0.8, yaw -3.5 | -0.8001 | 0.00136 | yes, coast at 0.54 s | yes | no |

The configured body beta and yaw matched on all 60 candidate rows, and each
cell/seed had one exact initial-state hash. However, rear tire slip at reset was
only `0.00136 rad`, far below the frozen `0.15 rad` already-sliding threshold.
The direct body-state reset did not initialize a dynamically consistent tire-
slip state. The strong sign asymmetry further makes this injected-state panel
unsuitable for a mirrored recovery claim.

All four selected winner replays were bit-exact. The expanded set weakly
contained every observed baseline recovery by construction, but neither quick
cell supplied a strict set-difference witness.

## Gate disposition

| gate | result |
|---|---|
| physical pedal contract | PASS |
| baseline strict subset of expanded set | PASS |
| 60/60 candidate rows | PASS |
| configured reset beta/yaw match | PASS |
| matched initial hashes | PASS |
| runtime finite obs and four-wheel telemetry | PASS |
| 4/4 selected winner exact replay | PASS |
| weak recovery-set inclusion | PASS |
| initial rear-slip truth | **FAIL** |
| positive-side strict witness | **FAIL** |
| negative-side strict witness | **FAIL** |
| frozen quick decision | `inconclusive` |

## Consequence

No strict post-slip empirical claim is admitted from M3271, and full is not
run. The next admissible route must price recovery branches reached through a
common continuous Chrono slide-entry prefix, so body, wheel, tire-relaxation,
and road states are inherited rather than injected independently. Thresholds
and policies from M3271 are not silently repaired.
