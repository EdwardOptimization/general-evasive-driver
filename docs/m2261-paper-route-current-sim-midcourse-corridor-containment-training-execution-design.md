# M2261 Paper-Route Current-Sim Midcourse Corridor-Containment Training Execution Design

- status: completed
- decision: `current_sim_midcourse_corridor_containment_training_execution_design_admit_execution`
- manifest: `experiments/manifests/m2261-paper-route-current-sim-midcourse-corridor-containment-training-execution-design.json`
- parent audit: `docs/m2260-paper-route-current-sim-midcourse-corridor-containment-config-materialization-result-audit.md`

## Admission Evidence

M2259/M2260 provide a clean targeted containment materialization:

```text
result_class: current_sim_midcourse_corridor_containment_config_materialization_pass
materialized_config_count: 15
training_matrix_row_count: 15
profile_set_matched: true
seed_set_matched: true
budget_signature_count: 1
target_value_mismatch_count: 0
contract_violation_count: 0
track_width_widened_count: 0
guardrail_violation_count: 0
```

The execution must use exactly:

```text
runs/m2259_paper_route_current_sim_midcourse_corridor_containment_configs/training_matrix.csv
```

## Execution Design

Use the existing candidate-checkpoint runner:

```bash
PYTHONPATH=src python -m autodrift.paper_route_current_sim_training_stability_repair_execution \
  --training-matrix runs/m2259_paper_route_current_sim_midcourse_corridor_containment_configs/training_matrix.csv \
  --output-dir runs/m2262_paper_route_current_sim_midcourse_corridor_containment_training_execution \
  --execution-root runs/m2262_paper_route_current_sim_midcourse_corridor_containment_training_execution \
  --task-id m2262-paper-route-current-sim-midcourse-corridor-containment-training-execution \
  --next-blocker m2263-paper-route-current-sim-midcourse-corridor-containment-training-execution-result-audit \
  --device cpu
```

This runner should:

```text
copy M2259 configs into the execution output directory
run exactly 15 train_ppo jobs
keep total_steps = 32768
keep checkpoint_interval_steps = 4096
evaluate 8 candidate checkpoints per run
write 120 candidate eval rows
write 15 selected checkpoint rows
write profile aggregates
```

## Guardrails

The execution remains diagnostic, not ranking evidence:

```text
private_holdout_used: false
controller_family_ranking_claim_made: false
winner_selected: false
finite_window_vs_gru_conclusion_made: false
paper_level_claim_made: false
level3_self_id_claim_made: false
```

Post-execution audit must not accept return improvement alone. The next
evidence question is whether targeted containment changes the M2256/M2257
failure slices:

```text
mid_offtrack_delta vs M2244 <= 0
mild_overshoot_delta vs M2244 <= 0
global_offtrack_count < 110
collision_count <= 107
max_step_noncompletion_count == 0
```

The execution itself only establishes whether the targeted configs can train
and produce candidate-checkpoint evidence.

## Failure Handling

Fail closed if any of these occur:

```text
M2259 matrix is missing or incomplete
profile set or seed set differs from the M2259 matrix
target value mismatch count is nonzero
contract violation count is nonzero
completed_run_count != 15
candidate_eval_count != 120
selected_checkpoint_count != 15
metrics are non-finite
guardrail_violation_count != 0
```

## Next

Admit:

```text
m2262-paper-route-current-sim-midcourse-corridor-containment-training-execution
```

M2262 may run training through the fixed command above. Interpretation remains
blocked until M2263 result audit and later outcome localization.
