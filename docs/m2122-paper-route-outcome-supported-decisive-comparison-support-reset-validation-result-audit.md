# M2122 Paper-Route Outcome-Supported Decisive Comparison-Support Reset Validation Result Audit

- status: completed
- decision: `comparison_support_reset_validation_audit_admit_measured_execution_command_design`
- audited summary: `runs/m2121_paper_route_outcome_supported_decisive_comparison_support_reset_validation_preflight/summary.json`
- reset/rollout/measured execution in M2122: `false`
- policy actions executed in M2122: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Audit Summary

M2121 is a clean reset-only validation artifact:

```text
result_class: comparison_support_reset_validation_preflight_pass
input_executable_spec_count: 240
target_executable_spec_count: 240
reset_attempt_count: 240
reset_success_count: 240
reset_failure_count: 0
observation_finite_count: 240
observation_dimension_failure_count: 0
obstacle_initialized_count: 240
contract_violation_count: 0
metadata_missing_count: 0
forbidden_key_violation_count: 0
intent_quota_pass: true
source_kind_quota_pass: true
proxy_template_quota_pass: true
generated_proxy_quota_pass: true
guardrail_violation_count: 0
```

Guardrails remain bounded to reset validation:

```text
environment_reset_started: true
environment_rollout_started: false
policy_action_executed: false
measured_rollout_started: false
training_started: false
replay_started: false
ppo_used: false
controller_family_ranking_claim_made: false
finite_window_vs_gru_conclusion_made: false
paper_level_claim_made: false
level3_self_id_claim_made: false
```

## Compatibility Note

The old controlled routing-smoke measured runner is close but not the exact
command to run directly. Its metadata schema includes old public-gate fields
such as `parent_feasibility_tier_id`, `normalized_surface_variant`, and
`sampled_obstacle_label`. The M2118 comparison-support panel instead carries:

```text
comparison_support_intent
target_support_tier
dynamics_band
obstacle_timing_band
road_width_band
initial_speed_band
materialization_semantics=comparison_support_smoke_proxy
```

M2123 should therefore freeze a dedicated or parameterized comparison-support
measured runner that preserves the new metadata and keeps all ranking and paper
claims blocked until measured execution and outcome localization are audited.

## Decision

M2122 admits measured-execution command design.

The next design should target:

```text
executable specs: runs/m2118_paper_route_outcome_supported_decisive_comparison_support_materialization_preflight/executable_task_specs.json
workload: runs/m2118_paper_route_outcome_supported_decisive_comparison_support_materialization_preflight/planned_workload.csv
output dir: runs/m2124_paper_route_outcome_supported_decisive_comparison_support_measured_execution
target episodes: 1200
target specs: 240
target profiles: 5
eval seed base: 212300
device: cpu
```

## Supported Claims

Supported:

```text
M2118 comparison-support executable specs are reset-valid and can proceed to
measured-execution command design.
```

Unsupported:

```text
rollout behavior;
measured execution;
policy performance;
comparison-ready support;
controller-family ranking;
paper-level benchmark evidence;
finite-window-vs-GRU conclusion;
level3 self-identification.
```

## Next

Next milestone:

```text
m2123-paper-route-outcome-supported-decisive-comparison-support-measured-execution-command-design
```
