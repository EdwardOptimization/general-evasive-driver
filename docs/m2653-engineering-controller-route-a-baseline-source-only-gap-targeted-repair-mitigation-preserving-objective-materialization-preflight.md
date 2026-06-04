# M2653 Engineering Controller Route A Mitigation-Preserving Objective Materialization Preflight

- status: completed
- result_class: `engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_objective_materialization_preflight_pass`
- manifest: `experiments/manifests/m2653-engineering-controller-route-a-baseline-source-only-gap-targeted-repair-mitigation-preserving-objective-materialization-preflight.json`
- summary: `runs/m2653_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_objective_materialization/summary.json`
- objective family rows: `runs/m2653_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_objective_materialization/objective_family_rows.csv`
- protected component gates: `runs/m2653_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_objective_materialization/protected_component_gate_rows.csv`
- target preservation gates: `runs/m2653_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_objective_materialization/target_preservation_gate_rows.csv`
- abort rules: `runs/m2653_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_objective_materialization/abort_rule_rows.csv`
- actor contract guards: `runs/m2653_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_objective_materialization/actor_contract_guard_rows.csv`
- claim boundary rows: `runs/m2653_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_objective_materialization/claim_boundary_rows.csv`
- gate matrix: `runs/m2653_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_objective_materialization/gate_matrix.csv`
- follow-up manifest: `experiments/manifests/m2654-engineering-controller-route-a-baseline-source-only-gap-targeted-repair-mitigation-preserving-objective-materialization-branch-synthesis.json`
- next: `m2654-engineering-controller-route-a-baseline-source-only-gap-targeted-repair-mitigation-preserving-objective-materialization-branch-synthesis`

## Result

M2653 materialized deterministic objective and gate rows from M2652.
It did not run repair, training, reset, rollout, replay, validation,
ranking, promotion, or success-rate computation.

```text
objective_family_row_count: 3
protected_component_gate_row_count: 4
target_preservation_gate_row_count: 2
abort_rule_row_count: 9
actor_contract_guard_row_count: 6
claim_boundary_row_count: 25
gate_matrix_pass: True
```

## Protected Components

```text
event_transition_guard
minimum_obstacle_clearance_preservation
obstacle_penetration_non_regression
severity_proxy_non_regression
```

## Decision

Route to M2654 branch synthesis before implementation repair or a second
repair execution preflight. M2654 must synthesize M2648-M2653 and
decide whether the materialized gate bundle is sufficient for
implementation repair, repair execution, artifact repair, evidence
expansion, pivot, or stop.

## Rejected Claims

M2653 does not claim driver performance, ranking, promotion, success
rate, validation, paper evidence, current-sim verdict, high-fidelity
validation, finite-window-vs-GRU evidence, or self-ID.
