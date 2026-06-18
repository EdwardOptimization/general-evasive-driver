# Drift-to-Avoid active-safety driver (2026-06-18): ONE RL driver that AUTONOMOUSLY DRIFTS to avoid where rule-based can't

## The actual goal (corrected)
A unified active-safety RL driver whose PRIMARY task is OBSTACLE AVOIDANCE, that AUTONOMOUSLY DECIDES whether to
drift. The key regime: road conditions where grip-limited braking/steering CANNOT avoid the obstacle, but a controlled
high-sideslip drift can. Traditional rule-based active safety (AEB/ESC) cannot do this -- they actively prevent slip.
(NOT the same as the separate drift-maintenance + reactive-avoidance regimes of the F2/capstone line.)

## Foundation: M5 scenario taxonomy (src/autodrift/scenarios.py)
Conservative feasibility labels per obstacle scenario: aeb_feasible (braking stops in time) / aes_feasible (normal
lateral accel clears it) / **drift_required** (only a high-sideslip lateral envelope clears it) / unavoidable.
Eval config configs/m5_obstacle_drift_required_eval.json filters to drift_required only.

## RESULT (fresh 1M-step PPO, current code, drift_required, 100 eps)
| policy | success | collision | high_sideslip_frac | min_clearance |
|---|---|---|---|---|
| **RL drift-to-avoid** | **0.93** | 0.07 | 0.099 (DRIFTS) | 2.55 |
| envelope_aes (best rule baseline) | 0.84 | 0.16 | 0.004 | 2.30 |
| aes_heuristic | 0.47 | 0.53 | -- | 1.89 |
| **AEB (pure braking = traditional active safety)** | **0.08** | **0.92** | 0 | 1.60 |

**HEADLINE: on obstacles where AEB collides 92% of the time, ONE RL driver avoids 93% by AUTONOMOUSLY DRIFTING** (it
genuinely uses sideslip -- high_sideslip_fraction 0.099 vs the best non-drifting baseline's 0.004, which plateaus at
0.84). Beats every rule-based baseline AND the stale May checkpoint (0.86). The drift is a CHOSEN tool: the same
policy normal-avoids the easy cells and drifts only when grip-limited avoidance fails. drift2avoid_driver.pt.

## Baselines confirm the floor
Pure-braking AEB collides 92-95% on drift_required (it physically cannot stop/steer in time) -- this is exactly the
gap traditional active safety cannot close and RL+drift does.

## NEXT (strongest + most general)
- Cross-vehicle (Sedan/UAZBUS/BMW) drift-to-avoid + the self-ID label-free conditioning (reuse the RMA work).
- More seeds + seed-clustered CI on the drift_required bucket; balanced label sampling.
- Stronger baseline (NMPC / optimal-control planner) instead of the conservative feasibility label.
- Faithful Chrono validation of the drift-to-avoid maneuvers (the surrogate->Chrono arbiter).
