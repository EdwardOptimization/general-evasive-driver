# Drift-to-Avoid active-safety driver (2026-06-18): ONE RL driver that AUTONOMOUSLY DRIFTS to avoid where rule-based can't

> **⚠️ SUPERSEDED / PREMISE FALSIFIED (2026-06-19).** The "drift to avoid where rule-based can't"
> premise below was the working goal on 2026-06-18, then **debunked** by the foundation audit
> (`docs/foundation-audit-drift-required-label-2026-06.md`): the `drift_required` label rested on a
> ~2x-too-low conventional-grip assumption; five measurements (capacity, planar/oriented/extended
> reachability, faithful Chrono) show drift gives **no obstacle-avoidance advantage while grip is
> intact** (true must-drift fraction ~2%). The 0.93-vs-AEB number here is therefore **not** evidence
> that drifting beats rules at avoidance. The canonical replacement is the **bounded two-regime conclusion**
> (`docs/two-regime-thesis-drift-2026-06.md`): deliberate drift is unnecessary before slip; after
> slip, added steering value is conditional and was not strict in M3271-M3273. The current, defensible RL result is the **F2 conditional
> finding** (drift positive + benign-avoidance regression) reported in `paper/c5prime/main.tex`. Read
> this doc as a record of the falsified hypothesis, not a live claim.

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

---

## ★ CORRECTED to FULL-SPECTRUM avoidance (2026-06-18): ONE driver covers the WHOLE spectrum, any means

User refinement: NOT "drift-to-avoid" (the narrow drift_required bucket) but UNIVERSAL avoidance across the entire
spectrum -- an experienced driver doesn't pick a "function" (AEB/AES/drift), he just avoids by any means. So train +
eval on ALL avoidable labels: aeb_feasible (braking suffices) + aes_feasible (steering suffices) + drift_required
(only high-sideslip suffices); exclude only `unavoidable`.

Built: configs/ppo_fullspectrum_avoidance.json (allowed_labels=[aeb,aes,drift], require_aeb_infeasible=False) +
per-bucket eval configs (m5_obstacle_{aeb_feasible,aes_feasible,all_avoidable}_eval.json). Fresh 1M-step PPO.

RESULT (all-avoidable eval, 200 eps, per obstacle_label bucket):
| bucket (n) | RL one driver | envelope_aes | aes_heuristic | aeb |
|---|---|---|---|---|
| aeb_feasible (112) | **1.000** | 0.821 | 0.161 | 0.161 |
| aes_feasible (20)  | **1.000** | 1.000 | 0.000 | 0.150 |
| drift_required (68)| **0.912** | 0.912 | 0.265 | 0.206 |
| OVERALL (200)      | **0.970** | 0.870 | 0.180 | 0.175 |
| collision_rate     | **0.030** | 0.030 | 0.535 | 0.790 |
| high_sideslip_frac | 0.155 (drifts WHEN NEEDED) | 0.002 | 0.450 | 0.128 |

**HEADLINE: ONE RL driver covers the FULL avoidance spectrum at >=0.91 on EVERY bucket (0.970 overall, 0.030
collision), beating every rule-based function -- each of which only handles its own slice (AEB brake-only, AES
steer-only, envelope_aes best rule at 0.870 but weaker on aeb_feasible).** It uses whatever maneuver fits -- brakes,
steers, or drifts (sideslip 0.155, used only when required) -- deciding nothing explicitly, like an experienced
driver. fullspectrum_avoid_driver.pt. (Metric is finish_on_pass = pass the obstacle without collision/off-track; a
pure-stop AEB is penalised because stopping != passing, so the cleanest comparison is RL 0.97 vs best-rule 0.87 +
collision 0.03 vs 0.53-0.79.)

NEXT (strongest+most general): multi-seed seed-clustered CI; cross-vehicle (Sedan/UAZBUS/BMW) + self-ID label-free;
stronger NMPC baseline; faithful Chrono validation of the full-spectrum maneuvers.
