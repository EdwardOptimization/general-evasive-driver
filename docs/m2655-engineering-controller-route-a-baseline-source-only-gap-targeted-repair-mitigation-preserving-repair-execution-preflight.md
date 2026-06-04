# M2655 Engineering Controller Route A Mitigation-Preserving Repair Execution Preflight

- status: completed
- result_class: `engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution_preflight_pass`
- manifest: `experiments/manifests/m2655-engineering-controller-route-a-baseline-source-only-gap-targeted-repair-mitigation-preserving-repair-execution-preflight.json`
- summary: `runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/summary.json`
- repair candidate sweep: `runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/repair_candidate_sweep.csv`
- selected repair trace: `runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/selected_repair_trace.csv`
- post-repair behavior rows: `runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/post_repair_behavior_rows.csv`
- mitigation-preserving gate evaluation: `runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/mitigation_preserving_gate_evaluation.csv`
- next: `m2656-engineering-controller-route-a-baseline-source-only-gap-targeted-repair-mitigation-preserving-repair-execution-branch-synthesis`

## Result

M2655 ran one bounded gate-aware mitigation-preserving source-only repair
execution preflight using the M2653 objective bundle. It wrote candidate
checkpoints, selected one diagnostic repair trace, measured post-repair
source-only behavior rows, and evaluated target preservation plus protected
mitigation component gates.

```text
repair_execution_started: True
repair_training_started: True
training_observation_count: 24
candidate_sweep_row_count: 3
selected_candidate_id: m2655_softened_gap_bias
candidate_constraint_status: protected_component_gate_failed
post_repair_behavior_row_count: 160
mitigation_preserving_gate_evaluation_row_count: 9
target_preservation_gates_all_passed: True
protected_component_gates_all_passed: False
target_and_protected_gates_all_passed: False
failed_gate_ids: severity_proxy_non_regression, obstacle_penetration_non_regression, minimum_obstacle_clearance_preservation
```

## Claim Boundary

M2655 is repair-execution preflight evidence for audit only. It does not
rank controllers, select a winner, promote a checkpoint, compute success
rates, validate, or claim driver performance, paper evidence,
finite-window-vs-GRU evidence, current-sim verdict, high-fidelity
validation, full ideal driver completion, or self-ID.
