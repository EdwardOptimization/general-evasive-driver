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
