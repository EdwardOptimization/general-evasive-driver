# M2848 Engineering Controller Route A Response-Predictive Recurrent-Belief Core Training Bounded Continuation Preflight

## Metadata

- status: completed
- result_class: `engineering_controller_route_a_response_predictive_recurrent_belief_core_training_bounded_continuation_preflight_pass`
- summary: `runs/m2848_engineering_controller_route_a_response_predictive_recurrent_belief_core_training_bounded_continuation_preflight/summary.json`
- candidate checkpoint: `runs/m2848_engineering_controller_route_a_response_predictive_recurrent_belief_core_training_bounded_continuation_preflight/checkpoints/m2848_response_predictive_recurrent_belief_continuation_candidate.pt`
- checkpoint manifest: `runs/m2848_engineering_controller_route_a_response_predictive_recurrent_belief_core_training_bounded_continuation_preflight/checkpoint_manifest.json`
- parameter group trace: `runs/m2848_engineering_controller_route_a_response_predictive_recurrent_belief_core_training_bounded_continuation_preflight/parameter_group_trace.csv`
- response target schema rows: `runs/m2848_engineering_controller_route_a_response_predictive_recurrent_belief_core_training_bounded_continuation_preflight/response_target_schema_rows.csv`
- proof gate rows: `runs/m2848_engineering_controller_route_a_response_predictive_recurrent_belief_core_training_bounded_continuation_preflight/proof_gate_rows.csv`
- generalization gate rows: `runs/m2848_engineering_controller_route_a_response_predictive_recurrent_belief_core_training_bounded_continuation_preflight/generalization_gate_rows.csv`
- promotion guard rows: `runs/m2848_engineering_controller_route_a_response_predictive_recurrent_belief_core_training_bounded_continuation_preflight/promotion_guard_rows.csv`
- follow-up manifest: `experiments/manifests/m2849-engineering-controller-route-a-response-predictive-recurrent-belief-core-training-bounded-continuation-result-audit.json`
- next: `m2849-engineering-controller-route-a-response-predictive-recurrent-belief-core-training-bounded-continuation-result-audit`

## Bounded Continuation Result

```text
training_status: completed
source_load_mode: strict
total_steps: 32
rollout_steps: 16
num_envs: 1
update_epochs: 2
response_prediction_dim: 9
response_prediction_horizon: 4
response_prediction_loss_mean: 0.32993096113204956
candidate_checkpoint_written: True
changed_parameter_groups: response_encoder,online_gru_cell,response_context_fusion,actor_mean,critic,log_std,response_prediction_head
non_actor_head_changed_groups: response_encoder,online_gru_cell,response_context_fusion,response_prediction_head
actor_mean_bias_only: False
gate_matrix_pass: True
failed_gate_ids: none
```

The bounded continuation run is training-preflight evidence only. It is not a validation run, ranking run, promotion decision, success-rate verdict, driver-performance claim, current-sim verdict, high-fidelity validation result, paper result, full-driver result, or self-ID result.

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

Allowed M2848 claim:

```text
bounded continuation-preflight artifacts were produced and are ready for M2849 audit
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
