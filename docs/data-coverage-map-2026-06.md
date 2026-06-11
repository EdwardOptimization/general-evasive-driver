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
<= 20 m/s for outcome panels, scalar uniform mu. M3224 adds a 36 m/s
env-contract smoke only, M3225 adds geometry-channel degradation and a
split-mu expressibility audit only, and M3226 adds a 60 s same-episode
drive-structure smoke only, not controller outcome panels. Fine for the scoped
self-ID science; the gap map below is what C5's population claim must close.

## Coverage by axis

| axis | covered (artifacts) | uncovered / C5 gap |
|---|---|---|
| vehicle parameters | nominal sedan +- within-model band: mass 0.85-1.20x (S2 in-flight: 0.70-1.50x), brake/drive 0.80-1.15x (S2: 0.60-1.30x), stiffness 0.65-1.35x, tau to 1.75-2.5x, cg shift +-0.12 m (panels, regime maps, WP1); M3220 A1 rider sampled cg shift about +-0.42 m and Iz 0.6-1.6x in current-sim and found 0/4 qualifying cells | **vehicle-class structure still unpriced**: wheelbase classes, load transfer, tire-curve shape, and high-fidelity multi-vehicle dynamics remain uncovered; the 900 kg-3.2 t population envelope is not yet covered by Chrono pricing |
| road surface | scalar mu in [0.25, 1.15], continuous + 12-point grids; mid-episode mu steps (all measurement series); M3225 audited split-mu expressibility and found it is not physical in the current `DriftObstacleEnv` single-track outcome path | spatially varying mu (split-mu left/right — the canonical ESC scenario) remains uncovered for outcome panels until a backend exposes per-wheel/per-side contacts and normal loads through the executable env path; tire-curve shape (tanh fixed; winter/summer shape difference inexpressible); no load transfer (h_cg unused) |
| scenario geometry | family #1 B2K2 (r=900 arc commitment) and family #2 F2C1 (straight asymmetric gap choice), both deeply measured; legacy r=18 drift circle, figure-eight, M3082 4-axis panel; M3223 adds a flagged constant-velocity crosser smoke with deterministic replay and preserved legacy zero-relvel contracts | S-curves, multi-obstacle (4 obs slots, only slot 0 ever used), preregistered moving-obstacle outcome panels, oncoming traffic, lane-change topologies |
| speed regime | 5-20 m/s outcome panels; utilization 0.2-0.95 sweeps; overshoot injection to 150% (measurements A/C); M3224 adds an explicit 36 m/s observation/preview smoke with obs72 preserved, selected channels max abs 0.900, and 2.5 s road preview | **> 72 km/h outcome coverage still missing** (production AEB/AES operates to 130+ km/h); sustained drift equilibria (de-scoped to Phase-3) |
| sensing degradation | ego channels thoroughly: delay (constant/episode-random/piecewise, 100-500 ms), iid Gaussian, AR(1) rho 0.9/0.95, dropout 0.2 (M3215); M3225 adds config-gated road-boundary and active-obstacle continuous-channel noise with present/size/empty-slot preservation | geometry-degraded outcome panels remain unpriced; calibration-bias error classes; action-side wrapper built (S1) but never measured |
| temporal structure | episodes 5.7-9.6 s; familiarization prefixes to 15 s (belief decomposition); M3226 smoked 60 s same-episode structure with warmup carry-over, later emergency obstacle, raw pass accounting, and post-pass continuation | minute-scale controller outcome panels remain unpriced; cross-episode persistence remains uncovered |
| fidelity | single-track toy (all measurements) + Chrono::Vehicle **Sedan only** spot checks (279 rows, HF4 + minis); M3218 inventory confirms Chrono resources for multi-vehicle/tire extension; M3219 reset/step-smoked default Sedan plus explicit BMW_E90/UAZBUS selectors | Chrono multi-vehicle zero pricing rollout coverage — selector exists, but S4 pricing still needs a frozen preregistration and a declared handling of unmapped `lf/lr/iz/cf/cr` |

## Volumes (this takeover session)

Oracle certification 43k rollouts; regime map 11k; degraded regime 23k;
belief decomposition 11.6k; recovery budget 6.9k; WP1 82k; M3215 33k;
family-2 design 16.9k; plus pilots. Generation is effectively free; the
binding resource is sampling-distribution design and per-instance oracle
budgets.

## Known instrumentation risks for S4

1. **Observation normalization constants are nominal-vehicle-tuned and were
   measured as a blocker** (`docs/m3221-a2-obs-normalization-audit.md`):
   road_y/20 saturates on curved far-boundary points, high-speed ego
   speed/accel scales saturate, obstacle rel-vy/12 saturates with
   ego-relative obstacle mode, and 40 m road preview is only 1.11 s at
   36 m/s. M3224 closes the high-speed env-contract blocker for an explicit
   B2 profile (`vx/40`, `vy/40`, `ax/50`, `ay/60`, `road_y/60`,
   `rel_vy/30`, 2.5 s preview), but this is not an outcome panel or a
   population-training admission.
2. v4's absolute thresholds (e.g. 14 m/s hard-safety gate) may be
   structurally misplaced across classes, not merely mistuned — exactly
   what the C5 four-arm pricing is designed to expose (the RLS arm can
   rescale gains but cannot move structure).

## Priority order for closing (feeds WP-RL prerequisites)

1. Normalization/preview implementation and smoke before any population or
   high-speed training: A2 found the blocker (M3221), and B2 implemented the
   explicit 36 m/s env-contract profile (M3224). S4 current-sim cg/Iz rider is
   closed negative (M3220), A3 C5-prime target consolidation is confirmed for
   CP-1 review (M3222), and Chrono S4 pricing still needs its own frozen
   pre-registration.
2. Moving obstacles outcome panels: B1 env engineering is complete (M3223),
   but any controller measurement on this axis still needs preregistered
   labels, floors, and criteria.
3. High-speed outcome panels: B2 env engineering is complete (M3224), but any
   controller measurement on this axis still needs preregistered labels,
   floors, and criteria.
4. Geometry-channel degradation env engineering is complete (M3225); split-mu
   is not expressible in the `DriftObstacleEnv` single-track outcome path and
   remains a high-fidelity/backend integration gap for outcome panels.
   Geometry-degraded controller outcome panels still require preregistered
   labels, floors, and criteria.
5. Minute-scale drive structure env engineering is complete (M3226); any
   minute-scale controller outcome panel or cross-episode persistence claim
   still requires preregistered labels, floors, criteria, and seed streams.

RL training-data distribution for C5 must be designed directly against
this map; otherwise the population claim dies at review on "trained in a
+-50% neighborhood of one virtual sedan".
