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
| vehicle parameters | nominal sedan +- within-model band: mass 0.85-1.20x (S2 in-flight: 0.70-1.50x), brake/drive 0.80-1.15x (S2: 0.60-1.30x), stiffness 0.65-1.35x, tau to 1.75-2.5x, cg shift +-0.12 m (panels, regime maps, WP1); M3220 A1 rider sampled cg shift about +-0.42 m and Iz 0.6-1.6x in current-sim and found 0/4 qualifying cells | **vehicle-class structure still unpriced**: wheelbase classes, load transfer, tire-curve shape, and high-fidelity multi-vehicle dynamics remain uncovered; the 900 kg-3.2 t population envelope is not yet covered by Chrono pricing |
| road surface | scalar mu in [0.25, 1.15], continuous + 12-point grids; mid-episode mu steps (all measurement series) | spatially varying mu (split-mu left/right — the canonical ESC scenario); tire-curve shape (tanh fixed; winter/summer shape difference inexpressible); no load transfer (h_cg unused) |
| scenario geometry | family #1 B2K2 (r=900 arc commitment) and family #2 F2C1 (straight asymmetric gap choice), both deeply measured; legacy r=18 drift circle, figure-eight, M3082 4-axis panel | S-curves, multi-obstacle (4 obs slots, only slot 0 ever used), **moving obstacles (rel-vel == 0 everywhere, contract-enforced)**, oncoming traffic, lane-change topologies |
| speed regime | 5-20 m/s; utilization 0.2-0.95 sweeps; overshoot injection to 150% (measurements A/C) | **> 72 km/h zero coverage** (production AEB/AES operates to 130+ km/h); sustained drift equilibria (de-scoped to Phase-3) |
| sensing degradation | ego channels thoroughly: delay (constant/episode-random/piecewise, 100-500 ms), iid Gaussian, AR(1) rho 0.9/0.95, dropout 0.2 (M3215) | geometry-channel degradation (obstacle/boundary perception noise — only binary reveal timing exists); calibration-bias error classes; action-side wrapper built (S1) but never measured |
| temporal structure | episodes 5.7-9.6 s; familiarization prefixes to 15 s (belief decomposition) | minute-scale continuous drives (the real L3.5 scale; per-car identification across the population needs it); cross-episode persistence |
| fidelity | single-track toy (all measurements) + Chrono::Vehicle **Sedan only** spot checks (279 rows, HF4 + minis); M3218 inventory confirms Chrono resources for multi-vehicle/tire extension; M3219 reset/step-smoked default Sedan plus explicit BMW_E90/UAZBUS selectors | Chrono multi-vehicle zero pricing rollout coverage — selector exists, but S4 pricing still needs a frozen preregistration and a declared handling of unmapped `lf/lr/iz/cf/cr` |

## Volumes (this takeover session)

Oracle certification 43k rollouts; regime map 11k; degraded regime 23k;
belief decomposition 11.6k; recovery budget 6.9k; WP1 82k; M3215 33k;
family-2 design 16.9k; plus pilots. Generation is effectively free; the
binding resource is sampling-distribution design and per-instance oracle
budgets.

## Known instrumentation risks for S4

1. **Observation normalization constants are nominal-vehicle-tuned and now
   measured as a blocker** (`docs/m3221-a2-obs-normalization-audit.md`):
   road_y/20 saturates on curved far-boundary points, high-speed ego
   speed/accel scales saturate, obstacle rel-vy/12 saturates with
   ego-relative obstacle mode, and 40 m road preview is only 1.11 s at
   36 m/s. Population or high-speed training needs a follow-up
   normalization/preview implementation first.
2. v4's absolute thresholds (e.g. 14 m/s hard-safety gate) may be
   structurally misplaced across classes, not merely mistuned — exactly
   what the C5 four-arm pricing is designed to expose (the RLS arm can
   rescale gains but cannot move structure).

## Priority order for closing (feeds WP-RL prerequisites)

1. Normalization/preview implementation and smoke before any population or high-speed training; the A2 audit is complete and found a blocker. S4 current-sim cg/Iz rider is closed negative (M3220), A3 C5-prime target consolidation is confirmed for CP-1 review (M3222), and Chrono S4 pricing still needs its own frozen pre-registration.
2. Moving obstacles (env engineering: kinematics, collision, label
   re-derivation; >= 1-2 days).
3. High-speed domain (> 20 m/s scenarios; preview/normalization rework).
4. Geometry-channel degradation + split-mu (env/wrapper extensions).
5. Minute-scale drive structure (episode chaining or long episodes).

RL training-data distribution for C5 must be designed directly against
this map; otherwise the population claim dies at review on "trained in a
+-50% neighborhood of one virtual sedan".
