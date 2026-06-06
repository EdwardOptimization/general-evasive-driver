# M2866 Engineering Controller Route A Response-Predictive Recurrent-Belief Localized Response-Prediction Training Implementation Preflight

## Metadata

- status: completed
- result_class: `engineering_controller_route_a_response_predictive_recurrent_belief_localized_response_prediction_training_implementation_preflight_pass`
- summary: `runs/m2866_engineering_controller_route_a_response_predictive_recurrent_belief_localized_response_prediction_training_implementation_preflight/summary.json`
- candidate checkpoint: `runs/m2866_engineering_controller_route_a_response_predictive_recurrent_belief_localized_response_prediction_training_implementation_preflight/checkpoints/m2866_localized_response_prediction_training_candidate.pt`
- checkpoint manifest: `runs/m2866_engineering_controller_route_a_response_predictive_recurrent_belief_localized_response_prediction_training_implementation_preflight/checkpoint_manifest.json`
- response-loss weight rows: `runs/m2866_engineering_controller_route_a_response_predictive_recurrent_belief_localized_response_prediction_training_implementation_preflight/response_loss_weight_rows.csv`
- valid-target mask accounting rows: `runs/m2866_engineering_controller_route_a_response_predictive_recurrent_belief_localized_response_prediction_training_implementation_preflight/valid_target_mask_accounting_rows.csv`
- surface accounting rows: `runs/m2866_engineering_controller_route_a_response_predictive_recurrent_belief_localized_response_prediction_training_implementation_preflight/surface_accounting_rows.csv`
- rollback gate rows: `runs/m2866_engineering_controller_route_a_response_predictive_recurrent_belief_localized_response_prediction_training_implementation_preflight/rollback_gate_rows.csv`
- gate matrix: `runs/m2866_engineering_controller_route_a_response_predictive_recurrent_belief_localized_response_prediction_training_implementation_preflight/gate_matrix.csv`
- follow-up manifest: `experiments/manifests/m2867-engineering-controller-route-a-response-predictive-recurrent-belief-localized-response-prediction-training-implementation-result-audit.json`
- next: `m2867-engineering-controller-route-a-response-predictive-recurrent-belief-localized-response-prediction-training-implementation-result-audit`

## Bounded Implementation Result

```text
training_status: completed
source_load_mode: strict
total_steps: 32
rollout_steps: 16
num_envs: 1
update_epochs: 2
response_prediction_dim: 9
response_prediction_horizon: 4
response_loss_weights_match_m2864: True
response_prediction_loss_mean: 0.24616368114948273
candidate_checkpoint_written: True
changed_parameter_groups: response_encoder,online_gru_cell,response_context_fusion,actor_mean,critic,log_std,response_prediction_head
non_actor_head_changed_groups: response_encoder,online_gru_cell,response_context_fusion,response_prediction_head
gate_matrix_pass: True
failed_gate_ids: none
triggered_rollback_gate_ids: none
```

The bounded implementation run is training-preflight evidence only. It is not a validation run, ranking run, promotion decision, success-rate verdict, driver-performance claim, current-sim verdict, high-fidelity validation result, paper result, full-driver result, or self-ID result.

## M2864 Weight And Mask Contract

```text
response_loss_weight_row_count: 36
valid_target_mask_accounting_row_count: 4
valid_target_mask_accounting_pass: True
m2861_terminal_gap_accounted_row_count: 863
future_labels_actor_visible: false
terminal_or_unavailable_targets_imputed: false
```

## Public/Fresh Surface Boundary

```text
m2850_explanatory_surface_row_count: 16
fresh_disjoint_surface_row_count: 8
surface_accounting_pass: True
ordinary_success_denominator_allowed: false
ranking_admissible: false
checkpoint_promotion_admitted: false
```

## Actor And Claim Boundary

```text
actor_observation_dim: 72
action_dim: 3
actor_encoder: human_view_online_gru
hidden_or_oracle_actor_inputs_required: false
response_prediction_target_indices: 0..8
excluded_previous_command_indices: 9,10,11
validation_run: false
ranking_run: false
success_rate_computed: false
checkpoint_promoted: false
driver_performance_claim_made: false
paper_claim_made: false
current_sim_verdict_claim_made: false
high_fidelity_validation_claim_made: false
full_ideal_driver_gate_passed: false
level3_self_id_claim_made: false
```
