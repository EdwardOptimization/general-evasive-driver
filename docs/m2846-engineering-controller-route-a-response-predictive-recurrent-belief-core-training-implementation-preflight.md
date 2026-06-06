# M2846 Engineering Controller Route A Response-Predictive Recurrent-Belief Core Training Implementation Preflight

## Metadata

- status: completed
- result_class: `engineering_controller_route_a_response_predictive_recurrent_belief_core_training_implementation_preflight_pass`
- summary: `runs/m2846_engineering_controller_route_a_response_predictive_recurrent_belief_core_training_implementation_preflight/summary.json`
- candidate checkpoint: `runs/m2846_engineering_controller_route_a_response_predictive_recurrent_belief_core_training_implementation_preflight/checkpoints/m2846_response_predictive_recurrent_belief_candidate.pt`
- checkpoint manifest: `runs/m2846_engineering_controller_route_a_response_predictive_recurrent_belief_core_training_implementation_preflight/checkpoint_manifest.json`
- parameter group trace: `runs/m2846_engineering_controller_route_a_response_predictive_recurrent_belief_core_training_implementation_preflight/parameter_group_trace.csv`
- response target schema rows: `runs/m2846_engineering_controller_route_a_response_predictive_recurrent_belief_core_training_implementation_preflight/response_target_schema_rows.csv`
- proof gate rows: `runs/m2846_engineering_controller_route_a_response_predictive_recurrent_belief_core_training_implementation_preflight/proof_gate_rows.csv`
- generalization gate rows: `runs/m2846_engineering_controller_route_a_response_predictive_recurrent_belief_core_training_implementation_preflight/generalization_gate_rows.csv`
- promotion guard rows: `runs/m2846_engineering_controller_route_a_response_predictive_recurrent_belief_core_training_implementation_preflight/promotion_guard_rows.csv`
- follow-up manifest: `experiments/manifests/m2847-engineering-controller-route-a-response-predictive-recurrent-belief-core-training-implementation-preflight-result-audit.json`
- next: `m2847-engineering-controller-route-a-response-predictive-recurrent-belief-core-training-implementation-preflight-result-audit`

## Implementation Preflight Result

```text
training_status: completed
source_load_mode: partial_response_prediction_head
total_steps: 8
rollout_steps: 8
num_envs: 1
response_prediction_dim: 9
response_prediction_horizon: 4
response_prediction_loss_mean: 0.3585260510444641
candidate_checkpoint_written: True
changed_parameter_groups: response_encoder,online_gru_cell,response_context_fusion,critic,log_std,response_prediction_head
non_actor_head_changed_groups: response_encoder,online_gru_cell,response_context_fusion,response_prediction_head
actor_mean_bias_only: False
gate_matrix_pass: True
failed_gate_ids: none
```

The bounded PPO smoke is implementation evidence only. It is not a validation run, ranking run, promotion decision, success-rate verdict, driver-performance claim, current-sim verdict, high-fidelity validation result, paper result, full-driver result, or self-ID result.

## Actor And Target Boundary

```text
actor_observation_dim: 72
action_dim: 3
actor_encoder: human_view_online_gru
hidden_or_oracle_actor_inputs_required: false
response_prediction_target_indices: 0..8
excluded_previous_command_indices: 9,10,11
```

## Prior Diagnostic Accounting

```text
M2838 diagnostic_success_count: 1
M2838 diagnostic_collision_count: 2
M2838 diagnostic_offtrack_count: 13
ordinary_success_denominator_allowed: false
```

## Claim Boundary

Allowed M2846 claim:

```text
bounded implementation-preflight artifacts were produced and are ready for M2847 audit
```

Rejected claims:

```text
checkpoint_promoted=false
validation_run=false
ranking_run=false
success_rate_computed=false
driver_performance_claim_made=false
paper_claim_made=false
current_sim_verdict_claim_made=false
high_fidelity_validation_claim_made=false
full_ideal_driver_gate_passed=false
level3_self_id_claim_made=false
```
