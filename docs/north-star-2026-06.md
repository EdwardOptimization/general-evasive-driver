# AutoDrift North Star (2026-06-17)

**ONE obs72 gated RL driver, across ALL scenarios × ALL vehicle types, each at 1.0, trained fast on a
FAITHFUL Chrono-GPU rewrite.** Crystallised by the user; every piece de-risked this session (not a wish).

## The four pieces — status
1. **Chrono GPU rewrite (faithful + fast + cross-vehicle).** PROVEN: drift physics rewrite passes
   (β@24 0.0295, all measured), transfers to Chrono 1.0, ~2400× faster. The architecture: translate
   Chrono's TEMPLATE framework (a vehicle = config-of-templates; concrete vehicle classes are pure param
   containers). Tier-a = chassis 6-DOF + 4 kinematic corners (lookups from the Chrono linkage, step-1 DONE)
   + TMeasy + driveline + masked gear-FSM, branchless/differentiable. NEXT: assemble the corner+chassis
   model → validate vs Chrono ramp/step-steer → a 2nd vehicle to prove cross-vehicle.
2. **Multi-vehicle, all-scenario.** Cross-vehicle by construction (template = config; validate the
   FRAMEWORK once, not per vehicle). All-scenario = the coverage spectrum (drift β×μ×sustain + avoid
   reveal×μ + vehicle variants + sensing), affordable on the GPU rewrite.
3. **Engineering training methods (the KEY).** PROVEN: distillation (master each regime separately →
   gated student, NO interfering joint-PPO) → do-both; multi-seed sweep + Chrono-task-score selection;
   DAgger (in flight) to close the imitation gap → 1.0. This is what turns "regimes fight" into "one
   driver does all" — the user's "分别学会再合并" insight, validated.
4. **drift + avoid both 1.0.** drift 1.0 ✓ (transfers); avoid 0.700 (canonical) → 0.825 (distillation)
   → 1.0 (DAgger, in flight). Then extend across the spectrum.

## Honest open questions (do NOT hand-wave "1.0 everywhere")
- **Physical ceiling:** some cells are at the limit — even the oracle is < 1.0 (the residual physically-
  unavoidable rows). Honest target = 1.0 WHERE PHYSICALLY ACHIEVABLE; the oracle ceiling is the bound.
- **Tier-a faithfulness:** it's a kinematic-reduced suspension, not the full linkage — must be validated
  against Chrono (ramp/step-steer); Tier-b (full-linkage DAE) is the fallback if compliance matters.
- **Recipe at N regimes:** N experts → one gated student; the gate must route N regimes cleanly — verify
  as the spectrum grows beyond 2.

## Concrete roadmap
- M1 [in flight] DAgger: avoid 0.825 → ~1.0, drift held → the both-good driver at full strength.
- M2 Tier-a build: assemble chassis-6DOF + 4 kinematic corners (+ damper extract) + TMeasy/driveline →
  validate vs Chrono (Sedan ramp/step-steer + a drift + an avoid episode) → cross-vehicle (2nd vehicle config).
- M3 Coverage spectrum: per-cell experts → distill into one gated driver → DAgger each to its physical
  ceiling → one full-scenario driver.
- M4 Cross-vehicle: repeat M3 across vehicle configs (the template generality).
Papers fall out: the GPU template-rewrite (methods) + the do-both distillation recipe (the "RL CAN do both"
result) + the conditional-negative-result science (when surrogate training over/under-fits).

---

## Piece ② cross-vehicle — scoped (2026-06-17)

Chrono backend is ALREADY a registry-driven multi-vehicle engine (CHRONO_VEHICLE_VARIANTS: sedan/bmw_e90/
uazbus; obs/collision/diagnostics vehicle-agnostic — adding a vehicle = 1 registry entry). The DO-BOTH
recipe transfers in STRUCTURE but needs per-vehicle re-physicalization:
- **CRUX RISK: the avoidance oracle is Sedan-FITTED** (hardcoded V_KNOTS safe-entry-speed, FZR rear load,
  mass in ramp_policy_voi_regime.py). It runs on UAZBUS but its plan is systematically wrong -> each
  vehicle needs its avoid oracle re-physicalized (re-measure safe-entry-speed vs mu, recompute FZR/mass).
- Drift surrogate: 6 extraction scripts + gpu_physics_pwr are Sedan-hardcoded (literals + the suspension-
  extraction casts to DoubleWishbone/MultiLink + the FWD traction-cap — RWD/4WD needs the cap on the
  other axle). Drift CELL params (mu/speed/beta) need per-vehicle re-tuning to land the controllable-drift
  regime; the drift TEACHER (DriftFeedbackPolicy) carries no mass/grip literals (gains re-tunable) = lower risk.
- F2 scripts hardcode VARIANT="sedan_tmeasy" + mass 1684 -> must thread the variant + per-vehicle params.
Recommended 2nd vehicle: UAZBUS (registered; heavy RWD/4WD high-CG = genuine contrast). Effort ~12-18 days.

DE-RISK FIRST (before the full build): prove both oracles generalize to UAZBUS — (a) re-tune its drift
cell + run the drift feedback teacher → controlled_drift sustain≥24? (b) re-physicalize the avoid oracle
(measure UAZBUS safe-entry-speed + FZR) → avoid success on UAZBUS? If both clear, the rest is plumbing +
the proven distill+DAgger recipe; if not, the blocker is found cheaply.

---

## ② cross-vehicle DE-RISKED on UAZBUS (2026-06-17): both teachers generalize → recipe is cross-vehicle

Ran the two make-or-break de-risks on UAZBUS (2858 kg RWD/4WD high-CG, genuine contrast to the FWD Sedan;
cross_vehicle_uazbus_drift_derisk.py / cross_vehicle_uazbus_avoid_derisk.py, verified by my own run):
- **DRIFT: UAZBUS drifts** — controlled_drift sustain **90/90** (≥24 needed) at a re-tuned cell (μ0.25, v6,
  the E4 criterion). The drift FEEDBACK teacher generalizes with cell re-tuning (it carries no mass literals).
  (At μ0.30 it's harder, sustain 15-35 — a real physical gradient, so the measurement is genuine.)
- **AVOID: the oracle avoids on UAZBUS = 1.000.** Measured UAZBUS FZR=14463 N (vs Sedan-fitted 6858) +
  V_KNOTS=(9.5,11,11,11) (vs Sedan (4.5,7.5,9.5,10.5)). The re-physicalized oracle scores 1.000 — AND so
  does the UN-modified Sedan-fitted oracle (the avoidance grid has enough margin that the mis-calibration
  doesn't cause failures). So the crux risk (Sedan-fitted oracle) is RETIRED; re-physicalization is a
  refinement, not a blocker.

**VERDICT: cross-vehicle is VIABLE and likely CHEAPER than the 12-18d estimate.** Both teachers generalize;
the avoid oracle works un-modified; the drift feedback teacher (sustain 90) may suffice for distillation
WITHOUT re-extracting the surrogate per vehicle (the 4-6d surrogate part). So the UAZBUS do-both build is
mostly PLUMBING (thread the variant + UAZBUS params + the re-tuned drift cell through F2/distill/DAgger) +
the proven distill→DAgger recipe → a UAZBUS gated do-both driver. The recipe is cross-vehicle by config.
