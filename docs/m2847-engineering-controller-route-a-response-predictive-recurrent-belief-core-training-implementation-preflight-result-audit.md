# M2847 Engineering Controller Route A Response-Predictive Recurrent-Belief Core Training Implementation Preflight Result Audit

## Metadata

- status: completed
- audit decision: `accept_m2846_response_predictive_recurrent_belief_core_training_implementation_preflight_route_to_m2848_bounded_continuation_preflight`
- manifest: `experiments/manifests/m2847-engineering-controller-route-a-response-predictive-recurrent-belief-core-training-implementation-preflight-result-audit.json`
- audit artifact: `docs/m2847-engineering-controller-route-a-response-predictive-recurrent-belief-core-training-implementation-preflight-result-audit.md`
- parent summary: `runs/m2846_engineering_controller_route_a_response_predictive_recurrent_belief_core_training_implementation_preflight/summary.json`
- parent result doc: `docs/m2846-engineering-controller-route-a-response-predictive-recurrent-belief-core-training-implementation-preflight.md`
- parent checkpoint manifest: `runs/m2846_engineering_controller_route_a_response_predictive_recurrent_belief_core_training_implementation_preflight/checkpoint_manifest.json`
- parent parameter trace: `runs/m2846_engineering_controller_route_a_response_predictive_recurrent_belief_core_training_implementation_preflight/parameter_group_trace.csv`
- follow-up manifest: `experiments/manifests/m2848-engineering-controller-route-a-response-predictive-recurrent-belief-core-training-bounded-continuation-preflight.json`
- next: `m2848-engineering-controller-route-a-response-predictive-recurrent-belief-core-training-bounded-continuation-preflight`

## Audit Decision

M2847 accepts M2846 as a complete claim-safe implementation preflight:

```text
accept_m2846_response_predictive_recurrent_belief_core_training_implementation_preflight_route_to_m2848_bounded_continuation_preflight
```

The acceptance is narrow. M2846 proves the response-predictive recurrent-belief
training path can be executed and audited under the unchanged actor contract. It
does not prove driver capability, validation readiness, current-sim performance,
paper evidence, high-fidelity readiness, full-driver completion, or level3
self-identification.

## Artifact Completeness Audit

M2846 wrote the required implementation-preflight artifacts:

```text
summary: present
candidate checkpoint: present
checkpoint manifest: present
response target schema rows: present
training seed rows: present
training run rows: present
train metrics: present
parameter group trace: present
response prediction probe rows: present
hidden intervention probe rows: present
proof gate rows: present
generalization gate rows: present
promotion guard rows: present
actor contract guard rows: present
claim boundary rows: present
gate matrix: present
run state: present
M2847 follow-up manifest from M2846: present
```

The M2846 summary reports:

```text
status_pass: true
required_artifacts_present: true
gate_matrix_pass: true
training_status: completed
candidate_checkpoint_written: true
```

## Actor And Target Boundary Audit

M2846 preserves the deployed actor boundary:

```text
actor_encoder: human_view_online_gru
actor observation shape: 72
action shape: 3
hidden/oracle actor input required: false
actor-visible labels: false
wheel_observation_mode: none
include_privileged_params: false
active_config_overwritten: false
```

The response-prediction target schema is clean:

```text
included target observation indices: 0,1,2,3,4,5,6,7,8
excluded previous-command indices: 9,10,11
hidden_or_oracle targets: false
label_or_verdict targets: false
```

This preserves the M2843/M2845 rule that previous physical commands remain
actor-visible context but are not next-response prediction targets.

## Implementation Evidence Audit

M2846 executed a bounded training smoke:

```text
total_steps: 8
rollout_steps: 8
num_envs: 1
device: cpu
response_prediction_dim: 9
response_prediction_horizon: 4
source_load_mode: partial_response_prediction_head
response_prediction_loss_mean: 0.3585260510444641
response_prediction_loss_finite: true
```

The partial load mode is expected because the M2655 source checkpoint used
response prediction dim 12 while M2846 restricts training-only targets to
observation indices 0-8.

The parameter trace is materially different from actor-head-only repair:

```text
changed groups:
  response_encoder
  online_gru_cell
  response_context_fusion
  critic
  log_std
  response_prediction_head

unchanged group:
  actor_mean

non_actor_head_changed_groups:
  response_encoder
  online_gru_cell
  response_context_fusion
  response_prediction_head

actor_mean_bias_only: false
```

This satisfies the M2843/M2845 requirement to move away from the rejected M2782
actor-head-only continuation pattern.

## Gate Audit

M2846 proof gates all pass:

```text
proof_actor_contract_72_3
proof_no_hidden_or_oracle_actor_input
proof_no_actor_visible_labels
proof_response_target_schema_clean
proof_response_prediction_head_enabled
proof_response_prediction_probe_finite
proof_recurrent_or_response_prediction_group_changed
proof_not_actor_head_only
proof_parameter_trace_complete
proof_m2838_negative_accounting_visible
proof_no_active_config_overwrite
```

M2846 generalization admission gates all pass, but they are not validation
results:

```text
generalization_seed_split_written
generalization_no_single_seed_verdict
generalization_prior_surface_guardrails_visible
generalization_failure_taxonomy_not_collapsed
generalization_no_current_sim_verdict
generalization_no_source_only_vs_current_sim_merge
```

M2846 promotion guards all pass:

```text
promotion_checkpoint_not_promoted
promotion_no_winner_selected
promotion_no_success_rate_verdict
promotion_no_active_config_overwrite
promotion_no_baseline_replacement
promotion_requires_future_audit
```

## Negative Evidence Retention

M2846 keeps M2838 visible as weak diagnostic evidence:

```text
M2838 diagnostic_success_count: 1
M2838 diagnostic_collision_count: 2
M2838 diagnostic_offtrack_count: 13
ordinary_success_denominator_allowed: false
```

Those rows remain outside performance denominators and are not actor-visible
labels or validation evidence.

## Limitations

M2846 is still an implementation preflight:

```text
training budget: 8 steps only
validation_run: false
ranking_run: false
winner_selected: false
checkpoint_promoted: false
success_rate_computed: false
hidden_intervention_probe_collected: false
driver_performance_claim_made: false
current_sim_verdict_claim_made: false
high_fidelity_validation_claim_made: false
paper_claim_made: false
level3_self_id_claim_made: false
full_ideal_driver_gate_passed: false
```

The result admits more bounded training evidence. It does not admit promotion,
validation, or a success-rate verdict.

## Accepted Follow-Up

M2847 routes to:

```text
m2848-engineering-controller-route-a-response-predictive-recurrent-belief-core-training-bounded-continuation-preflight
```

M2848 should implement and execute a bounded continuation preflight from the
M2846 candidate checkpoint. The continuation should increase training evidence
beyond the 8-step smoke, keep response targets at indices 0-8, preserve actor
72/action 3 and no hidden/oracle labels, write parameter and gate artifacts, and
route to M2849 audit. It must not run validation, rank checkpoints, promote a
checkpoint, compute a success-rate verdict, or claim driver performance,
current-sim, high-fidelity, paper, full-driver, or self-ID evidence.

## Claim Boundary

Allowed M2847 claim:

```text
M2846 implementation preflight artifacts are accepted as complete and
claim-safe for a bounded continuation-preflight route.
```

Rejected claims:

```text
new_training_run=false
validation_run=false
ranking_run=false
checkpoint_promoted=false
success_rate_verdict=false
repair_success=false
driver_performance=false
paper_evidence=false
finite_window_vs_gru_conclusion=false
current_sim_verdict=false
high_fidelity_validation=false
full_ideal_driver_completion=false
level3_self_identification=false
```
