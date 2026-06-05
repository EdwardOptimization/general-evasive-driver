# M2791 Engineering Controller Route A Source-Only Belief-Stress Guardrailed Multi-Objective Training Preflight

- status: completed
- result_class: `engineering_controller_route_a_source_only_belief_stress_guardrailed_multi_objective_training_preflight_pass`
- manifest: `experiments/manifests/m2791-engineering-controller-route-a-source-only-belief-stress-guardrailed-multi-objective-training-preflight.json`
- summary: `runs/m2791_engineering_controller_route_a_source_only_belief_stress_guardrailed_multi_objective_training_preflight/summary.json`
- source reference checkpoint: `runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt`
- base candidate checkpoint: `runs/m2782_engineering_controller_route_a_source_only_belief_stress_short_training_continuation_preflight/checkpoints/m2782_belief_stress_short_training_candidate.pt`
- candidate checkpoint: `runs/m2791_engineering_controller_route_a_source_only_belief_stress_guardrailed_multi_objective_training_preflight/checkpoints/m2791_guardrailed_multi_objective_candidate.pt`
- checkpoint manifest: `runs/m2791_engineering_controller_route_a_source_only_belief_stress_guardrailed_multi_objective_training_preflight/checkpoint_manifest.json`
- training objective rows: `runs/m2791_engineering_controller_route_a_source_only_belief_stress_guardrailed_multi_objective_training_preflight/training_objective_rows.csv`
- training run rows: `runs/m2791_engineering_controller_route_a_source_only_belief_stress_guardrailed_multi_objective_training_preflight/training_run_rows.csv`
- proof gates: `runs/m2791_engineering_controller_route_a_source_only_belief_stress_guardrailed_multi_objective_training_preflight/proof_gate_rows.csv`
- generalization gates: `runs/m2791_engineering_controller_route_a_source_only_belief_stress_guardrailed_multi_objective_training_preflight/generalization_gate_rows.csv`
- behavior-retention gates: `runs/m2791_engineering_controller_route_a_source_only_belief_stress_guardrailed_multi_objective_training_preflight/behavior_retention_gate_rows.csv`
- promotion guards: `runs/m2791_engineering_controller_route_a_source_only_belief_stress_guardrailed_multi_objective_training_preflight/promotion_guard_rows.csv`
- follow-up manifest: `experiments/manifests/m2792-engineering-controller-route-a-source-only-belief-stress-guardrailed-multi-objective-training-result-audit.json`
- next: `m2792-engineering-controller-route-a-source-only-belief-stress-guardrailed-multi-objective-training-result-audit`

## Result

M2791 ran one bounded source-only guardrailed multi-objective training/update
preflight from the M2782 candidate checkpoint, with M2655 retained as source
reference. It wrote a candidate checkpoint for audit, not promotion.

```text
training_objective_rows: 18
training_run_rows: 54
proof_holdout_probe_rows: 36
proof_gate_rows: 13
generalization_gate_rows: 6
behavior_retention_gate_rows: 7
promotion_guard_rows: 4
candidate_checkpoint_written: True
checkpoint_behavior_changed: True
gate_matrix_pass: True
failed_gate_ids: none
```

## Behavior-Retention Guard

```text
m2787_paired_delta_rows: 72
m2787_obstacle_clearance_negative_count: 29
m2787_obstacle_clearance_positive_count: 43
m2787_road_margin_positive_count: 72
m2787_yaw_rate_lower_count: 60
m2787_throttle_brake_conflict_zero_count: 72
obstacle_clearance_regression_guard_required: True
obstacle_clearance_guard_hard_before_objectives: True
```

Obstacle clearance is the hard guard. Road-margin, yaw-rate, final-speed,
throttle/brake conflict, and action-delta metrics are separated and cannot
hide obstacle-clearance regression. This is still a preflight artifact pack,
not validation or promotion evidence.

## Actor And Claim Boundary

Actor input stayed at P0 observation 72 and action 3. Stress, admission,
curriculum, role, dynamics, outcome, success, progress, route, and verdict
labels remained evaluator metadata and were not actor-visible. Mitigation
reference rows stayed outside ordinary denominators.

M2791 does not validate, rank, promote, compute a success-rate verdict,
claim repair success, driver performance, paper evidence, current-sim
verdict, high-fidelity validation, full ideal driver completion, or
level3 self-identification.
