# M2049 Paper-Route Controlled Routing Smoke Task-Quality Repair Materialization Preflight Result Audit

- status: completed
- decision: `controlled_routing_smoke_task_quality_repair_materialization_audit_admit_reset_command_design`
- audited summary: `runs/m2048_paper_route_controlled_routing_smoke_task_quality_repair_materialization_preflight/summary.json`
- audited specs: `runs/m2048_paper_route_controlled_routing_smoke_task_quality_repair_materialization_preflight/executable_task_specs.json`
- audited workload: `runs/m2048_paper_route_controlled_routing_smoke_task_quality_repair_materialization_preflight/planned_workload.csv`
- reset/rollout/measured execution in M2049: `false`
- policy actions executed in M2049: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Result Audit

M2048 is a clean no-reset materialization preflight pass:

```text
result_class: controlled_routing_smoke_task_quality_repair_materialization_preflight_pass
input_candidate_count: 192 / 192
repaired_spec_count: 192
planned_workload_count: 2304 / 2304
profile_count: 12 / 12
unresolved_parent_count: 0
materialization_failure_count: 0
duplicate_task_source_id_count: 0
duplicate_workload_id_count: 0
guardrail_violation_count: 0
```

Repair-axis quotas are preserved:

```text
l2_offtrack_relief: 64
family_offtrack_relief: 48
zero_success_source_kind_relief: 40
success_neighborhood_expansion: 24
generated_proxy_support_check: 16
```

Split quotas are preserved:

```text
public_debug: 112
public_gate: 80
```

## Contract And Claim Audit

The materialization remains within the paper-route claim boundary:

```text
contract_violation_count: 0
forbidden_key_violation_count: 0
generated_proxy_paper_claim_count: 0
profile_specific_tuning_count: 0
forbidden_claim_count: 0
actor_input_contract_changed: false
generated_proxy_paper_validity_claim_made: false
controller_family_ranking_claim_made: false
finite_window_vs_gru_conclusion_made: false
paper_level_claim_made: false
level3_self_id_claim_made: false
environment_reset_started: false
environment_rollout_started: false
policy_action_executed: false
```

The repaired specs are executable-task specs, but this audit does not establish
reset validity, rollout validity, controller-family ranking, finite-window vs
GRU evidence, or self-identification evidence.

## Route Decision

Selected:

```text
route_to_controlled_routing_smoke_task_quality_repair_reset_validation_command_design
```

M2050 should freeze the exact reset-only validation route for the M2048 repaired
panel:

```text
input executable task specs: 192
reset attempts: 192
expected observation dimension: 72
output: runs/m2051_paper_route_controlled_routing_smoke_task_quality_repair_reset_validation_preflight
next blocker: m2052-paper-route-controlled-routing-smoke-task-quality-repair-reset-validation-result-audit
```

The existing focused validator
`autodrift.paper_route_controlled_routing_smoke_reset_validation_preflight` is
schema-compatible with the M2048 specs because the M2048 rows preserve the
controlled-routing-smoke metadata required by the validator. M2050 should still
freeze the command explicitly because the target count, output directory,
eval-seed base, and next blocker differ from the original M2036 run.

Rejected:

```text
direct reset execution:
  rejected because M2049 is an audit and the reset command must be frozen first.

direct measured execution:
  rejected because reset validity has not been proven for the repaired panel.

controller-family ranking:
  rejected because there is no repaired-panel reset or rollout evidence.

another materialization repair:
  rejected because M2048 passed registered materialization and claim guards.
```

Controller ranking, finite-window-vs-GRU, paper-level comparison, and level3
self-ID claims remain blocked.

## Next

Next milestone:

```text
m2050-paper-route-controlled-routing-smoke-task-quality-repair-reset-validation-command-design
```
