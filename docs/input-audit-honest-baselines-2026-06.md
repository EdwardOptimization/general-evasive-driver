# Rigorous input audit + honest baselines for the full-spectrum avoidance driver (2026-06-18)

Motivation: the first "RL vs rule-based" comparison used `envelope_aes` (0.870) as the "strongest rule" WITHOUT
auditing its inputs. It cheats. This document audits, INPUT BY INPUT, what is realistically obtainable, and rebuilds
the comparison on equal, realistic footing.

## What the RL driver actually observes (verified in src/autodrift/env.py)
- ego proprioception: vx, vy, yaw_rate, ax, ay, steer, steer_rate, throttle/brake actuator states (IMU/encoders).
- road-lane lookahead points (lane geometry, map/lane perception).
- previous own action (known command).
- obstacle slot: body-frame position (x,y) + relative velocity + half-width, GATED by
  `_obstacle_perception_visible` (env.py:882) -> appears only when in sensor range (radar/camera).
- **mu EXCLUDED** by default (env.py:453 "Observation excludes mu", include_privileged_params=False); policy must
  INFER friction. **No obstacle_label. No required-offset. No future prediction.**
=> the RL uses ONLY realistic inputs. CLEAN.

## Info-field provenance (what a baseline COULD read)
| field | source (env.py) | realistic? |
|---|---|---|
| mu | params.mu = TRUE friction (1367) | NO -- privileged |
| obstacle_label | ground-truth feasibility class (1416) | NO -- privileged (answer key) |
| obstacle_required_lateral_offset | precomputed exact clearance (1436) | NO -- privileged |
| obstacle_predicted_lateral_offset_at_arrival | future position (1427) | NO -- privileged |
| obstacle_distance, obstacle_lateral_offset | obstacle CURRENT position (1432-1434), gated by perception_visible | YES -- perception |
| lateral_error, heading_error | own lane pose (1404-1405) | YES -- localization |
| obstacle_perception_visible | sensor-range gate (1413) | YES (the gate) |

## Baseline audit (src/autodrift/policies.py)
- `aeb` (full braking [0,-1,1]): reads NOTHING. CLEAN (trivial).
- `aes_heuristic`: reads `obstacle_required_lateral_offset` -> PRIVILEGED -> INVALID.
- `envelope_aes`: reads `mu` (true) + `obstacle_required_lateral_offset` + **`obstacle_label`** (throttle switched on
  the answer key) -> TRIPLE-PRIVILEGED -> INVALID. (Its 0.870 is meaningless as a "rule baseline".)
- `honest_aes` (NEW, this audit): reads ONLY obstacle_distance + obstacle_lateral_offset (gated on
  perception_visible) + lateral_error + own speed; FIXED assumed mu (not the true mu); NO label; steer hard-capped.
  CLEAN.

## Honest comparison (all_avoidable, 200 eps, per-bucket)
| bucket (n) | RL (clean obs) | honest_aes (clean) | aeb (clean) | envelope_aes (PRIVILEGED, invalid) |
|---|---|---|---|---|
| aeb_feasible (112) | 1.000 | 0.473 | 0.161 | 0.821 |
| aes_feasible (20)  | 1.000 | 0.200 | 0.150 | 1.000 |
| drift_required (68)| 0.912 | 0.456 | 0.206 | 0.912 |
| OVERALL            | **0.970** | 0.440 | 0.175 | 0.870 (invalid) |

## Findings
1. The RL is CLEAN (no mu, no label, obstacle via gated perception) -- verified, not assumed.
2. The previously-headlined "strongest rule" envelope_aes (0.870) CHEATS with true mu + exact required-offset + the
   ground-truth label. Invalid. aes_heuristic also reads the privileged required-offset.
3. Against HONEST (non-privileged) baselines the RL wins much more cleanly: 0.970 vs 0.440 (honest_aes) vs 0.175 (aeb).
4. honest_aes still shows high sideslip (0.515): a fixed non-privileged rule trying to avoid on unknown-low-mu
   SLIDES (it can't operate at the limit without knowing/feeling mu). A truly never-slide rule would be too gentle
   to avoid. The RL (sideslip 0.155) CONTROLS the slide via closed-loop response -- it feels mu from the reaction.
   This is the real reason "no stable production rule can do this": you must close the loop on the vehicle's
   response, which is exactly what the learned policy does and a fixed feedforward rule cannot.

## HONEST CAVEATS (process discipline -- do not over-claim)
- honest_aes is ONE hand-built clean baseline, not provably the strongest non-privileged controller. A stronger
  honest baseline (online mu estimation + limit control) could do better -- but that is essentially what the RL
  learns. The right framing: the non-privileged ceiling requires feeling mu; the RL reaches it by learning.
- The `aeb` baseline collides even on many aeb_feasible cells (0.78) -- suggests the conservative feasibility LABELS
  are loose and/or the simple AEB policy + pass-semantics (success = PASS the obstacle, not just stop) penalise pure
  braking. The labels/metric deserve their own audit before any headline CI claim.
- Process lesson: audit every input's realism BEFORE running the comparison, not after. This audit should gate any
  future "RL beats rule-based" statement.
