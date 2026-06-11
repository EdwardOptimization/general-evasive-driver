# Family #2 Design Freeze + Clean-Sensing Acceptance (WP0.1, Track F, 2026-06)

## Status

- kind: task-family DESIGN measurement (manual takeover, Phase-2 week-1).
- plan anchor: `docs/research-plan-phase2-capability-boundary-tracking.md` WP0.1;
  thesis: `docs/capability-boundary-tracking-thesis-2026-06.md` Section 8.
- claim boundary: feasibility-audit task-design measurement only. Scripted
  mu-agnostic commitment plans, a per-mu oracle and a belief-free
  threshold-seeker on candidate family-2 geometries; construction VoI and the
  clean-sensing seeker-vs-oracle gap are measured. No driver promotion,
  training, repair-success, gate-validity, paper, or self-ID capability claim.
- pre-registration: `experiments/feasibility_audit/family2_prereg.json`
  (criteria frozen before any run) +
  `experiments/feasibility_audit/family2_prereg_repair1.json` (repair round,
  frozen before the repair run).
- artifacts: `scripts/feasibility_audit/family2_design.py`,
  `experiments/feasibility_audit/family2_spec.json`,
  `runs/feasibility_audit/family2_design/episode_rows{,_repair1}.csv`.

## 1. Pinned direction and a geometric constraint found during design

Pinned (plan WP0.1): large-radius straight (circle R=3000 m; curvature
3.3e-4 1/m, lateral demand at 13 m/s = 0.056 m/s^2 — negligible) + laterally
offset single obstacle = asymmetric gap choice, expressible today through
`obstacle.lateral_offset_range` (env.py:516,551), reusing the per-cell
degenerate-config mechanism from `ramp_policy_voi_regime.py`.

**Constraint (design fact, reported per discipline):** with a free centerline
approach and a single offset disc, the wider gap is always the *nearer* one
(less lateral displacement), so a literal "near-narrow vs far-wide" choice
cannot exist without pinning the approach line off-center. The only
expressible pin today (warmup gate) was rejected by design: gate collision is
metric-only (no env-native failure semantics), and the pinned-line trade-off
collapses to the speed axis anyway (the lateral detour's path-length cost is
negligible). The honest single-obstacle realization of a mu-dependent gap
choice is the **mu-SIGNED open side**: per-cell configs couple the offset
sign to mu, so predicting the correct gap side before reveal requires mu.

## 2. Candidates (<= 3, all reported; knobs frozen in prereg)

Shared: circle R=3000, dt 0.02, v0 = 8 m/s, mu domain [0.25, 1.15] (12-point
grid), all non-mu randomization degenerate, obs72, rewards 40/60,
finish_on_pass, distance jitter U(-0.75, 0.75) keyed `[BASE,777,seed]`,
floor 14.5 m; effective lateral offset additionally inherits the ego reset
radial noise N(0, 0.3) keyed by the same seed (documented; breaks exact
mu<->geometry inversion).

| knob | F2C1_offset_jitter_react | F2C2_mu_signed_gap | F2C3_mu_signed_tight |
|---|---|---|---|
| corridor half-width (track_width) | 3.2 m | 3.0 m | 2.9 m |
| obstacle half-width | 1.0 m | 1.0 m | 1.1 m |
| lateral offset magnitude | 0.8 m | 0.85 m | 0.95 m |
| offset sign rule | coin per seed `[BASE,555,seed]` | +0.85 if mu<0.70 else -0.85 | +0.95 if mu<0.70 else -0.95 |
| mu->d knots (mu 0.30/0.55/0.85/1.15) | 24/40/50/58 m | 24/40/50/58 m | 22/38/48/56 m |
| reveal distance | 9.5 m | 9.5 m | 8.5 m |
| deadline (max_steps) | 5.2 s (260) | 5.2 s (260) | 4.8 s (240) |
| closed-side room (nominal) | 0.5 m | 0.25 m | -0.05 m (blocked) |

## 3. Construction criterion (frozen) and results — MEASURED

Criterion: commitment VoI = per-mu oracle (per-point best of 28 mu-agnostic
plans, selected on stream A) minus best fixed plan, success measured on the
disjoint stream B (12 points x 8 seeds = 96 episodes per readout arm);
bar >= 0.25. Plan family: speeds {4.5..11.5} x side {react, bias_left +1 m,
bias_right -1 m} + 4 swerve-only react plans. 4032 episodes per candidate.

| candidate | VoI_val | oracle_val | best fixed (plan) | fixed failure mode | pass |
|---|---|---|---|---|---|
| F2C1_offset_jitter_react | **+0.406** | 0.927 | 0.521 (swerve_only_v12_react) | collisions 0.479 | PASS |
| F2C2_mu_signed_gap | +0.385 | 0.917 | 0.531 (swerve_only_v12_react) | collisions 0.469 | PASS |
| F2C3_mu_signed_tight | +0.354 | 0.750 | 0.396 (commit_v9.5_bias_right) | timeouts 0.448 | PASS |

All three candidates clear the bar. Winner by the frozen rule (argmax
VoI_val): **F2C1_offset_jitter_react**. Note (inferred): F2C2 carries the
fuller asymmetric-choice semantics and passed within ~0.02 of the winner; it
remains available to the degradation scan as a documented alternate. F2C3's
lower oracle ceiling (0.750, with a 0.0 top point) shows its tightening also
prices the oracle, not only the fixed plans.

## 4. Clean acceptance on the winner — MEASURED

Readout: threshold-seeker (shortfall detector reused from
`ramp_policy_voi_regime.py`; tau/rate/backoff/dv re-selected for this family
on stream C) vs per-mu parametric oracle (dv per point on C); validation on
stream D: 12 points x 10 seeds = 120 episodes/arm. Bar: gap <= 0.05 +
oracle-strength guard (oracle >= plan-family oracle on D - 0.02).

**Round 0 (brake-ramp seeker family only): FAIL.** Oracle 1.000 vs seeker
0.850, gap +0.150. Diagnosis (measured): identification was essentially
perfect (mu_hat abs err 0.0003, censoring 0.0, side prediction 1.0); losses
concentrated at the top-mu points (per-point 0.6 and 0.0), timeouts 0.10 vs
collisions 0.05. Mechanism: the B2K2-style brake-first ramp pays a ~1 s
speed dip; at d(1.15)=58 m / 5.2 s (mean-speed floor 11.2 m/s) that dip is
fatal, while B2K2 (52 m / 5.7 s) had the slack to absorb it.

**Repair round 1 (pre-registered addendum, one shot): PASS.** Change scoped
to the seeker controller family only: added a `drive_ramp` seek style —
settle, then throttle-force ramp; drive-side shortfall onset identifies mu
*while the deadline-useful acceleration is running*. Physics: MAX_DRIVE
8200 N exceeds the rear tire limit 0.98*mu*Fzr <= 7727 N over the whole mu
domain, so drive-side onset covers every cell with zero actuator censoring.
Declared deviation: the parent prereg scoped repairs to "speed-law
constants/dv grids"; a new seek style is a controller-family extension
slightly beyond that wording — declared in the addendum BEFORE the run.

| arm | success (stream D, n=120) | Wilson 95% | collisions | timeouts |
|---|---|---|---|---|
| per-mu oracle (dv per point) | 1.000 | [0.969, 1.000] | 0.000 | 0.000 |
| best seeker `seeker_drive_r6000_t0.08_b0.06_v+0.75` | 0.983 | [0.941, 0.995] | 0.017 | 0.000 |

- **gap = VoI(belief | clean) = +0.0167 <= 0.05 -> PASS** (per-point seeker
  success 1.0 everywhere except 0.9 at mu points 9/12 and 10/12).
- oracle-strength guard: 1.000 >= 0.9417 (plan-family oracle on D) - 0.02 ->
  PASS; commitment VoI re-measured on stream D: 0.350 (plan oracle 0.942 vs
  best fixed 0.592).
- seeker telemetry: mu_hat abs err 0.0002 (uncensored), censored fraction
  0.0, id_step mean 47.4 (~0.95 s), no reliance on the brake ramp.

Interpretation (inferred, scoped): the clean-sensing half of the two-regime
law replicates on family #2 — a belief-free embedded-identification seeker
matches the per-mu oracle to within 0.017 once identification rides the
family's *useful* action (throttle here, brake in B2K2). The round-0 failure
is a transfer lesson about seeker design, not measured belief value; it is
itself thesis-consistent ("identification embedded in the useful action").
The degraded-regime readout on this family is the next stage (Track W modes
first) and is explicitly out of this track's scope.

## 5. Seed discipline — MEASURED (statically verified)

`seed = 20260624*10 + 17*point + 1000*k + offset`, offsets A=0 (construction
selection), B=100000 (construction validation), C=300000 (acceptance
selection), D=600000 (acceptance validation). Pairwise overlap verified 0
over the full index envelope; in-stream span 9187 << offset spacing. Jitter
keys `[20260624,777,seed]` (distance), `[20260624,555,seed]` (F2C1 side
coin). SEED_BASE 20260624 fresh (prior streams 20260611-20260622).

## 6. Env expressiveness gaps (for the env backlog)

1. mu-correlated obstacle distance AND mu-signed lateral offset both require
   per-episode mixtures of degenerate configs; one config cannot couple
   `randomization.mu_range` with `obstacle.distance_range` /
   `lateral_offset_range` (B2K2 gap, now on two knobs).
2. Ego reset radial noise N(0,0.3) leaks into the obstacle's effective
   lateral offset (obstacle placed relative to the reset pose); a
   track-frame-anchored placement knob would decouple geometry jitter from
   reset noise.
3. `warmup_gate` collision is metric-only — gate-based approach-line pinning
   cannot be expressed with env-native failure semantics.

## 7. Final spec (degradation-scan-ready)

`experiments/feasibility_audit/family2_spec.json` `final_spec` block:
family_id `F2_F2C1_offset_jitter_react`, status **frozen**; full env-knob
table; construction criterion numbers; clean acceptance numbers (round 1);
adapter notes (compose `observation_degradation` via
`autodrift.observation_degradation_wrapper.make_env_from_config`; rebuild
envs via `family2_design.py::env_config`; controllers `Family2Ramp`
oracle/seeker with per-cell tau re-calibration; reserve a NEW SEED_BASE for
the scan — 20260624's A-D streams are consumed).

Compute: 16,896 episodes total (13,920 main + 2,976 repair), ~8 min CPU,
single managed background process per run, polled to completion.
