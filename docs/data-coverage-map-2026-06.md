# Data Coverage Map (2026-06-13)

## Status

- kind: coverage audit (manual takeover session); the authoritative gap
  map for C5 ("one policy for all passenger cars") sampling design and
  for the papers' limitation sections.
- claim boundary: inventory only; no result claim beyond cited artifacts.

## Headline

Volume is not the constraint — this program has generated ~250k+ episodes
at ~0.04 s/episode on demand. **Concentration is**: deep coverage of a
single nominal mid-size sedan (1450 kg, 2.8 m wheelbase) within a
within-model band, on two scenario geometries, static obstacles mostly,
<= 20 m/s for the deeply measured outcome panels, scalar uniform mu. M3223
adds a flagged constant-velocity crosser env axis, and M3240 prices the
current crosser outcome panel negative. M3224 adds a 36 m/s env-contract
profile, and M3242 prices the current six-cell high-speed outcome panel
negative. M3225 adds geometry-channel degradation and a split-mu
expressibility audit only, M3226 adds a 60 s same-episode drive-structure
smoke only, M3227 adds a Chrono multi-vehicle direction-pricing proxy, and
M3248 freezes the Phase-4 E0 Chrono spread expressibility envelope for
Sedan/BMW_E90/UAZBUS fixtures only. M3251 adds a Sedan-only E2 Chrono
two-regime protocol smoke, M3252 adds the initial full Sedan/TMeasy E2
verdict (clean belief value positive at 9.5 m and 12 m), M3258 hardens E2'
across Sedan/TMeasy and UAZBUS/TMeasy with 30 validation seeds per cell and
confirms the clean flip on both variants, and M3253 adds a Sedan/TMeasy E3
measurement-A/C protocol smoke only, M3254 adds the Sedan/TMeasy E3 tire-truth
telemetry connector smoke, M3255 adds the full Sedan/TMeasy E3
detector-latency and recovery-budget verdict, and M3257 adds the E3-fix
detector-onset reconciliation trace panel: 24/24 case rows, 3426 trace rows,
original early-fire rate 0.5, reconciled early-fire rate 0.0, detector miss
rate 0.1667. M3259 completes the E1' oracle-adequate spread-revival
repricing across Sedan/BMW_E90/UAZBUS with 24 validation units per variant,
0/3 qualifying variants, and a negative pooled `v4_pertuned - fixed_star`
readout. Track F is still not admitted before the later PI GPU-days
checkpoint. Fine for the scoped self-ID science; the gap map below is what
C5's population claim must close.

## Coverage by axis

| axis | covered (artifacts) | uncovered / C5 gap |
|---|---|---|
| vehicle parameters | nominal sedan +- within-model band: mass 0.85-1.20x (S2 in-flight: 0.70-1.50x), brake/drive 0.80-1.15x (S2: 0.60-1.30x), stiffness 0.65-1.35x, tau to 1.75-2.5x, cg shift +-0.12 m (panels, regime maps, WP1); M3220 A1 rider sampled cg shift about +-0.42 m and Iz 0.6-1.6x in current-sim and found 0/4 qualifying cells; M3227 ran a Chrono discrete-variant direction-pricing proxy over Sedan/BMW_E90/UAZBUS and found all three variants reversed for current-sim structured oracle-tail replay; M3248 froze the Phase-4 E0 expressibility table: selected Chrono vehicle fixtures are admitted for E1, total mass is partial via chassis-mass override, load transfer is present as fixture physics, and payload-position/h_cg, tire-family, split-mu, and continuous lf/lr/Iz/cf/cr remain blocked without new connectors; M3259 repriced the selected Sedan/BMW_E90/UAZBUS E1' fixture envelope with oracle adequacy and found 0/3 spread-revival qualifying variants | **vehicle-class structure remains only partially priced**: E1/E1' price the selected Chrono fixtures only, but the 900 kg-3.2 t population envelope is still not a full Chrono outcome panel and independent payload-position/h_cg, tire-family, split-mu, and continuous geometry/inertia/tire axes are not wired |
| road surface | scalar mu in [0.25, 1.15], continuous + 12-point grids; mid-episode mu steps (all measurement series); M3225 audited split-mu expressibility and found it is not physical in the current `DriftObstacleEnv` single-track outcome path; M3254 confirms selected Sedan/TMeasy Chrono tire-truth diagnostics expose per-wheel slip/force and normal load for E3 design; M3255 uses those tire-truth diagnostics for the full Sedan/TMeasy E3 measurement A/C panel; M3257 reuses the same Sedan/TMeasy tire-slip truth for the detector-onset reconciliation trace panel | spatially varying mu (split-mu left/right — the canonical ESC scenario) remains uncovered for outcome panels; M3254/M3255/M3257 do not implement split-mu, tire-family variants, or a split-mu outcome panel |
| scenario geometry | family #1 B2K2 (r=900 arc commitment) and family #2 F2C1 (straight asymmetric gap choice), both deeply measured; legacy r=18 drift circle, figure-eight, M3082 4-axis panel; M3223 adds a flagged constant-velocity crosser smoke with deterministic replay and preserved legacy zero-relvel contracts; M3240 prices the current moving-crosser outcome panel negative (0/4 cells qualified) | S-curves, multi-obstacle (4 obs slots, only slot 0 ever used), oncoming traffic, lane-change topologies; any new moving-obstacle topology needs a new preregistered outcome panel |
| speed regime | 5-20 m/s outcome panels; utilization 0.2-0.95 sweeps; overshoot injection to 150% (measurements A/C); M3224 adds an explicit 36 m/s observation/preview smoke with obs72 preserved, selected channels max abs 0.900, and 2.5 s road preview; M3242 prices the current six-cell high-speed outcome panel negative (0/6 cells qualified; fixed_star/v4_pertuned 46/48) | **> 72 km/h coverage remains sparse beyond the priced six-cell 24/30/36 m/s current formulation** (production AEB/AES operates to 130+ km/h); sustained drift equilibria (de-scoped to Phase-3); any harder high-speed/degraded-sensing rider needs a new preregistered outcome panel |
| sensing degradation | ego channels thoroughly: delay (constant/episode-random/piecewise, 100-500 ms), iid Gaussian, AR(1) rho 0.9/0.95, dropout 0.2 (M3215); M3225 adds config-gated road-boundary and active-obstacle continuous-channel noise with present/size/empty-slot preservation; M3251 smokes a Chrono policy-observation delay25 tight spot with ego channels 0-8 degraded and geometry/command-history channels preserved; M3252 includes one delay25_tight Sedan/TMeasy secondary full-panel spot; M3258 includes the same delay25_tight secondary spot on Sedan/TMeasy and UAZBUS/TMeasy | geometry-degraded outcome panels remain unpriced; calibration-bias error classes; action-side wrapper built (S1) but never measured; Chrono degraded sensing still lacks a broad degraded-regime panel beyond the single delay25_tight secondary spot |
| temporal structure | episodes 5.7-9.6 s; familiarization prefixes to 15 s (belief decomposition); M3226 smoked 60 s same-episode structure with warmup carry-over, later emergency obstacle, raw pass accounting, and post-pass continuation | minute-scale controller outcome panels remain unpriced; cross-episode persistence remains uncovered |
| fidelity | single-track toy (all measurements) + Chrono::Vehicle Sedan spot checks (279 rows, HF4 + minis); M3218 inventory confirms Chrono resources for multi-vehicle/tire extension; M3219 reset/step-smoked default Sedan plus explicit BMW_E90/UAZBUS selectors; M3227 ran 108 preregistered multi-vehicle Chrono direction-pricing episodes and found direction reversed in all three variants; M3231 ran native Chrono oracle direction-pricing on Sedan/BMW_E90; M3248 completed the Phase-4 E0 expressibility audit and admits E1 on selected fixtures only; M3251 passed a Sedan-only E2 protocol smoke, M3252 completed the initial full Sedan/TMeasy E2 verdict for scripted oracle/seeker/fixed arms, M3258 completed the hardened E2' full verdict on Sedan/TMeasy and UAZBUS/TMeasy, M3259 completed the oracle-adequate E1' spread-revival repricing on Sedan/BMW_E90/UAZBUS with 0/3 qualifying variants, M3253 passed a Sedan/TMeasy E3 A/C protocol smoke for obs72 detector traces plus planar overshoot recovery traces, M3254 passed a Sedan/TMeasy E3 tire-truth telemetry connector smoke with 8/8 samples and 32/32 finite wheel rows, M3255 completed the full Sedan/TMeasy E3 detector-latency/recovery-budget panel, and M3257 completed the Sedan/TMeasy E3-fix detector-onset reconciliation trace panel | Chrono coverage is still not full high-fidelity sufficiency: no UAZBUS D1b native oracle search, no independent payload-position/h_cg, tire-family, split-mu, or continuous `lf/lr/iz/cf/cr` mapping, no non-Sedan full E3 verdict, and no learned-policy outcome panel |

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
   CP-1 review (M3222), and D1 Chrono S4-HF-lite direction-pricing is closed
   negative/reversed for the structured current-sim oracle-tail transfer
   proxy (M3227).
2. Moving obstacles outcome panels: B1 env engineering is complete (M3223),
   and the current B1b constant-velocity crosser formulation is priced
   negative (M3240; 0/4 cells qualified). Any new moving-obstacle topology
   still needs preregistered labels, floors, criteria, and seed streams.
3. High-speed outcome panels: B2 env engineering is complete (M3224), and the
   current B2b six-cell M3224-profile formulation is priced negative (M3242;
   0/6 cells qualified). Any high-speed hardening or degraded-sensing rider
   still needs preregistered labels, floors, criteria, and seed streams.
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
