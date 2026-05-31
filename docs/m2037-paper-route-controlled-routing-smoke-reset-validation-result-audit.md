# M2037 Paper-Route Controlled Routing Smoke Reset Validation Result Audit

- status: completed
- decision: `controlled_routing_smoke_reset_validation_audit_admit_measured_execution_command_design`
- manifest: `experiments/manifests/m2037-paper-route-controlled-routing-smoke-reset-validation-result-audit.json`
- audited summary: `runs/m2036_paper_route_controlled_routing_smoke_reset_validation_preflight/summary.json`
- audited workload: `runs/m2033_paper_route_controlled_routing_smoke_materialization_preflight/planned_workload.csv`
- reset/rollout/measured execution in M2037: `false`
- policy actions executed: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Audit Summary

M2037 audits the M2036 focused reset-only validation result before allowing any
measured execution design.

M2036 passes all reset gates:

```text
result_class=controlled_routing_smoke_reset_validation_preflight_pass
input_executable_spec_count=36
target_executable_spec_count=36
reset_attempt_count=36
reset_success_count=36
reset_failure_count=0
observation_finite_count=36
observation_dimension_failure_count=0
obstacle_initialized_count=36
contract_violation_count=0
metadata_missing_count=0
forbidden_key_violation_count=0
family_quota_pass=true
source_kind_quota_pass=true
proxy_template_quota_pass=true
generated_proxy_quota_pass=true
guardrail_violation_count=0
environment_reset_started=true
environment_rollout_started=false
policy_action_executed=false
```

The reset-valid panel preserves the family coverage:

```text
T1_reactive_active_safety: 4
T2_same_current_different_older_history: 10
T3_active_diagnostic_warmup: 10
T4_variable_diagnostic_delay: 4
T5_source_rich_extreme_dynamics: 8
```

Generated proxy boundary is intact:

```text
generated=false|semantics=smoke_proxy|paper_claim=false: 24
generated=true|semantics=smoke_proxy|paper_claim=false: 12
```

The next measured-execution design target remains the M2033 planned workload:

```text
planned_workload_rows=432
workload_task_sources=36
workload_profiles=12
```

## Claim Boundary

M2037 accepts only this claim:

```text
the M2033 controlled routing-smoke 36-spec panel is reset-valid under the
current simulator and human-view observation contract.
```

Still blocked:

```text
measured controller performance;
controller-family ranking;
finite-window-vs-GRU conclusion;
paper-level benchmark evidence;
paper-valid generated T2/T3 task semantics;
level3 self-identification.
```

## Decision

M2037 admits measured execution command design over the existing `432` planned
workload rows. The next milestone must only design the execution route and
compatibility checks. It must not execute the workload or rank controller
families yet.

The measured-execution design must preserve:

```text
task_source_id
panel_source_id
panel_task_family
source_origin
source_kind
source_edge
window_tag
source_role_semantics
parent_feasibility_tier_id
normalized_surface_variant
sampled_obstacle_label
materialization_semantics
proxy_template_family
generated_source_row
paper_validity_claim
profile_name
profile_config_path
checkpoint_path
```

## Next

M2038 should design the exact measured execution command or focused runner
route for:

```text
runs/m2033_paper_route_controlled_routing_smoke_materialization_preflight/executable_task_specs.json
runs/m2033_paper_route_controlled_routing_smoke_materialization_preflight/planned_workload.csv
```

Measured execution, controller ranking, and paper claims remain blocked until
the command is designed, executed, and audited.
