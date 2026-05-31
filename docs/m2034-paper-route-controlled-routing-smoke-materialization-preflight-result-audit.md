# M2034 Paper-Route Controlled Routing Smoke Materialization Preflight Result Audit

- status: completed
- decision: `controlled_routing_smoke_materialization_result_audit_admit_reset_validation_command_design`
- manifest: `experiments/manifests/m2034-paper-route-controlled-routing-smoke-materialization-preflight-result-audit.json`
- audited summary: `runs/m2033_paper_route_controlled_routing_smoke_materialization_preflight/summary.json`
- audited workload: `runs/m2033_paper_route_controlled_routing_smoke_materialization_preflight/planned_workload.csv`
- focused tests: `not_applicable_result_audit_only`
- reset/rollout/measured execution in M2034: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Audit Summary

M2034 audits the M2033 no-reset materialization artifacts before allowing any
reset-only validation command design.

M2033 passes the materialization checks:

```text
result_class=controlled_routing_smoke_materialization_preflight_pass
selected_source_count=36
executable_task_spec_count=36
planned_workload_count=432
profile_count=12
profile_missing_count=0
materialization_failure_count=0
duplicate_task_source_id_count=0
duplicate_workload_id_count=0
contract_violation_count=0
forbidden_key_violation_count=0
generated_non_proxy_count=0
smoke_proxy_paper_claim_count=0
guardrail_violation_count=0
```

The executable specs cover all expected smoke families:

```text
T1_reactive_active_safety: 4
T2_same_current_different_older_history: 10
T3_active_diagnostic_warmup: 10
T4_variable_diagnostic_delay: 4
T5_source_rich_extreme_dynamics: 8
```

The planned workload has `432` rows: `36` executable specs crossed with `12`
controller profiles.

## Proxy and Claim Boundary

Generated T2/T3 rows remain bounded smoke proxies:

```text
generated_count=12
generated_semantics=['smoke_proxy']
generated_paper_claims=['false']
```

The M2033 claim boundary admits only materialization and routing-smoke execution
readiness. It keeps these claims blocked:

```text
controller_family_ranking=false
paper_valid_generated_task_semantics=false
finite_window_vs_gru_conclusion=false
level3_self_identification=false
```

This is important because the generated T2/T3 rows were created to exercise
source coverage and routing plumbing. They are not yet validated as paper-level
task semantics.

## Decision

M2034 accepts M2033 as a clean materialization pass and admits a reset-only
validation command design.

The next step must not jump directly to rollout or ranking. It should first
freeze a reset-only validation route over:

```text
runs/m2033_paper_route_controlled_routing_smoke_materialization_preflight/executable_task_specs.json
```

Target reset scope:

```text
target executable specs: 36
expected observation dimension: 72
rollout steps: 0
policy actions: 0
```

Because the M2033 executable specs carry the controlled-routing-smoke metadata
schema rather than the older task-quality repair schema, M2035 should audit
whether an existing reset validator can preserve:

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
```

If not, M2035 should design a focused controlled-routing-smoke reset validator
instead of forcing the older validator schema.

## Rejected Routes

Rejected now:

```text
direct rollout execution;
controller-family ranking;
paper benchmark execution;
finite-window-vs-GRU comparison;
level3 self-identification claims;
claiming generated T2/T3 task semantics are paper-valid.
```

## Next

M2035 should design the exact reset-only validation command or focused validator
route for the M2033 36-spec executable panel. Interpretation of any reset result
must be deferred to a later result audit.
