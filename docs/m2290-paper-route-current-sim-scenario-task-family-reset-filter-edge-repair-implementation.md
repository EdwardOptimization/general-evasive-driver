# M2290 Paper-Route Current-Sim Scenario Task-Family Reset Filter-Edge Repair Implementation

- status: completed
- result class: `current_sim_scenario_task_family_reset_validation_pass`
- decision: `current_sim_scenario_task_family_filter_edge_repair_pass_route_to_result_audit`
- manifest: `experiments/manifests/m2290-paper-route-current-sim-scenario-task-family-reset-filter-edge-repair-implementation.json`
- implementation:
  - `src/autodrift/paper_route_current_sim_scenario_task_family_config_materialization.py`
- tests:
  - `tests/test_paper_route_current_sim_scenario_task_family_config_materialization.py`
- materialization artifact: `runs/m2290_paper_route_current_sim_scenario_task_family_filter_edge_repair/materialization/summary.json`
- reset-validation artifact: `runs/m2290_paper_route_current_sim_scenario_task_family_filter_edge_repair/reset_validation/summary.json`
- policy actions executed: `false`
- rollout/measured execution/training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Implementation

M2290 implemented the M2289 focused repair:

```text
1. removed the implicit low_mu -> friction_step.enabled rule from the v0
   reset-valid scenario pack;
2. added a materializer-side reset-filter compatibility helper that checks
   label filters, AEB-infeasible filters, friction-limited speed compatibility,
   and friction-step timing compatibility;
3. refreshed configs/paper_route_current_sim_scenario_task_family_v0.json.
```

The repaired pack now has:

```text
scenario_spec_count: 72
friction_step_enabled_count: 0
left_offset sign: +1.2
right_offset sign: -1.2
```

Sudden friction-change scenarios remain a future explicit scenario family, not
an implicit side effect of the `low_mu` hidden bucket in this v0 reset-valid
pack.

## Verification

Focused tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_paper_route_current_sim_scenario_task_family_config_materialization.py \
  tests/test_paper_route_current_sim_scenario_task_family_reset_validation.py \
  tests/test_obstacle_lateral_offset_instrumentation.py
```

Result:

```text
11 passed
```

## Materialization Result

Command:

```bash
PYTHONPATH=src python -m autodrift.paper_route_current_sim_scenario_task_family_config_materialization \
  --config-output configs/paper_route_current_sim_scenario_task_family_v0.json \
  --output-dir runs/m2290_paper_route_current_sim_scenario_task_family_filter_edge_repair/materialization \
  --next-blocker m2290-paper-route-current-sim-scenario-task-family-reset-filter-edge-repair-implementation
```

Result:

```text
result_class: current_sim_scenario_task_family_config_materialization_pass
scenario_family_count: 6
scenario_spec_count: 72
unsupported_execution_blocker_count: 0
actor_contract_violation_count: 0
labels_enter_actor_input_count: 0
ranking_admissible_count: 0
guardrail_violation_count: 0
passes_public_materialization_gates: true
```

## Reset-Validation Result

Command:

```bash
PYTHONPATH=src python -m autodrift.paper_route_current_sim_scenario_task_family_reset_validation \
  --config configs/paper_route_current_sim_scenario_task_family_v0.json \
  --output-dir runs/m2290_paper_route_current_sim_scenario_task_family_filter_edge_repair/reset_validation \
  --eval-seed-base 229000 \
  --target-spec-count 72 \
  --expected-observation-dim 72 \
  --next-blocker m2291-paper-route-current-sim-scenario-task-family-reset-filter-edge-repair-result-audit
```

Result:

```text
result_class: current_sim_scenario_task_family_reset_validation_pass
reset_attempt_count: 72
reset_success_count: 72
reset_failure_count: 0
observation_dimension_failure_count: 0
observation_finite_count: 72
obstacle_initialized_count: 72
actor_contract_violation_count: 0
label_not_allowed_count: 0
single_label_exact_mismatch_count: 0
lateral_offset_numeric_mismatch_count: 0
lateral_bucket_mismatch_count: 0
guardrail_violation_count: 0
passes_public_reset_validation_gates: true
```

Actual reset labels:

```text
aeb_feasible: 12
aes_feasible: 21
drift_required: 27
unavoidable: 12
```

## Interpretation

M2290 establishes reset-validity for the current-sim role-family scenario pack:

```text
M2284 reset successes: 12 / 72
M2287 reset successes: 71 / 72
M2290 reset successes: 72 / 72
```

This is a scenario-quality infrastructure result. It does not prove rollout
performance, controller ranking, paper-level evidence, finite-window vs GRU
behavior, or level3 self-identification.

## Contract And Guardrails

Clean:

```text
actor_contract_violation_count: 0
labels_enter_actor_input_count: 0
ranking_admissible_count: 0
guardrail_violation_count: 0
```

No rollout, policy action, measured execution, training, replay, PPO, private
holdout, controller-family ranking, paper-level claim, finite-window-vs-GRU
conclusion, or level3 self-ID claim was made.

## Decision

Route to M2291 result audit:

```text
m2291-paper-route-current-sim-scenario-task-family-reset-filter-edge-repair-result-audit
```

M2291 should audit the reset-valid pack and decide whether to route to measured
execution design, branch synthesis, or another non-ranking diagnostic.

## Blocked Claims

Still blocked:

```text
rollout success
measured execution success
training result
controller-family ranking
winner selection
finite-window vs GRU verdict
paper-level result
level3 self-identification
```
