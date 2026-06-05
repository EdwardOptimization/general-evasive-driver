# M2799 Engineering Controller Route A Source-Only Belief-Stress Clearance-Localized Corrective Training Preflight

- status: completed
- result_class: `engineering_controller_route_a_source_only_belief_stress_clearance_localized_corrective_training_preflight_pass`
- manifest: `experiments/manifests/m2799-engineering-controller-route-a-source-only-belief-stress-clearance-localized-corrective-training-preflight.json`
- summary: `runs/m2799_engineering_controller_route_a_source_only_belief_stress_clearance_localized_corrective_training_preflight/summary.json`
- source reference checkpoint: `runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt`
- base candidate checkpoint: `runs/m2782_engineering_controller_route_a_source_only_belief_stress_short_training_continuation_preflight/checkpoints/m2782_belief_stress_short_training_candidate.pt`
- start candidate checkpoint: `runs/m2791_engineering_controller_route_a_source_only_belief_stress_guardrailed_multi_objective_training_preflight/checkpoints/m2791_guardrailed_multi_objective_candidate.pt`
- candidate checkpoint: `runs/m2799_engineering_controller_route_a_source_only_belief_stress_clearance_localized_corrective_training_preflight/checkpoints/m2799_clearance_localized_corrective_candidate.pt`
- checkpoint manifest: `runs/m2799_engineering_controller_route_a_source_only_belief_stress_clearance_localized_corrective_training_preflight/checkpoint_manifest.json`
- training objective rows: `runs/m2799_engineering_controller_route_a_source_only_belief_stress_clearance_localized_corrective_training_preflight/training_objective_rows.csv`
- training run rows: `runs/m2799_engineering_controller_route_a_source_only_belief_stress_clearance_localized_corrective_training_preflight/training_run_rows.csv`
- proof probe rows: `runs/m2799_engineering_controller_route_a_source_only_belief_stress_clearance_localized_corrective_training_preflight/proof_probe_rows.csv`
- proof gates: `runs/m2799_engineering_controller_route_a_source_only_belief_stress_clearance_localized_corrective_training_preflight/proof_gate_rows.csv`
- generalization gates: `runs/m2799_engineering_controller_route_a_source_only_belief_stress_clearance_localized_corrective_training_preflight/generalization_gate_rows.csv`
- behavior-retention gates: `runs/m2799_engineering_controller_route_a_source_only_belief_stress_clearance_localized_corrective_training_preflight/behavior_retention_gate_rows.csv`
- promotion guards: `runs/m2799_engineering_controller_route_a_source_only_belief_stress_clearance_localized_corrective_training_preflight/promotion_guard_rows.csv`
- follow-up manifest: `experiments/manifests/m2800-engineering-controller-route-a-source-only-belief-stress-clearance-localized-corrective-training-result-audit.json`
- next: `m2800-engineering-controller-route-a-source-only-belief-stress-clearance-localized-corrective-training-result-audit`

## Result

M2799 ran one bounded source-only clearance-localized corrective
training/update preflight from the M2791 guardrailed candidate checkpoint,
with M2655 source and M2782 base retained as references. It wrote a
candidate checkpoint for audit, not promotion.

```text
training_objective_rows: 18
target_objective_rows: 12
retention_objective_rows: 6
training_run_rows: 48
proof_probe_rows: 48
stable_avoidable_retention_probe_rows: 24
proof_gate_rows: 14
generalization_gate_rows: 6
behavior_retention_gate_rows: 7
promotion_guard_rows: 4
candidate_checkpoint_written: True
checkpoint_behavior_changed: True
gate_matrix_pass: True
failed_gate_ids: none
```

## Clearance Target And Retention

```text
target_negative_clearance_count: 84
target_row_count: 96
target_negative_clearance_rate: 0.875
drift_required_recovery_negative_count: 48/48
stable_aes_negative_count: 36/48
stable_avoidable_negative_clearance_count: 1/48
obstacle_clearance_guard_hard_before_objectives: True
```

Obstacle clearance is the hard guard. Road-margin, yaw-rate, final-speed,
throttle/brake conflict, and action-delta metrics are diagnostics and cannot
hide clearance or stable_avoidable retention failures.

## Actor And Claim Boundary

Actor input stayed at P0 observation 72 and action 3. Atlas, role,
dynamics, stress, clearance, outcome, success, progress, route, and verdict
labels remained evaluator metadata and were not actor-visible. Mitigation
reference rows stayed outside ordinary denominators.

M2799 does not validate, rank, promote, compute a success-rate verdict,
claim repair success, driver performance, paper evidence, current-sim
verdict, high-fidelity validation, full ideal driver completion, or
level3 self-identification.
