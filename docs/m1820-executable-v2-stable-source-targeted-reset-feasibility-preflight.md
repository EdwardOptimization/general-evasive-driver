# M1820 Executable V2 Stable Source Targeted Reset Feasibility Preflight

- status: completed
- decision: `stable_source_targeted_reset_feasibility_fail_route_to_result_audit`
- result class: `executable_v2_reset_feasibility_preflight_fail`
- output dir: `runs/m1820_executable_v2_stable_source_targeted_reset_feasibility_preflight`
- environment reset run: `true`
- rollout/training/replay/PPO: `false`

## Result

M1820 ran the targeted M1792 reset-only preflight over the M1816 converted
payload. The result is a clean negative result: reset was attempted, no guardrail
was violated, but the payload still has sampling failures.

```text
attempted_spec_count=36
reset_success_count=10
sampling_failure_count=26
guardrail_violation_count=0
```

## Count Checks

| field | observed | target |
| --- | ---: | ---: |
| `attempted_spec_count` | 36 | 36 |
| `reset_success_count` | 10 | 36 |
| `sampling_failure_count` | 26 | 0 |
| `profile_count` | 12 | 12 |
| `role_surface_count` | 1 | 1 |
| `reset_ready_spec_count` | 36 | 36 |
| `labels_enter_actor_input_count` | 0 | 0 |
| `ranking_admissible_by_default_count` | 0 | 0 |
| `metadata_join_incomplete_count` | 0 | 0 |
| `guardrail_violation_count` | 0 | 0 |

## Failure Distribution

By requested task label:

```text
aes_feasible: 24 failed / 24 attempted
aeb_feasible: 10 passed, 2 failed / 12 attempted
```

By hidden bucket:

```text
nominal: 12 failures
friction_step: 12 failures
brake_variation: 2 failures, 10 passes
```

Error class:

```text
RuntimeError: failed to sample an obstacle scenario matching the configured filters
```

The sampled labels in successful rows were:

```text
aeb_feasible: 10
```

No successful `aes_feasible` reset was observed.

## Artifacts

```text
runs/m1820_executable_v2_stable_source_targeted_reset_feasibility_preflight/summary.json
runs/m1820_executable_v2_stable_source_targeted_reset_feasibility_preflight/reset_stress_rows.csv
runs/m1820_executable_v2_stable_source_targeted_reset_feasibility_preflight/sampling_failure_rows.csv
runs/m1820_executable_v2_stable_source_targeted_reset_feasibility_preflight/label_distribution_by_surface.csv
runs/m1820_executable_v2_stable_source_targeted_reset_feasibility_preflight/label_distribution_by_profile.csv
runs/m1820_executable_v2_stable_source_targeted_reset_feasibility_preflight/label_distribution_by_hidden_bucket.csv
```

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
- profile-specific tuning: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`
- guardrail violation count: `0`

## Claim Boundary

Supported:

- targeted reset-only preflight was executed;
- the current converted payload still fails reset feasibility;
- failures are concentrated in all `aes_feasible` rows and two `aeb_feasible`
  rows.

Unsupported:

- repaired reset feasibility;
- measured execution;
- controller-family ranking;
- private-holdout evidence;
- paper-level benchmark result;
- level3 self-identification.

## Decision

Route to:

```text
m1821-executable-v2-stable-source-targeted-reset-feasibility-result-audit
```

M1821 should audit the failure pattern before any repair. The likely repair
question is whether the M1811 label-specific sampler patch is insufficient for
`aes_feasible` stable sources or whether the reset adapter/profile merge is
overriding the materialized `env_config`.
