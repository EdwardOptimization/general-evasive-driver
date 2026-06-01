# M2291 Paper-Route Current-Sim Scenario Task-Family Reset Filter-Edge Repair Result Audit

- status: completed
- decision: `current_sim_scenario_task_family_reset_validity_audit_route_to_measured_execution_design`
- manifest: `experiments/manifests/m2291-paper-route-current-sim-scenario-task-family-reset-filter-edge-repair-result-audit.json`
- parent result: `runs/m2290_paper_route_current_sim_scenario_task_family_filter_edge_repair/reset_validation/summary.json`
- reset rerun in M2291: `false`
- rollout/measured execution in M2291: `false`
- policy actions executed in M2291: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Audit Result

M2290 establishes reset-validity for the current-sim role-family scenario pack:

```text
materialization result_class: current_sim_scenario_task_family_config_materialization_pass
scenario_spec_count: 72
unsupported_execution_blocker_count: 0
friction_step_enabled_count: 0
actor_contract_violation_count: 0
guardrail_violation_count: 0

reset result_class: current_sim_scenario_task_family_reset_validation_pass
reset_success_count: 72 / 72
reset_failure_count: 0
label_not_allowed_count: 0
single_label_exact_mismatch_count: 0
lateral_offset_numeric_mismatch_count: 0
lateral_bucket_mismatch_count: 0
guardrail_violation_count: 0
```

Actual reset label distribution:

```text
aeb_feasible: 12
aes_feasible: 21
drift_required: 27
unavoidable: 12
```

This is the first reset-valid version of the explicit six-role current-sim
scenario task-family pack.

## Claim Boundary

Accepted:

```text
the v0 current-sim role-family scenario pack is materialized and reset-valid
under the P0 actor contract.
```

Not accepted:

```text
rollout success
measured execution success
training result
controller-family ranking
winner selection
finite-window vs GRU conclusion
paper-level evidence
level3 self-identification
```

The next step may design measured execution, but M2291 itself does not execute
policy actions and does not compare controller families.

## Route Decision

Route to measured execution design:

```text
m2292-paper-route-current-sim-scenario-task-family-measured-execution-design
```

M2292 should decide the execution panel before any policy action is run:

```text
scenario source:
  configs/paper_route_current_sim_scenario_task_family_v0.json

required coverage:
  six role families
  three timing buckets
  three signed lateral buckets
  hidden dynamics buckets
  label groups aeb/aes/drift_required/unavoidable

design outputs:
  controller/checkpoint source policy
  seed count and episode budget
  outcome metrics and slice tables
  no-ranking claim boundary
  result-audit route
```

The measured execution design should prefer reusing existing current-sim runner
patterns where possible, but it may design a focused scenario-family runner if
existing runners cannot consume the new `scenario_specs` config directly.

## Guardrails

Clean:

```text
actor_contract_violation_count: 0
labels_enter_actor_input_count: 0
ranking_admissible_count: 0
guardrail_violation_count: 0
```

No reset, rollout, policy action, measured execution, training, replay, PPO,
private holdout, controller-family ranking, paper-level claim, finite-window vs
GRU verdict, or level3 self-ID claim was made in this audit.

## Blocked Routes

Still blocked until M2292 design and a later implementation milestone:

```text
direct measured execution
controller-family ranking
winner selection
training or PPO
paper-level result
finite-window vs GRU verdict
level3 self-identification
```

## Next

Pre-register:

```text
m2292-paper-route-current-sim-scenario-task-family-measured-execution-design
```
