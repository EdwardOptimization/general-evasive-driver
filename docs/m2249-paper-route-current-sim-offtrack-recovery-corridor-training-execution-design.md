# M2249 Paper-Route Current-Sim Offtrack/Recovery/Corridor Training Execution Design

- status: completed
- decision: `current_sim_offtrack_recovery_corridor_training_execution_design_admit_execution`
- manifest: `experiments/manifests/m2249-paper-route-current-sim-offtrack-recovery-corridor-training-execution-design.json`
- parent result: `runs/m2248_paper_route_current_sim_offtrack_recovery_corridor_reward_extension_materialization/summary.json`

## Admission Evidence

M2248 is a clean materialization artifact:

```text
result_class: current_sim_offtrack_recovery_corridor_reward_extension_materialization_pass
materialized_config_count: 15
training_matrix_row_count: 15
profile_set_matched: true
seed_set_matched: true
budget_signature_count: 1
contract_violation_count: 0
track_width_widened_count: 0
guardrail_violation_count: 0
```

The execution must use exactly:

```text
runs/m2248_paper_route_current_sim_offtrack_recovery_corridor_reward_extension_materialization/training_matrix.csv
```

## Execution Design

Use the existing candidate-checkpoint runner:

```bash
PYTHONPATH=src python -m autodrift.paper_route_current_sim_training_stability_repair_execution \
  --training-matrix runs/m2248_paper_route_current_sim_offtrack_recovery_corridor_reward_extension_materialization/training_matrix.csv \
  --output-dir runs/m2250_paper_route_current_sim_offtrack_recovery_corridor_training_execution \
  --execution-root runs/m2250_paper_route_current_sim_offtrack_recovery_corridor_training_execution \
  --task-id m2250-paper-route-current-sim-offtrack-recovery-corridor-training-execution \
  --next-blocker m2251-paper-route-current-sim-offtrack-recovery-corridor-training-execution-result-audit \
  --device cpu
```

This runner should:

```text
copy M2248 configs into the execution output directory
run exactly 15 train_ppo jobs
keep total_steps = 32768
keep checkpoint_interval_steps = 4096
evaluate 8 candidate checkpoints per run
write 120 candidate eval rows
write 15 selected checkpoint rows
write profile aggregates
```

## Guardrails

The execution is still diagnostic, not ranking evidence:

```text
private_holdout_used: false
controller_family_ranking_claim_made: false
winner_selected: false
finite_window_vs_gru_conclusion_made: false
paper_level_claim_made: false
level3_self_id_claim_made: false
```

Post-execution audit must compare against M2241/M2244 only as repair evidence:

```text
selected_checkpoint_profile_floor_pass_count
selected_beats_final_count
selected_eval_return_mean
selected_eval_termination_rate
candidate_eval_count
guardrail_violation_count
```

The execution should not claim success merely because reward increased. A useful
repair must later reduce selected-checkpoint offtrack without materially raising
collision.

## Failure Handling

Fail closed if any of these occur:

```text
M2248 matrix is missing or incomplete
profile set or seed set differs from the M2248 matrix
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
m2250-paper-route-current-sim-offtrack-recovery-corridor-training-execution
```

M2250 may run training through the fixed command above. Interpretation remains
blocked until M2251 result audit.
