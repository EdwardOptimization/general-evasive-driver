# M1828 Executable V2 Stable Source Repaired Targeted Reset Feasibility Preflight

- status: completed with fail result
- decision: `stable_source_repaired_targeted_reset_feasibility_fail_route_to_result_audit`
- source result: `runs/m1828_executable_v2_stable_source_repaired_targeted_reset_feasibility_preflight/summary.json`
- environment reset run: `true`
- rollout/training/replay/PPO: `false`

## Result Summary

M1828 ran the M1827 pre-registered reset-only command over the M1825 repaired
payload. The run is a clean negative result:

```text
result_class=executable_v2_reset_feasibility_preflight_fail
attempted_spec_count=36
reset_success_count=12
sampling_failure_count=24
profile_count=12
role_surface_count=1
reset_ready_spec_count=36
labels_enter_actor_input_count=0
ranking_admissible_by_default_count=0
metadata_join_incomplete_count=0
guardrail_violation_count=0
```

No rollout, policy action, measured execution, training, replay, PPO, ranking,
paper-level, or level3 self-ID claim was made.

## Failure Distribution

All successes came from the repaired `aeb_feasible` source. The two
`aes_feasible` sources still failed under reset:

```text
sampled_label_counts:
  aeb_feasible=12
  empty=24

hidden_bucket_counts:
  brake_variation=12
  friction_step=12
  nominal=12

hidden_bucket sampled-label distribution:
  brake_variation -> aeb_feasible=12
  friction_step -> empty=12
  nominal -> empty=12
```

By source:

| source | label | hidden bucket | repair candidate | reset result |
| --- | --- | --- | --- | --- |
| `m1771-bp1-00` | `aes_feasible` | `nominal` | `aes_medium_band` | 0/12 success |
| `m1771-bp1-02` | `aes_feasible` | `friction_step` | `original_attempts` | 0/12 success |
| `m1771-bp1-05` | `aeb_feasible` | `brake_variation` | `aeb_wide_search_band` | 12/12 success |

The error class for the 24 failures is:

```text
RuntimeError: failed to sample an obstacle scenario matching the configured filters
```

## Interpretation

The M1825 source-level repair was sufficient for the sparse `aeb_feasible`
source but not for the two systematic `aes_feasible` sources. This means the
offline density check used by the repair planner is not yet an adequate proxy
for the reset-time sampler constraints on the AES sources.

This is still an infrastructure failure, not a driver-performance result. The
correct next step is a result audit, not measured execution or profile-specific
tuning.

## Follow-Up

Route to:

```text
m1829-paper-route-executable-v2-targeted-reset-validation-branch-synthesis
```

The branch has reached the workflow synthesis cadence, so M1829 should
synthesize M1819-M1828 and audit whether the persistent AES failures are caused
by:

- sampler repair ranges still being incompatible with reset-time feasibility;
- offline density assumptions missing reset-time hidden dynamics or warmup
  constraints;
- a threshold or label classifier mismatch between the repair planner and the
  reset path.

M1829 must not run additional reset.

## Guardrails

- environment reset started: `true`
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

- repaired targeted reset-only preflight was executed;
- `aeb_feasible` repaired source passed reset for all 12 profiles;
- both `aes_feasible` repaired sources still fail reset for all 24 profiles;
- result audit is required.

Unsupported:

- repaired targeted reset feasibility;
- measured execution;
- controller-family ranking;
- private-holdout evidence;
- paper-level benchmark result;
- level3 self-identification.
