# M2845 Engineering Controller Route A Response-Predictive Recurrent-Belief Core Training Implementation Preflight Design

## Metadata

- status: completed
- decision: `admit_m2846_response_predictive_recurrent_belief_core_training_implementation_preflight`
- manifest: `experiments/manifests/m2845-engineering-controller-route-a-response-predictive-recurrent-belief-core-training-implementation-preflight-design.json`
- design artifact: `docs/m2845-engineering-controller-route-a-response-predictive-recurrent-belief-core-training-implementation-preflight-design.md`
- parent audit: `docs/m2844-engineering-controller-route-a-driver-like-recurrent-belief-architecture-training-redesign-protocol-result-audit.md`
- parent protocol: `docs/m2843-engineering-controller-route-a-driver-like-recurrent-belief-architecture-training-redesign-protocol-design.md`
- source checkpoint: `runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt`
- follow-up manifest: `experiments/manifests/m2846-engineering-controller-route-a-response-predictive-recurrent-belief-core-training-implementation-preflight.json`
- next: `m2846-engineering-controller-route-a-response-predictive-recurrent-belief-core-training-implementation-preflight`

## Design Decision

M2845 admits a bounded implementation preflight:

```text
admit_m2846_response_predictive_recurrent_belief_core_training_implementation_preflight
```

M2845 itself is design-only. It does not edit implementation code, run PPO,
reset, step, roll out, create a checkpoint, validate, rank, promote, or claim
driver performance.

M2846 is allowed to be the first code/config implementation preflight for the
accepted M2843/M2844 protocol. It may add a runner module and execute a bounded
training smoke only to prove the implementation path and artifact gates. It may
not promote the candidate or claim repair success.

## Existing Implementation Surface

The design can use current code without changing the actor contract:

```text
src/autodrift/train_ppo.py:
  PPOConfig.response_prediction_aux_coef
  PPOConfig.response_prediction_dim
  PPOConfig.response_prediction_horizon
  PPOConfig.response_prediction_stride
  PPOConfig.recurrent_sequence_training
  ActorCritic.response_prediction_head
  ActorCritic.predict_response_recurrent_sequence
  build_response_prediction_targets
  train(...)

src/autodrift/artifacts.py:
  write_json
  write_csv_rows
  read_json

src/autodrift/config.py:
  build_env_config
  env_config_to_dict
  build_curriculum
  env_config_for_step

src/autodrift/checkpoints.py:
  load_actor_critic_checkpoint

src/autodrift/engineering_controller_route_a_source_only_belief_stress_short_training_continuation_preflight.py:
  artifact and gate writer pattern only; the actor_mean.bias-only update method
  is explicitly rejected as the new training method
```

`train_ppo.build_response_prediction_targets` predicts the first
`response_prediction_dim` observation channels. Therefore M2846 must set:

```text
response_prediction_dim: 9
response_prediction_target_indices: 0..8
```

This target covers:

```text
0 vx
1 vy
2 yaw_rate
3 ax
4 ay
5 steer_actuator
6 steer_rate
7 throttle_actuator
8 brake_actuator
```

Indices 9-11 are previous physical command fields. They remain actor-visible
inputs, but they are not response-prediction targets. Hidden dynamics and
evaluator labels remain excluded.

## Code And Config Boundary For M2846

M2846 should add one runner module:

```text
src/autodrift/engineering_controller_route_a_response_predictive_recurrent_belief_core_training_implementation_preflight.py
```

The runner should call existing training infrastructure instead of rewriting
PPO:

```text
autodrift.config.build_env_config
autodrift.config.env_config_to_dict
autodrift.train_ppo.PPOConfig
autodrift.train_ppo.train
autodrift.train_ppo.load_init_checkpoint_state
autodrift.train_ppo.build_response_prediction_targets
```

Allowed M2846 implementation edits:

```text
new M2846 runner module
optional focused tests for response target schema or parameter-group tracing
minimal helper functions inside the new runner
```

Conditionally allowed implementation edits:

```text
small non-behavioral helper in train_ppo.py only if the runner cannot otherwise
trace trainable parameter groups or load the source checkpoint with a response
prediction head
```

Forbidden M2846 implementation edits:

```text
change observation shape
change deployed action shape
add hidden/oracle actor inputs
add wheel/slip/privileged branch
change reward semantics for the preflight
change success definitions
overwrite active configs
install or fetch external dependencies
modify source or HF3 dependency trees
```

## M2846 Bounded Training Smoke

M2846 should execute a deliberately small training smoke through the new runner:

```text
source checkpoint:
  M2655 mitigation-preserving actor-head repair checkpoint

actor_encoder:
  human_view_online_gru

history_baseline_level:
  L3_online_gru

env:
  history_length=1
  action_history_mode=full
  include_privileged_params=false
  wheel_observation_mode=none
  road_lookahead_count=8
  obstacle_slots=4

PPO smoke budget:
  total_steps: small bounded value selected by M2846 runner
  rollout_steps: > response_prediction_horizon
  num_envs: small CPU-safe value
  update_epochs: small CPU-safe value
  eval_episodes: 0 or omitted from the runner-level claim accounting

response objective:
  recurrent_sequence_training=true
  response_prediction_aux_coef > 0
  response_prediction_dim=9
  response_prediction_horizon=4
  response_prediction_stride=1

preservation:
  baseline_action_anchor_checkpoint=M2655
  baseline_action_anchor_coef > 0

candidate:
  written only under the M2846 run directory
  checkpoint_promoted=false
  active_config_overwritten=false
```

The preflight may collect training rollouts because that is needed to test the
implementation path. It must label them as training smoke rows, not validation
or performance rows.

## Required M2846 Artifacts

M2846 should write:

```text
protocol_config_snapshot.json
ppo_config_snapshot.json
env_config_snapshot.json
response_target_schema_rows.csv
training_seed_rows.csv
training_run_rows.csv
train_metrics.csv
checkpoint_manifest.json
parameter_group_trace.csv
response_prediction_probe_rows.csv
hidden_intervention_probe_rows.csv
proof_gate_rows.csv
generalization_gate_rows.csv
promotion_guard_rows.csv
actor_contract_guard_rows.csv
claim_boundary_rows.csv
gate_matrix.csv
summary.json
run_state.json
follow_up_manifest.json
```

The candidate checkpoint path should live under:

```text
runs/m2846_engineering_controller_route_a_response_predictive_recurrent_belief_core_training_implementation_preflight/checkpoints/
```

It must not replace any baseline path.

## Artifact Schema Requirements

`response_target_schema_rows.csv` must include:

```text
target_index
observation_index
channel_name
normalization
actor_visible_input
hidden_or_oracle
label_or_verdict
included_in_response_prediction
claim_boundary
```

`parameter_group_trace.csv` must include:

```text
parameter_group
parameter_count
source_hash
candidate_hash
changed
delta_l2
delta_max_abs
trainable
required_for_protocol
actor_head_only_group
claim_boundary
```

The trace must include at least:

```text
response_encoder
online_gru_cell
response_context_fusion
actor_mean
critic
log_std
response_prediction_head
```

The proof gate `proof_not_actor_head_only` must fail unless at least one of
these changes:

```text
response_encoder
online_gru_cell
response_context_fusion
response_prediction_head
```

`response_prediction_probe_rows.csv` must include finite probe rows for the
configured response target channels and horizon. It should report loss or error
as a smoke diagnostic only.

`hidden_intervention_probe_rows.csv` should record normal, reset-hidden,
zero-history, and wrong-history intervention hooks if they can be collected
inside the bounded budget. If not collected in M2846, the row must record
`executed=false` and route the missing proof to the next audit instead of
claiming history evidence.

## Proof Gates For M2846

Required proof gates:

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

## Generalization Gates For M2846

M2846 is an implementation preflight, not a generalization result. Its
generalization gates should be admission guards only:

```text
generalization_seed_split_written
generalization_no_single_seed_verdict
generalization_prior_surface_guardrails_visible
generalization_failure_taxonomy_not_collapsed
generalization_no_current_sim_verdict
generalization_no_source_only_vs_current_sim_merge
```

No M2846 row may be used as a validation distribution or current-sim verdict.

## Promotion Guards For M2846

Required promotion guards:

```text
promotion_checkpoint_not_promoted
promotion_no_winner_selected
promotion_no_success_rate_verdict
promotion_no_active_config_overwrite
promotion_no_baseline_replacement
promotion_requires_future_audit
```

## Follow-Up Route

M2845 registers:

```text
m2846-engineering-controller-route-a-response-predictive-recurrent-belief-core-training-implementation-preflight
```

If M2846 passes, it should route to M2847 result audit. If implementation
cannot preserve the actor contract, cannot write the parameter trace, or cannot
produce a non-actor-head-only candidate under a bounded budget, M2846 must
record the failure and route to audit or branch stop instead of silently
weakening the protocol.

## Claim Boundary

Allowed M2845 claim:

```text
M2845 defines exact implementation-preflight boundaries for M2846 and registers
a bounded implementation-preflight manifest.
```

Rejected claims:

```text
implementation_completed=false
training_completed=false
checkpoint_created=false
checkpoint_promoted=false
repair_success=false
validation_readiness=false
validation_result=false
driver_performance=false
controller_family_ranking=false
winner_selection=false
success_rate_verdict=false
paper_evidence=false
finite_window_vs_gru_conclusion=false
current_sim_verdict=false
high_fidelity_validation=false
full_ideal_driver_completion=false
level3_self_identification=false
```
