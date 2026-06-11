# Data Coverage Map (2026-06-12)

## Status

- kind: coverage audit (manual takeover session); the authoritative gap
  map for C5 ("one policy for all passenger cars") sampling design and
  for the papers' limitation sections.
- claim boundary: inventory only; no result claim beyond cited artifacts.

## Headline

Volume is not the constraint — this program has generated ~250k+ episodes
at ~0.04 s/episode on demand. **Concentration is**: deep coverage of a
single nominal mid-size sedan (1450 kg, 2.8 m wheelbase) within a
within-model band, on two scenario geometries, static obstacles only,
<= 20 m/s, scalar uniform mu. Fine for the scoped self-ID science; the
gap map below is what C5's population claim must close.

## Coverage by axis

| axis | covered (artifacts) | uncovered / C5 gap |
|---|---|---|
| vehicle parameters | nominal sedan +- within-model band: mass 0.85-1.20x (S2 in-flight: 0.70-1.50x), brake/drive 0.80-1.15x (S2: 0.60-1.30x), stiffness 0.65-1.35x, tau to 1.75-2.5x, cg shift +-0.12 m (panels, regime maps, WP1) | **geometry essentially fixed** (wheelbase/lf/lr never varied beyond cg shift); no vehicle-class structure; the 900 kg-3.2 t population envelope (S4) has zero coverage |
| road surface | scalar mu in [0.25, 1.15], continuous + 12-point grids; mid-episode mu steps (all measurement series) | spatially varying mu (split-mu left/right — the canonical ESC scenario); tire-curve shape (tanh fixed; winter/summer shape difference inexpressible); no load transfer (h_cg unused) |
| scenario geometry | family #1 B2K2 (r=900 arc commitment) and family #2 F2C1 (straight asymmetric gap choice), both deeply measured; legacy r=18 drift circle, figure-eight, M3082 4-axis panel | S-curves, multi-obstacle (4 obs slots, only slot 0 ever used), **moving obstacles (rel-vel == 0 everywhere, contract-enforced)**, oncoming traffic, lane-change topologies |
| speed regime | 5-20 m/s; utilization 0.2-0.95 sweeps; overshoot injection to 150% (measurements A/C) | **> 72 km/h zero coverage** (production AEB/AES operates to 130+ km/h); sustained drift equilibria (de-scoped to Phase-3) |
| sensing degradation | ego channels thoroughly: delay (constant/episode-random/piecewise, 100-500 ms), iid Gaussian, AR(1) rho 0.9/0.95, dropout 0.2 (M3215) | geometry-channel degradation (obstacle/boundary perception noise — only binary reveal timing exists); calibration-bias error classes; action-side wrapper built (S1) but never measured |
| temporal structure | episodes 5.7-9.6 s; familiarization prefixes to 15 s (belief decomposition) | minute-scale continuous drives (the real L3.5 scale; per-car identification across the population needs it); cross-episode persistence |
| fidelity | single-track toy (all measurements) + Chrono::Vehicle **Sedan only** spot checks (279 rows, HF4 + minis) | Chrono multi-vehicle zero coverage — Chrono ships multiple vehicle classes and is the natural S4 high-fidelity path |

## Volumes (this takeover session)

Oracle certification 43k rollouts; regime map 11k; degraded regime 23k;
belief decomposition 11.6k; recovery budget 6.9k; WP1 82k; M3215 33k;
family-2 design 16.9k; plus pilots. Generation is effectively free; the
binding resource is sampling-distribution design and per-instance oracle
budgets.

## Known instrumentation risks for S4

1. **Observation normalization constants are nominal-vehicle-tuned**
   (vx/20, ay/15, boundary lookahead 80 m / 20 m scales): a 3 t MPV and a
   light sports car shift the observation distribution under the same
   normalization; at 36 m/s an 80 m lookahead is only 2.2 s of preview.
   An obs-normalization audit must precede any population training.
2. v4's absolute thresholds (e.g. 14 m/s hard-safety gate) may be
   structurally misplaced across classes, not merely mistuned — exactly
   what the C5 four-arm pricing is designed to expose (the RLS arm can
   rescale gains but cannot move structure).

## Priority order for closing (feeds WP-RL prerequisites)

1. S4 population tier + obs-normalization audit (zero training, CPU).
2. Moving obstacles (env engineering: kinematics, collision, label
   re-derivation; >= 1-2 days).
3. High-speed domain (> 20 m/s scenarios; preview/normalization rework).
4. Geometry-channel degradation + split-mu (env/wrapper extensions).
5. Minute-scale drive structure (episode chaining or long episodes).

RL training-data distribution for C5 must be designed directly against
this map; otherwise the population claim dies at review on "trained in a
+-50% neighborhood of one virtual sedan".
