# M3273 Phase-5 H3 Planar Dynamic Recovery Certificate

Date: 2026-07-10

## Decision

**Completed / no strict witness at canonical quick; full was not run.** All
nine compact-model branch states were eligible deep slides, but neither the
zero-steer baseline set nor any added countersteer policy recovered any state.
The frozen quick strict-count and friction-coverage gates failed.

## Evidence health

- all three M3266 planar source-prefix hashes remained frozen;
- physical zero pedals mapped to normalized `-1`;
- the six baseline policies were an exact subset of the 30 expanded policies;
- 270/270 candidate rows were written;
- complete branch states, including steer and drive force, matched across
  policies;
- weak recovery-set inclusion passed;
- 18/18 selected winner replays were exact.

The invalid normalized-action counts in
`scripts/audits/recovery_reachability.py` are not used.

## Quick results

All nine branch states passed four-frame beta dwell and rear-slip truth. Their
absolute body sideslip ranged from `0.329` to `1.531 rad`; rear slip angle ranged
from `0.433` to `1.539 rad` across `mu=0.35/0.60/0.90`.

| mu | eligible branches | baseline recoveries | expanded recoveries | strict witnesses |
|---:|---:|---:|---:|---:|
| 0.35 | 3/3 | 0/3 | 0/3 | 0/3 |
| 0.60 | 3/3 | 0/3 | 0/3 | 0/3 |
| 0.90 | 3/3 | 0/3 | 0/3 | 0/3 |

The dominant completion was spin. Added steering sometimes changed which
failed trajectory was closest to recovery, but no expanded policy achieved the
ten-frame stable recovery condition at forward speed >=4 m/s.

## Combined post-slip inference

M3271 showed that direct body-state injection did not initialize valid tire
slip. M3272 corrected this with continuous Chrono branches and found moderate
slides recoverable by zero-steer throttle or braking, with 0.00 s added-steering
advantage. M3273 tested deeper, complete-state compact-model branches and found
them unrecoverable by both control sets.

Therefore the current experiments do **not** establish strict post-slip
recovery-set expansion. They identify three regimes instead:

1. invalid injected slide states, which cannot support a claim;
2. moderate real slides recoverable without steering-based drift management;
3. deep compact-model slides beyond every tested recovery policy.

The theorem-level nested-control inclusion remains valid, but strictness needs a
constructive witness that this project has not found. No more local post-slip
policy, branch, threshold, or model repair is admitted under the current priced
evidence.
