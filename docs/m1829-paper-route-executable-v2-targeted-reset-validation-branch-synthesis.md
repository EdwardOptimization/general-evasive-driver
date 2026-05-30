# M1829 Paper Route Executable V2 Targeted Reset Validation Branch Synthesis

- status: completed
- synthesis decision: `pivot`
- completed branch: `paper_route_executable_v2_targeted_reset_validation`
- next branch: `paper_route_executable_v2_reset_time_aes_sampler_diagnostic`
- additional reset run: `false`
- rollout/training/replay/PPO: `false`

## Evidence Summary

M1819-M1828 tested whether the three stable source-label gaps materialized in
M1811 and converted in M1816 could become reset-ready targeted executable-v2
rows.

Branch evidence:

- M1819 pre-registered the exact M1792 reset-only command over the clean M1816
  targeted reset payload.
- M1820 ran that reset-only preflight and failed cleanly: `36` attempted,
  `10` reset successes, `26` sampling failures, zero guardrail violations.
- M1821 localized the failures as systematic `aes_feasible` sampler
  infeasibility for two sources plus sparse `aeb_feasible` seed failure for one
  source.
- M1822 designed source-level sampler repair, explicitly preserving all 12
  profile controls and keeping labels metadata-only.
- M1823 implemented a no-reset sampler repair planner based on source-level
  failure classes and offline label-density checks.
- M1825 executed that planner and produced a repaired 36-row targeted reset
  payload with three repaired source targets and clean guardrails.
- M1826 audited the repaired payload as complete: `36` unique rows, `12`
  profiles, `3` sources, no label leakage, no ranking admission, and no
  profile-specific tuning.
- M1827 pre-registered the exact reset-only preflight over the repaired payload.
- M1828 ran the repaired reset-only preflight and failed cleanly:
  `36` attempted, `12` reset successes, `24` sampling failures, zero guardrail
  violations.

The M1828 failure distribution is decisive:

```text
aeb_feasible / brake_variation / wide_offset: 12/12 reset successes
aes_feasible / nominal / medium center:       0/12 reset successes
aes_feasible / friction_step / late center:   0/12 reset successes
```

All M1828 failures are:

```text
RuntimeError: failed to sample an obstacle scenario matching the configured filters
```

## Supported Claims

Supported:

- the executable-v2 targeted reset adapter and metadata contract remain clean;
- profile controls are preserved across materialization, repair, and reset
  preflight;
- labels remain metadata-only and do not enter actor input;
- controller-family ranking remains blocked by default;
- the sparse `aeb_feasible` source was repaired enough to reset successfully for
  all 12 profiles;
- the two `aes_feasible` sources still have systematic reset-time sampler
  infeasibility after M1825 repair.

Unsupported:

- repaired targeted reset feasibility for the full 36-row payload;
- measured execution readiness;
- controller-family ranking;
- private-holdout evidence;
- paper-level benchmark evidence;
- level3 self-identification.

## Falsified Claims

Falsified or rejected during this branch:

- The original M1816 targeted payload was reset-ready for all 36 rows.
- A source-level label patch plus increased attempts was enough for the two
  `aes_feasible` stable sources.
- The M1823/M1825 offline density proxy was sufficient to predict reset-time
  `aes_feasible` sampler support.
- Another broad repaired reset rerun is justified before diagnosing the
  reset-time AES sampler path.

Not falsified:

- The `aeb_feasible` source can be repaired with a broader search band.
- The executable-v2 metadata, profile, and ranking guardrails are intact.

## Failure Taxonomy Summary

Observed failure types:

- `scenario_sampling_failure`: dominant and persistent for `aes_feasible`
  source reset.
- `metric_artifact`: avoided for metadata/ranking/label leakage; no current
  evidence that counts or joins are corrupted.

Subclasses:

```text
systematic_aes_reset_time_sampler_incompatibility: 24 rows
aeb_sparse_seed_failure_repaired: 12 rows now pass
offline_density_proxy_mismatch: M1825 accepted AES candidates but M1828 reset still failed
```

No actor-input contract violation occurred. No profile-specific tuning was
introduced. No rollout, policy action, measured execution, training, replay,
PPO, promotion, private holdout, ranking, paper-level claim, or level3 self-ID
claim was made.

## Public Gate Overfit Risk

The main overfit risk in this branch is infrastructure overfitting, not policy
overfitting. The branch repeatedly tried to satisfy a fixed 36-row targeted
reset payload. M1828 shows that passing a no-reset repair planner is not enough:
the repair objective can overfit the offline density proxy while still failing
the reset-time sampler.

The next branch should not keep widening ranges blindly. It should instrument
the reset-time AES sampler path and compare it against the offline density
assumptions before another repair attempt.

## Next Branch Decision

Decision:

```text
pivot
```

Next branch:

```text
paper_route_executable_v2_reset_time_aes_sampler_diagnostic
```

Next milestone:

```text
m1830-executable-v2-reset-time-aes-sampler-diagnostic-design
```

M1830 should design a diagnostic that can explain why the two repaired AES
sources still fail under reset. The diagnostic should target:

```text
m1811-stable-bp-000 / m1771-bp1-00 / aes_feasible / nominal
m1811-stable-bp-001 / m1771-bp1-02 / aes_feasible / friction_step
```

It should compare:

- reset-time sampled candidate distributions;
- label classifier outcomes;
- threshold scores;
- hidden dynamics and friction-step timing constraints;
- warmup/reveal constraints;
- obstacle distance and half-width ranges;
- attempt-budget effects.

M1830 should not run reset; it should specify the diagnostic contract and route
to implementation or execution design.

## Guardrails

- additional environment reset started: `false`
- environment rollout started: `false`
- policy action executed: `false`
- measured rollout started: `false`
- training started: `false`
- replay started: `false`
- PPO used: `false`
- promoted: `false`
- private holdout used: `false`
- actor input contract changed: `false`
- reward changed: `false`
- dynamics changed: `false`
- termination behavior changed: `false`
- profile-specific tuning: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`
- guardrail violation count: `0`

## Claim Boundary

Supported:

- targeted reset validation branch synthesis;
- persistent AES reset-time sampler incompatibility diagnosis target;
- pivot to reset-time AES sampler diagnostic branch.

Unsupported:

- repaired targeted reset feasibility;
- measured execution;
- controller-family ranking;
- private-holdout evidence;
- paper-level benchmark result;
- level3 self-identification.
