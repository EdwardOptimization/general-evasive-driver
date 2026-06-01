# M2101 Paper-Route Outcome-Supported Decisive Public-Gate Core Measured Execution Implementation And Run

- status: completed
- decision: `public_gate_core_measured_execution_incomplete_route_to_result_audit`
- run artifact: `runs/m2101_paper_route_outcome_supported_decisive_public_gate_core_measured_execution/summary.json`
- focused tests: `3 passed`
- measured execution in M2101: `true`
- rollout/policy actions in M2101: `true`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Run Result

M2101 ran the frozen M2100 measured-execution command over the M2098
metadata-compatible public-gate core artifacts.

Result:

```text
result_class: controlled_routing_smoke_measured_execution_incomplete_or_fail
episode_count: 478
target_episode_count: 480
failure_count: 2
spec_count: 96
target_spec_count: 96
profile_count: 5
target_profile_count: 5
metadata_missing_count: 480
metric_completeness_failure_count: 0
guardrail_violation_count: 0
environment_rollout_started: true
policy_action_executed: true
measured_rollout_started: true
training_started: false
replay_started: false
ppo_used: false
paper_level_claim_made: false
level3_self_id_claim_made: false
```

The run is incomplete and must not be interpreted as a controller ranking or
paper-level result.

## Failure Rows

Two workload cells failed during obstacle sampling:

```text
m2063-osd-osd_v0_0162_t3::L2_window_50
  profile: L2_window_50
  family: T3_active_diagnostic_warmup
  source_kind: warmup_brake_authority_probe
  error: failed to sample an obstacle scenario matching the configured filters

m2063-osd-osd_v0_0235_t5::L3_online_gru
  profile: L3_online_gru
  family: T5_terminal_boundary_near_constraint
  source_kind: late_terminal_boundary_margin
  error: failed to sample an obstacle scenario matching the configured filters
```

Validation did not fail before rollout:

```text
validation_failure_rows.csv: header only
metric_completeness_failure_count: 0
```

## Metadata Gap

The run also reports metadata_missing_count `480`. The missing fields are:

```text
source_role_semantics
parent_feasibility_tier_id
normalized_surface_variant
sampled_obstacle_label
```

These fields are part of the existing controlled-routing-smoke measured runner's
full metadata completeness audit. M2098 repaired the fields required for
pre-rollout validation, but not these full metadata completeness fields.

## Interpretation Boundary

Supported:

```text
The frozen M2100 command executed rollout/policy actions and wrote measured
execution artifacts for 478/480 workload cells.
The run has no metric completeness failures and no guardrail violations.
```

Unsupported:

```text
complete measured execution;
controller-family ranking;
paper-level benchmark evidence;
finite-window-vs-GRU conclusion;
level3 self-identification.
```

## Next

Next milestone:

```text
m2102-paper-route-outcome-supported-decisive-public-gate-core-measured-execution-result-audit
```
