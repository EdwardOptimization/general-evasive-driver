# Foundation audit: the "drift_required" label is built on a 2x-wrong conventional-grip assumption (2026-06-18)

The whole "RL drifts to avoid where rule-based active safety can't" result rests on the scenario LABEL model
(src/autodrift/scenarios.py classify_obstacle_scenario), which buckets each obstacle scenario as
aeb_feasible / aes_feasible / drift_required / unavoidable from three mu-fractions:
- brake_mu_fraction = 0.90 (longitudinal). Reasonable (ABS ~0.9-1.0).
- conventional_lateral_mu_fraction = 0.42 (the lateral accel "conventional steering" can use).
- drift_lateral_mu_fraction = 0.85 (the lateral accel a "drift" can use).
drift_required := required lateral offset is beyond the 0.42*mu*g capacity but within the 0.85*mu*g capacity.

## What the env ACTUALLY delivers (measured, scripts/audits/measure_env_lateral_capacity.py)
Peak lateral SPECIFIC FORCE fy_body/m (the real tire capability, from env.last_forces; friction-circle-capped in
dynamics.py:238-246), conventional (sideslip<0.10) vs drifting:
| mu | conventional /mu*g | drift /mu*g |
|---|---|---|
| 0.35 | 0.78-0.86 | 0.99 |
| 0.60 | 0.90 | 0.98 |
| 0.90 | 0.95 | 0.95 |
=> conventional steering reaches ~0.78-0.95*mu*g, NOT 0.42. Drift reaches ~0.95-0.99 -- only ~0.1*mu*g more, and at
high mu ZERO advantage. The label's 0.42 understates conventional grip by ~2x; the label's premise that drift gives
2x the lateral capacity (0.85 vs 0.42) is false in this env (both cap near mu*g, as physics requires).

## Consequence: the drift_required bucket is mostly an artifact
Re-labeling 4000 scenarios (speed 12-16, mu 0.25-1.15, dist 5-24, hw 0.45-1.15):
| thresholds | aeb_feasible | aes_feasible | drift_required | unavoidable |
|---|---|---|---|---|
| ORIGINAL (0.42 / 0.85) | 0.371 | 0.040 | **0.205** | 0.384 |
| env's real capacity (0.85 / 0.97) | 0.370 | 0.258 | **0.041** | 0.331 |
| generous-to-drift (0.80 / 0.97) | 0.355 | 0.228 | **0.069** | 0.348 |
=> with the env's true conventional grip, drift_required collapses 20.5% -> ~4%, and that remnant is a thin band
between 0.85 and 0.97*mu*g that conventional limit-steering (peaks ~0.95) largely also clears.

## Verdict
The "drift_required, and RL must drift to avoid where AEB/AES can't" headline was built on a bogus label: most cells
labeled drift_required are clearable by HARD CONVENTIONAL STEERING (no drift). Direct corroboration: the privileged
envelope_aes cleared drift_required at 0.912 with sideslip ~0.002 (NO drift); the RL's sideslip on these cells is not
necessary. In a friction-circle-respecting physics, drift gives ~no peak-lateral-force advantage for simple
obstacle avoidance -- the avoidance envelope is set by mu*N, reachable by conventional limit-steering.

This is a measured NEGATIVE result, not an analysis guess: the drift-to-avoid premise does NOT hold in this env's
physics as the label model claimed.

## What a REAL drift-advantage task would require (if pursued)
Drift's genuine avoidance value is NOT higher peak lateral force; it is (a) faster HEADING rotation (point the
velocity vector away -- matters for specific geometries / very short reaction windows), (b) recovering an
already-initiated slide ("save the car"), (c) combined-slip cases where you must brake AND turn. Any future
drift-to-avoid claim MUST: (1) derive labels from MEASURED env capacity (not 0.42/0.85), and (2) verify by
reachability that a sideslip-bounded non-drift trajectory truly cannot avoid while a drift one can -- not trust an
analytic label. Until then, "RL beats rule-based by drifting to avoid" is unsupported in this simulator.

## Reachability test: does drift EVER beat non-drift on lateral displacement? (scripts/audits/drift_reachability.py)
Simulate the dynamics model directly from straight-line motion; sweep control profiles; compare the MAX lateral CG
displacement reachable by the horizon, NON-DRIFT (max sideslip<0.10) vs DRIFT (>=0.10), across (mu, v) and horizons.

| horizon | drift beats non-drift (of 12 mu,v cells) | best drift gain | note |
|---|---|---|---|
| 0.4s (emergency reaction window) | 0/12 | -9% | drift LOSES everywhere |
| 0.7s | 0/12 | +0.3% | drift loses/ties |
| 1.0s | 1/12 | +5% | marginal |
| 1.5s (no emergency) | 5/12 | +6% | small wins only when there's ample time |

**VERDICT (measured, not assumed): for the CG-displacement / circle-circle avoidance task in this env's physics,
drift provides NO advantage in the emergency regime (short windows) and at most a marginal +6% when there's ample
time. There is NO must-drift-to-avoid regime.** Physically: drift = high slip angle = PAST the tire lateral-force
peak = LESS lateral force = less displacement. Drift's real value (if any) lives in effects this task does NOT model:
extended/angled-obstacle geometry where rotating the body helps, recovering an already-initiated slide, or forced
combined hard-brake-and-turn. None of those is "displace the CG past a point obstacle". So in this simulator the
entire "RL drifts to avoid where rule-based can't" thesis is unsupported -- twice over (bogus label + reachability).

## Box-to-box (OBB) reachability: car-body ROTATION makes drift WORSE, not better (scripts/audits/box_reachability.py)
Upgraded the collision model from CG circle-circle to oriented-box vs box (SAT), so the car's HEADING/rotation enters
the collision. Car 4.4x1.8m. For each scenario, find the smallest obstacle distance D* each regime can still clear
(smaller = better avoidance):
| mu | v | nondrift D* | drift D* | drift edge |
|---|---|---|---|---|
| 0.4 | 12 | 13.5 | 14.0 | -0.5 (worse) |
| 0.4 | 16 | 17.5 | 18.5 | -1.0 (worse) |
| 0.7 | 12 | 10.5 | 11.5 | -1.0 (worse) |
| 0.7 | 16 | 14.0 | 14.0 | tie |
| 1.0 | 12 | 9.5 | (cannot clear) | worse |
| 1.0 | 16 | 12.0 | 12.0 | tie |
Drift clears a >0.4m closer obstacle in 0/6 cells; coarse grid: 0 drift-ONLY-clears of 24. **Body rotation HURTS
avoidance: the yawed (drifting) car's TAIL swings out, sweeping a wider arc -> it needs the obstacle farther away or
fails outright. Non-drift (body aligned with the path) presents the minimal swept footprint.**

## FINAL VERDICT (triple-confirmed, all measured)
"Drift to avoid where rule-based can't" is FALSE in this simulator, confirmed three independent ways:
1. Label audit -- conventional grip understated 2x (0.42 vs measured ~0.85); drift_required collapses 20.5%->~4%.
2. CG reachability -- drift <= non-drift on lateral displacement; 0/12 (mu,v) cells in the emergency window.
3. Box-to-box reachability -- drift clears an EQUAL-or-FARTHER obstacle (0/6 closer), and is strictly WORSE where it
   matters (tail-swing).
For obstacle avoidance, conventional limit-steering DOMINATES drift. Drift's genuine value (if any) is a DIFFERENT
task -- recovering an already-initiated slide ("save the car"), not clearing a newly-revealed obstacle. The RL
driver's real, honest differentiator is learning to operate at the friction limit + infer mu from realistic obs
(beating non-privileged rules that don't know mu) -- NOT drifting. Caveat: planar friction-circle model; a faithful
Chrono multibody (load transfer) could in principle differ, but the planar model is mu*N-faithful so a flip is
unlikely; the honest next step if pursued is to repeat reachability on Chrono.

## Direction 3: FAITHFUL CHRONO confirms (and strengthens) the negative (scripts/audits/chrono_drift_reachability.py)
Closing the only caveat (planar friction-circle vs Chrono multibody). Open-loop maneuvers on the real Chrono backend
at a fixed 16 m/s; max lateral displacement over the horizon, conventional vs PROVOKED drift (power-oversteer /
trail-brake, since plain emergency steering does NOT even induce drift on the faithful vehicle -- it corners at the
grip limit with sideslip<0.10):
| mu | conventional disp | drift disp | drift edge |
|---|---|---|---|
| 0.35 | 1.03 m | 0.57 m | -45% |
| 0.60 | 1.71 m | 1.18 m | -31% |
| 0.90 | 2.43 m | 2.26 m | -7% |
Drift achieves LESS lateral displacement at every mu -- a BIGGER deficit than planar. The reason is the multibody
effect the planar model omits: large load transfer (measured (max-min)/max normal load = 0.45-0.76) unloads a tire
during the aggressive drift -> less total grip -> less displacement; the provoking throttle/brake also spends friction
longitudinally. So the faithful physics closes the caveat in the direction that STRENGTHENS the negative.

Also notable: on faithful Chrono a plain emergency STEER (even full lock at 16 m/s) does not drift at all -- it
corners at the limit. Drift has to be deliberately provoked, and then it is worse. So "drift to avoid" is not even a
behaviour that naturally arises in emergency avoidance on the faithful vehicle.

### Net (4 independent measurements, planar + faithful Chrono): drift is NON-ESSENTIAL (indeed counterproductive) for
### obstacle avoidance while grip is intact. The thesis "drift is unnecessary before the car has started sliding"
### is established by theory (friction circle + load transfer) AND experiment (CG, box, and Chrono reachability).

## Adversarial verification (2026-06-19): negative SURVIVES, 3 reporting flaws fixed, scope gap closed
Ran 4 skeptics (one per measurement) + an adjudicator to try to REFUTE "drift gives no avoidance advantage". Result:
the negative SURVIVES (3 independent tests + Chrono all say no drift advantage; every correction pushes drift WORSE).
Fixes applied:

1. **[threshold artifact -- the one real "would-flip" against the CG test]** The beta>=0.10 rad "drift" classification
   in drift_reachability.py / chrono_drift_reachability.py is tautological: the global-best-displacement maneuver
   (steer~0.35) is itself a ~8-12deg mild-slip maneuver, so it lands in the "drift" bin and inflates "drift wins".
   Threshold sweep: drift gain +12.6% @ beta>=0.05, +5.2% @ 0.10, +0.4% @ 0.15. => the CG-displacement test is NOT
   evidence of a drift ADVANTAGE; the apparent +5% win is a classification artifact that vanishes at a sane
   threshold. CORRECTION: the CG/displacement results are downgraded to "drift <= non-drift" only; the box-SAT and
   Chrono tests carry the load.
2. **[peak-vs-average re-label]** measure_env_lateral_capacity.py reports PEAK ay (~0.95mu*g); the label's d=0.5*a*t^2
   needs AVERAGE ay. Measured avg/peak ~= 0.91 for BOTH regimes, so the GAP (what sets drift_required) stays small.
   Corrected re-label (conv 0.86, drift 0.90): **drift_required ~= 1.9% (range 0.5-2.7%)**, vs the original 20.5% --
   the collapse is robust (more severe, not less; skeptic's 8-12% fear was wrong because both regimes scale together).
3. **[util>1.0 logging artifact]** the Chrono `util` column divides one wheel's peak lateral force by the fleet-max
   normal load (cross-wheel aggregation), so it can exceed 1.0 -- a logging artifact, NOT a physics violation
   (per-tire friction-circle saturation is enforced). util is explanatory garnish; the conclusion rests on
   displacement (cmax vs dmax). Treat util as unreliable / drop it.

### Decisive scope gap CLOSED -- angled + extended obstacles (scripts/audits/box_reachability_angled.py)
The one untested geometry where theory said body-rotation (drift) COULD help: oriented obstacles psi in {30,45,60}deg,
depth hd in {1.5,2.5}m, oriented-box SAT, binary-search min clearable D* per regime:
**drift clears a >0.4m-closer obstacle in 0/12 angled/deep cells.** Non-drift always equal-or-closer; drift is worse
(tail swing) or CANNOT clear the deep ones at all. => drift gives no advantage even in its best-case geometry. The
negative is closed at FULL scope.

## FINAL (adversarially-verified) CONCLUSION
Across FIVE measurements (lateral-capacity/label, CG reachability, axis-aligned box-SAT, angled+extended box-SAT, and
faithful Chrono multibody), spanning planar and multibody physics and point/oriented/extended collision geometries,
**controlled drift provides NO obstacle-avoidance advantage while grip is intact -- it is equal-or-worse everywhere,
and load transfer / tail-swing make it strictly worse where they bite.** With physically-grounded labels the genuine
"must-drift" fraction is ~2% (not 20.5%). The thesis is established by theory (friction circle + load transfer +
tail-swing) AND experiment, and SURVIVED adversarial attack with only reporting corrections. Drift's real value lies
in a DIFFERENT regime -- recovering an ALREADY-INITIATED slide -- which is direction 1, not obstacle avoidance.
