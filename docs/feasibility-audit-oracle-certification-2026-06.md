# Feasibility Audit: Oracle Certification of the 7 Residual Hard-Safety Failure Rows (2026-06)

## Status

- protocol: `feasibility_audit_oracle_certification` (manual takeover route step 1,
  per `docs/feasibility-takeover-2026-06-route-decision.md`)
- scope: privileged oracle search over control sequences on the 7 residual
  hard-safety failure rows of the fixed M3084/M3105 64-seed panel. This converts
  the physical-audit avoidability bounds from computation to measurement.
- claim boundary: oracle results bound what any controller could achieve on these
  rows under the searched action-sequence family; no driver-performance,
  validation-result, repair-success, current-sim verdict, robustness-result, or
  self-ID claim is made for any deployable controller.
- artifacts:
  - script: `scripts/feasibility_audit/oracle_certification.py`
    (re-run: `PYTHONPATH=src python scripts/feasibility_audit/oracle_certification.py`)
  - per-row results: `experiments/feasibility_audit/oracle_certification_results.json`
  - best action sequences (per-step traces): `runs/feasibility_audit/oracle_certification_sequences.json`
  - run log: `runs/feasibility_audit/oracle_certification_run.log`

## Headline result

**Oracle verdict: 7/7 rows hard-fail under every searched control sequence, in
both tiers (43,372 privileged rollouts total).** No success sequence and no
no-hard-fail sequence (not even a safe stop ending in `speed_too_low`) was found
for any row. The Tier A (full-preview) best margins converge to a graze —
between -3.4e-6 and -1.4e-3 — i.e. the optimizer can drive the trajectory
arbitrarily close to the collision/boundary surface but never across it. The
fixed-panel ceiling of 57/64 = 0.890625 is therefore a **measured** ceiling,
not only a computed one, and the physical audit's predictions are confirmed on
all 7 rows including the two medium-confidence rows (0024, 0025).

## Method

- **Environment reconstruction** reuses the measurement-module code path
  exactly (no dynamics re-implemented): m3084 panel row -> m3012 executable
  workload (`config_path`, `profile_binding_name`) -> m3012 executable source
  spec -> `m3075.profile_config_for_runtime` ->
  `env_config_for_executable_profile` -> `wrap_env_with_profile_mask(AutoDriftEnv(...))`
  -> `reset(seed=eval_seed)` (deterministic; verified below).
- **Outcome semantics** reuse `autodrift.evaluate.outcome_bucket_from_info` — the
  same function used by `run_episode_with_policy` in every full-fresh measurement
  preflight. Buckets: `success_obstacle_pass` / `collision_failure` /
  `off_track_…` / `speed_too_low_…` / `max_steps_noncompletion`. "No hard fail" =
  {success, speed_too_low, max_steps}. Each tier's best candidate is additionally
  re-executed through `run_episode_with_policy` itself; outcome and step count
  matched the light rollout in **14/14** verification replays (7 rows x 2 tiers).
- **Incumbent reproduction gate**: the M3105 incumbent
  (`m3103_v4_v2_fallback_no_regression_hard_safety_direct_action_repair`, the
  deterministic obs72->action3 reflex family of
  `src/autodrift/active_safety_reflex_driver.py`) was re-run closed-loop on each
  row; outcome bucket, step count, and `min_clearance_margin` matched the
  recorded m3105 CSV rows on **7/7** (margin agreement < 1e-6).
- **Tier A (full-preview oracle)**: open-loop action sequence searched from step 0.
- **Tier B (reveal-constrained oracle)**: incumbent closed-loop actions forced for
  steps < `perception_reveal_step` (the first step at which the obstacle enters
  the actor-visible observation), search only afterwards — an upper bound for any
  causal controller restricted to actor-visible information.
- **Search** (per row x tier): 26 structured candidates (incumbent replay;
  full brake; full brake + constant steer ±0.2/0.5/0.8/1.0; coast + same steer
  grid; swerve-then-recenter at ±0.5/±1.0 for 8/16 steps), then CEM over a
  piecewise-constant parameterization (16 segments x 8 steps x 3 action dims,
  last segment held to episode end; population 64, elites 8, 48 iterations,
  initialized at the best structured candidate). Objective (lexicographic via
  scalar score): success > no-hard-fail > maximize worst margin
  (min of obstacle clearance margin and per-step boundary margin
  `track_width - |lateral_error|`), with later hard-failure time as secondary.
- **Determinism**: pure numpy on CPU; `numpy.random.default_rng(20260611 +
  100*row_index + tier_index)`; env reset(seed) re-verified bit-stable on reuse.
- **Budget**: 3,098 rollouts per row x tier; 43,372 total; wall time 225.8 s.

## Per-row certification table

Margins are the *combined margin* = min(obstacle clearance margin, boundary
margin); negative = hard failure. `inc` = incumbent (M3105) margin reproduced.

| row | eval_seed | spec | hidden label | incumbent outcome (step) | inc margin | Tier A best margin (outcome) | Tier B best margin (outcome) | success found A/B | no-hard-fail A/B |
|---|---|---|---|---|---|---|---|---|---|
| 0007 | 401530 | spec-0008 | unavoidable | collision (29) | -0.1119 | **-1.39e-3** (collision) | -0.1118 (collision) | no/no | no/no |
| 0010 | 401541 | spec-0010 | unavoidable | collision (38) | -0.2089 | **-8.4e-6** (collision) | -0.1694 (collision) | no/no | no/no |
| 0013 | 401560 | spec-0014 | drift_required | off_track (52) | -0.1405 | **-3.4e-6** (off_track) | -1.1e-5 (off_track) | no/no | no/no |
| 0024 | 401631 | spec-0008 | drift_required | off_track (50) | -0.0137 | **-8.5e-6** (off_track) | -5.9e-3 (off_track) | no/no | no/no |
| 0025 | 401640 | spec-0010 | drift_required | collision (36) | -0.1642 | **-1.1e-5** (collision) | -7.4e-7 (collision) | no/no | no/no |
| 0026 | 401641 | spec-0010 | unavoidable | collision (27) | -0.2054 | **-1.5e-5** (collision) | -0.2052 (collision) | no/no | no/no |
| 0029 | 401660 | spec-0014 | unavoidable | collision (23) | -0.2312 | **-1.3e-5** (collision) | -0.2285 (collision) | no/no | no/no |

(spec ids are `m3012-executable-source-spec-XXXX`; row ids are
`m3084-measurement-episode-XXXX`; "inc margin" for off_track rows is the
boundary-side combined margin, hence 0013 shows -0.1405 rather than its
clearance margin of +4.00.)

Additional measured facts:

- **No safe stop exists on any row**: every braking-led candidate (structured
  and CEM) ends in collision or off_track before speed can fall below the
  1.0 m/s `speed_too_low` threshold. Hidden physics make this concrete:
  initial speeds 14.8-19.3 m/s against obstacles 10.5-21.5 m ahead require
  5.9-17.7 m/s^2 of average deceleration, while the grip ceiling mu*g is only
  2.5-8.2 m/s^2 — on an r=18 m curve that simultaneously demands most of the
  friction circle laterally (all three specs are the
  `friction_limited_speed=false`, `speed_range=[14,20]` specs flagged in the
  route decision; five of the seven rows additionally take a mid-episode
  friction step down, e.g. 0025: mu 0.836 -> 0.324 at step 13).
- **Latest achievable hard-failure step** barely moves under full preview
  (e.g. 0029: step 23 incumbent -> 23 oracle; 0007: 29 -> 31): failure timing is
  geometrically pinned, not a controller artifact.

## Tier B: the incumbent is near the causal upper bound

Tier B margin minus incumbent margin (how much *any* causal controller could
still gain after obstacle reveal):

| row | incumbent margin | Tier B oracle margin | causal headroom |
|---|---|---|---|
| 0007 | -0.11192 | -0.11179 | +1.3e-4 |
| 0010 | -0.20891 | -0.16935 | +4.0e-2 |
| 0013 | -0.14051 | -0.00001 | +1.4e-1 |
| 0024 | -0.01366 | -0.00590 | +7.8e-3 |
| 0025 | -0.16420 | -0.00000 | +1.6e-1 |
| 0026 | -0.20540 | -0.20517 | +2.3e-4 |
| 0029 | -0.23123 | -0.22849 | +2.7e-3 |

On 0007/0026/0029 the incumbent is within 3e-4 of the reveal-constrained oracle
margin — it is already extracting essentially all causally available safety
margin. On 0013/0025 a causal controller could in principle graze
(margin ~ -1e-5) instead of failing by ~0.15 m, but still cannot avoid the hard
failure. **No causal controller of any kind can repair any of the 7 rows.**

## Comparison with the physical-audit predictions

| row | physical-audit prediction (confidence) | oracle measurement | agreement |
|---|---|---|---|
| 0007 | unavoidable (high) | hard fail under all sequences, both tiers | confirmed |
| 0010 | unavoidable (high) | hard fail under all sequences, both tiers | confirmed |
| 0013 | unavoidable (high) | hard fail under all sequences, both tiers | confirmed |
| 0024 | unavoidable (medium-high) | hard fail under all sequences, both tiers | confirmed (upgraded to measured) |
| 0025 | unavoidable (medium) | hard fail under all sequences, both tiers | confirmed (upgraded to measured; closest call — graze at -1e-5) |
| 0026 | unavoidable (high) | hard fail under all sequences, both tiers | confirmed |
| 0029 | unavoidable (high) | hard fail under all sequences, both tiers | confirmed |

Agreement: **7/7**. Note the generator's `drift_required` label on
0013/0024/0025 is optimistic relative to actual reachability: even privileged
full-preview drift-style sequences (the searched family includes hard swerve,
counter-steer, and throttle-through shapes) cannot pass these rows under this
env config; the label derives from generator-side heuristics
(`drift_lateral_mu_fraction=0.85`), not from a trajectory existence proof.

## Caveats

1. The oracle is an existence *search*, not an exhaustive proof: the action
   family is piecewise-constant (16 x 8 steps) open-loop plus 26 structured
   shapes, CEM 64x48 per tier. A pathological solution outside this family
   cannot be formally excluded. However, on 6/7 rows the optimizer converged to
   margins within 2e-5 of zero from independent seeds — the signature of an
   active geometric constraint surface rather than an under-searched landscape.
2. Tier B forces the M3105 incumbent prefix; a causal controller behaving
   differently *before* reveal (e.g. driving slower from step 0 without seeing
   the obstacle) is covered by Tier A, not Tier B. Since even Tier A finds no
   success, this distinction does not affect the verdict.
3. All results are current-sim (AutoDriftEnv) only; no high-fidelity claim.

## Route implication

The M3108-M3212 residual-repair branch (and planned M3213) targeted rows that
are now measured — not just computed — to be unrepairable by any controller,
causal or privileged. The block decision in
`docs/feasibility-takeover-2026-06-route-decision.md` stands on measurement;
the resume condition (pre-repair feasibility oracle gate) can use this script
directly as the gate primitive.

## Reproduction

```bash
PYTHONPATH=src python scripts/feasibility_audit/oracle_certification.py
# smoke (~7 s):
PYTHONPATH=src python scripts/feasibility_audit/oracle_certification.py --quick \
  --results-json runs/feasibility_audit/quick_results.json \
  --sequences-json runs/feasibility_audit/quick_sequences.json \
  --progress-json runs/feasibility_audit/quick_progress.json
```

Deterministic: identical results JSON (modulo `elapsed_s`) on re-run.
