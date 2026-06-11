# M3215 WP0 Degraded Sweep + Bridge Validation (Phase-2 WP0.2/WP0.3 closing measurement)

Status: completed (harness run
`runs/research/m3215-wp0-degraded-sweep-bridge-validation_20260611T121026Z`,
returncode 0, 18.3 min). Manual-takeover mixed bookkeeping: registered and
executed as a formal harness milestone per the Phase-2 plan
(`docs/research-plan-phase2-capability-boundary-tracking.md`, Section 0).
Branch `phase2_wp0_degraded_sweep`; auxiliary measurement; the engineering
incumbent and `ActiveSafetyReflexDriver` are unchanged.

`self_id_evidence_discipline.claim_level`: `not_applicable`.

## 1. What was measured

Pre-registration (frozen before the `--full` run, echoed into `summary.json`):
`experiments/feasibility_audit/wp0_degraded_sweep_prereg.json`.

- Task surfaces: family #1 = B2K2_final at reveal 9.5 m (seed stream 20260618;
  validation seeds k=0..9, of which k=0,1 extend the `degraded_regime_final`
  anchors); family #2 = frozen `F2_F2C1_offset_jitter_react` (fresh SEED_BASE
  20260625), seeker grid REQUIRED to contain the drive-side (throttle) seek
  style per the family-2 design lesson, brake style competing alongside.
- 10 degradation cells per family: anchors {clean, delay 5/12/25 steps
  (100/240/500 ms), iid noise 0.05} + 5 NEW cells {AR(1) rho=0.9 sigma_eq=0.05,
  AR(1) rho=0.95 sigma_eq=0.05, dropout 0.2, episode_random delay U[5,25],
  piecewise delay [5,25]}; identical `make_env_from_config` wrapper path for
  every cell including clean.
- Primary readout (matched anchor): VoI_matched = same-cell degraded per-mu
  oracle minus floor, floor = max(best belief-free seeker over the per-cell
  re-calibrated detector grid, best fixed plan). 12 mu x 2 selection + 10
  validation seeds = 120 validation episodes/arm/cell; Wilson 95% CIs;
  Newcombe 95% CI on the difference. Clean-anchor VoI reported as secondary.
- Bridge (WP0.2 falsifiable prediction): dL = measurement-A median detection
  latency (sub-limit ramps, task outcomes never consulted) minus clean median;
  prediction = same family's pure-delay VoI curve interpolated at dL
  (miss rate > 0.5 saturates dL to the largest pure-delay anchor). PASS =
  classification (VoI >= 0.15) agreement >= 75% pooled over the 10 new cells
  AND Spearman >= 0.6.
- G-A (pre-registered): family-2 clean VoI_matched <= 0.05 AND >= 3 of 5 NEW
  family-2 cells >= 0.15.

Episodes: 32,832 task episodes + calibration/latency; 20/20 cells at the full
pre-registered budget (no cell dropped; runtime 1097 s, well under the 2.5 h
bar, so the cells-not-seeds budget rule never fired).

## 2. Per-cell results (validation stream, n=120/arm) — MEASURED

### Family #1 (B2K2_final, reveal 9.5 m)

| cell | kind | oracle (matched) | floor (arm) | VoI_matched [Newcombe 95%] | VoI_clean_anchor |
|---|---|---|---|---|---|
| clean | anchor | 0.950 [0.895,0.977] | 0.883 seeker_w1_t0.08 | **+0.067** [-0.005,+0.141] | — |
| delay5 | anchor | 0.908 | 0.575 seeker_w1_t0.08 | **+0.333** [+0.227,+0.431] | 0.375 |
| delay12 | anchor | 0.850 | 0.392 fixed_v9.5 | **+0.458** [+0.342,+0.557] | 0.558 |
| delay25 | anchor | 0.542 | 0.358 fixed_v9.5 | **+0.183** [+0.057,+0.301] | 0.592 |
| noise0.05 | anchor | 0.533 | 0.383 fixed_v9.5 | **+0.150** [+0.024,+0.270] | 0.567 |
| ar1 r0.9 | NEW | 0.308 | 0.325 fixed_v9.5 | **-0.017** [-0.133,+0.100] | 0.625 |
| ar1 r0.95 | NEW | 0.308 | 0.358 fixed_v9.5 | **-0.050** [-0.167,+0.069] | 0.592 |
| dropout0.2 | NEW | 0.950 | 0.867 seeker_w1_t0.08 | **+0.083** [+0.010,+0.160] | 0.083 |
| eprand[5,25] | NEW | 0.483 | 0.467 seeker_w1_t0.08 | **+0.017** [-0.108,+0.141] | 0.483 |
| piecewise[5,25] | NEW | 0.525 | 0.425 seeker_w1_t0.08 | **+0.100** [-0.026,+0.222] | 0.525 |

### Family #2 (F2C1_offset_jitter_react, reveal 9.5 m)

| cell | kind | oracle (matched) | floor (arm) | VoI_matched [Newcombe 95%] | VoI_clean_anchor |
|---|---|---|---|---|---|
| clean | anchor | 1.000 [0.969,1.0] | 0.975 seeker_drive | **+0.025** [-0.010,+0.071] | — |
| delay5 | anchor | 0.942 | 0.975 seeker_drive | **-0.033** [-0.093,+0.021] | 0.025 |
| delay12 | anchor | 0.942 | 0.942 seeker_drive | **+0.000** [-0.065,+0.065] | 0.058 |
| delay25 | anchor | 0.817 | 0.892 seeker_drive | **-0.075** [-0.165,+0.015] | 0.108 |
| noise0.05 | anchor | 0.758 | 0.425 commit_v11.5_bias_right | **+0.333** [+0.211,+0.442] | 0.575 |
| ar1 r0.9 | NEW | 0.650 | 0.483 swerve_only_v12_react | **+0.167** [+0.041,+0.285] | 0.517 |
| ar1 r0.95 | NEW | 0.658 | 0.367 commit_v11.5_bias_right | **+0.292** [+0.166,+0.405] | 0.633 |
| dropout0.2 | NEW | 1.000 | 0.975 seeker_drive | **+0.025** [-0.010,+0.071] | 0.025 |
| eprand[5,25] | NEW | 0.808 | 0.933 seeker_drive | **-0.125** [-0.211,-0.040] | 0.067 |
| piecewise[5,25] | NEW | 0.842 | 0.908 seeker_drive | **-0.067** [-0.152,+0.018] | 0.092 |

## 3. G-A adjudication — pre-registered rule applied as written

- clean rule: family-2 clean VoI_matched = **+0.025 <= 0.05 -> PASS** (the
  clean half of the law replicates on family #2 on the hardened set).
- degraded rule: NEW family-2 cells >= 0.15: **2 of 5** (ar1 r0.9 +0.167,
  ar1 r0.95 +0.292; dropout +0.025, eprand -0.125, piecewise -0.067) — below
  the >= 3 bar -> **FAIL**.
- **G-A verdict: `law_not_replicated_family_specific_scope`.** Pre-registered
  routing applied: papers scope the degraded-revival claim family-specific
  (B2K2); WP1 still runs on family #1.

Structure behind the verdict (measured, reported not gated on): the degraded
revival on family #2 is MODE-dependent, not absent — both noise-like new
cells revive strongly (and the noise-0.05 anchor revives at +0.333, CI
excluding 0), while all delay-type cells (constant, episode-random,
piecewise) and dropout stay at zero or negative. Mechanism (inferred,
scoped): the family-2 drive-ramp seeker identifies mu while accelerating,
~1 s into a >= 3 s approach, so even 500 ms of delayed self-sensing leaves
slack before the speed commitment binds; noise-like degradation instead
blinds the shortfall detector outright (per-cell re-calibrated taus hit the
1.2 cap even at W=25 for AR(1) — time-averaging defeated as the plan
anticipated), collapsing the seeker to fixed-plan floors that the matched
oracle clears. On family #1 the same AR(1) cells also break the ORACLE's own
degraded speed tracking (0.308 vs clean 0.950), so the matched prize
vanishes there while the clean-anchor VoI stays large (~0.6) — the
anchor-distinction caveat from the plan, now measured.

## 4. Bridge validation — FALSIFIED (pre-registered criteria)

Latency inputs (measurement-A, median detection delay in steps; clean
median 8): delay5 dL=8, delay12 dL=11, delay25 dL=24, dropout dL=0,
eprand dL=12.5, piecewise dL=17; noise0.05 / ar1 r0.9 / ar1 r0.95 saturated
(miss rate 0.83-1.00 > 0.5 -> dL := 24, declared).

| family | new cell | dL (steps) | VoI predicted | VoI measured | classify agree |
|---|---|---|---|---|---|
| F1 | ar1 r0.9 | 24 (sat) | +0.183 | -0.017 | no |
| F1 | ar1 r0.95 | 24 (sat) | +0.183 | -0.050 | no |
| F1 | dropout0.2 | 0 | +0.067 | +0.083 | yes |
| F1 | eprand[5,25] | 12.5 | +0.427 | +0.017 | no |
| F1 | piecewise[5,25] | 17 | +0.331 | +0.100 | no |
| F2 | ar1 r0.9 | 24 (sat) | -0.075 | +0.167 | no |
| F2 | ar1 r0.95 | 24 (sat) | -0.075 | +0.292 | no |
| F2 | dropout0.2 | 0 | +0.025 | +0.025 | yes |
| F2 | eprand[5,25] | 12.5 | -0.009 | -0.125 | yes |
| F2 | piecewise[5,25] | 17 | -0.035 | -0.067 | yes |

Pooled (n=10): classification agreement **0.40 < 0.75**; Spearman
**-0.21 < 0.6** -> **bridge FAIL** in both pre-registered criteria. The
detection-latency increment does NOT predict where belief value re-emerges:
AR(1) breaks it in BOTH directions (saturated latency predicts delay-25-level
VoI, but measured VoI is ~0 on F1 because the oracle collapses too, and
positive on F2 because the floor collapses while the oracle survives), and
time-varying delay raises latency without VoI revival wherever the seeker
identifies before the commitment binds. Pre-registered route applied: the
bridge is demoted — degradation placements require direct per-cell
measurement; the falsification is itself the WP0.2 result.

## 5. Replication notes on the anchors (hardening deltas) — MEASURED

- Family-1 delay/noise anchors all revive at the matched anchor on 10
  validation seeds (delay5 +0.333, delay12 +0.458, delay25 +0.183, noise
  +0.150), confirming the two-regime law's degraded half on B2K2 with
  hardened statistics and Newcombe CIs excluding 0 in all four cells.
- The family-1 CLEAN cell tightens from VoI 0.000 (2 seeds) to +0.067
  (10 seeds, CI [-0.005,+0.141] including 0): the clean-regime null survives
  but is now bounded rather than exactly zero at this budget.
- 2-seed vs 10-seed matched estimates moved materially in several cells
  (e.g. F1 delay12 0.542->0.458 oracle; delay25 matched 0.333->0.183),
  vindicating the WP0.3 hardening requirement before WP1 freezes eligible
  cells.

## 6. Claim boundary

Allowed: pre-registered feasibility-audit VoI measurements on two scripted
task families under the extended degradation modes, the G-A adjudication and
the bridge falsification exactly as pre-registered. Rejected (explicit): any
driver-performance, current-sim verdict, high-fidelity, full-driver,
repair-success, robustness-result, feasibility-proof, validation/ranking/
promotion, paper-result, or self-ID claim; any reading of seeker/oracle
configurations as deployable drivers.

## 7. Routing

1. **WP1 proceeds on family #1 only** (G-A fallback as pre-registered);
   eligible-cell freezing for WP1 uses THIS milestone's hardened matched
   panel: eligible (matched >= 0.15) on F1 = {delay5, delay12, delay25,
   noise0.05}; the AR(1)/time-varying cells are NOT eligible at the matched
   anchor.
2. Papers scope the degraded-revival claim as family-conditional with the
   measured mode structure (noise-like vs delay-like x seeker-design) as a
   primary finding; the family-2 clean replication (+0.025) stands.
3. The bridge is demoted to direct measurement; its falsification is
   reported as the WP0.2 outcome (the prediction was designed to be
   breakable by AR(1) and it broke).

## 8. Artifacts

- `runs/feasibility_audit/wp0_degraded_sweep/summary.json` (pre-registration
  echo, per-cell tables, bridge, G-A verdicts; status completed)
- `runs/feasibility_audit/wp0_degraded_sweep/progress.jsonl` (per-unit
  resume log) and `rows/` (per-unit episode/latency CSVs)
- `experiments/feasibility_audit/wp0_degraded_sweep_prereg.json` (frozen
  criteria)
- `scripts/feasibility_audit/wp0_degraded_sweep.py` (criteria in docstring;
  `--quick` smoke + resume verified before registration)
- harness record: `runs/research/m3215-wp0-degraded-sweep-bridge-validation_20260611T121026Z/command.log`
- review: `docs/reviews/m3215-wp0-degraded-sweep-bridge-validation.md`
