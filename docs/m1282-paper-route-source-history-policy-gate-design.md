# M1282 Paper-Route Source-History Policy Gate Design

## Summary

M1282 designs the first policy-side gate for the M1280 four-wheel source
response histories.

Decision:

```text
source_history_policy_gate_design_admit_no_training_implementation
```

The next step should implement a no-training, eval-only gate:

```text
m1283-paper-route-source-history-policy-gate-implementation
```

This gate should answer a narrow question:

```text
Given the same current source-intervention observation, does a recurrent actor
score preferred/rejected actions differently when its hidden state is built from
the correct source response history versus the same-pair wrong response history?
```

It must not train, run PPO, promote, use private holdout, add actor inputs, or
claim self-identification.

## Inputs

Required inputs:

```text
checkpoint path
runs/m1280_four_wheel_source_response_history_materialization/history_frame_rows.csv
runs/m1280_four_wheel_source_response_history_materialization/history_intervention_rows.csv
runs/m1280_four_wheel_source_response_history_materialization/wrong_history_pair_rows.csv
runs/m1277_four_wheel_source_intervention_materialization/intervention_observations.csv
runs/m1277_four_wheel_source_intervention_materialization/intervention_action_sequences.csv
```

Default eval checkpoint for the first implementation:

```text
runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
```

The checkpoint must load through:

```text
autodrift.checkpoints.load_actor_critic_checkpoint
```

Required actor contract:

```text
actor_encoder in {human_view_online_gru, response_critical_online_gru}
obs_dim == 72
response_feature_indices == 0..11
context_feature_indices == 12..71
```

If the checkpoint is not a canonical 72-value human-view online recurrent actor,
the gate must stop with `contract_violation`.

## Canonical History Projection

M1280 history rows are source-history artifacts, not canonical actor frames.
The implementation must project each `history_frame_rows.csv` row into a
72-value frame before replaying it through the recurrent actor.

Projection for response indices:

| actor index | projected value |
| ---: | --- |
| 0 | `vx / 20.0` |
| 1 | `vy / 12.0` |
| 2 | `yaw_rate / 2.5` |
| 3 | `ax / 15.0` |
| 4 | `ay / 15.0` |
| 5 | `steer_state / max_steer` |
| 6 | `steer_rate / max_steer_rate` |
| 7 | `clip(drive_state / max_drive_force, 0, 1)` |
| 8 | `clip(brake_state / max_brake_force, 0, 1)` |
| 9 | `prev_cmd_steer` |
| 10 | `0.5 * (prev_cmd_throttle + 1.0)` |
| 11 | `0.5 * (prev_cmd_brake + 1.0)` |

Use the source-side four-wheel defaults unless the M1280 artifact later records
explicit params:

```text
max_steer = 0.62
max_steer_rate = 3.5
max_drive_force = 8200.0
max_brake_force = 6000.0
```

The implementation must clip only actuator state and physical pedal command
channels to their expected actor ranges. It should not clip kinematic response
channels except through the documented normalization.

Context indices during prefix replay:

```text
indices 12..71 = zeros
```

Reason:

```text
For the canonical response/context actor, the GRU hidden update depends only on
response indices 0..11. Context is only fused for the action at the current
frame. Zero context during prefix replay prevents accidental scene leakage and
does not affect the hidden-state update.
```

The implementation should include a focused test that verifies replaying the
same response prefix with zero context and current-observation context produces
the same final hidden state for `human_view_online_gru`.

## Current Observation

The action query must use the actual current source-intervention observation:

```text
runs/m1277_four_wheel_source_intervention_materialization/intervention_observations.csv
```

For each `history_intervention_rows.csv` row:

```text
observation = intervention_observations[intervention_id]
correct_hidden = replay(history_id)
wrong_hidden = replay(wrong_history_id)
```

The same `observation` must be used for both hidden states. The only variable
being tested is the response-history hidden state.

Forbidden current-observation modifications:

```text
do not append condition, fault, pair, probe, margin, success, or source labels;
do not insert cmd_* prefix action fields;
do not add per-wheel fault metadata;
do not overwrite obstacle or road features unless a separate ablation is
pre-registered.
```

## Action Targets

Use first-step preferred and rejected actions from:

```text
intervention_action_sequences.csv
```

For each intervention:

```text
preferred_action = role == preferred, step == 0
rejected_action = role == rejected, step == 0
```

The action targets are already in the network action convention:

```text
[steer, throttle_command, brake_command]
```

where throttle and brake command channels are in the normalized network range
`[-1, 1]`. Do not convert these action targets to physical pedals before
evaluating policy log probabilities or action-mean distances.

## Metrics

For every history-intervention row, compute these log-probability scores:

```text
logp_cp = log pi(preferred_action | current_observation, correct_hidden)
logp_cr = log pi(rejected_action  | current_observation, correct_hidden)
logp_wp = log pi(preferred_action | current_observation, wrong_hidden)
logp_wr = log pi(rejected_action  | current_observation, wrong_hidden)
```

Primary margins:

```text
correct_preference_margin = logp_cp - logp_cr
wrong_history_preference_margin = logp_wr - logp_wp
preferred_hidden_margin = logp_cp - logp_wp
rejected_hidden_margin = logp_wr - logp_cr
```

Action-mean diagnostics:

```text
mean_correct = actor_mean(current_observation, correct_hidden)
mean_wrong = actor_mean(current_observation, wrong_hidden)
history_action_l2 = ||mean_correct - mean_wrong||_2
correct_closer_to_preferred = dist(mean_correct, preferred) < dist(mean_correct, rejected)
wrong_closer_to_rejected = dist(mean_wrong, rejected) < dist(mean_wrong, preferred)
```

Aggregate metrics:

```text
row_count
finite_row_count
correct_preference_positive_count
wrong_history_preference_positive_count
both_directional_count
preferred_hidden_margin_positive_count
rejected_hidden_margin_positive_count
history_action_l2_mean
history_action_l2_min
history_action_l2_p10
history_action_l2_median
history_action_l2_p90
```

Secondary controls:

```text
zero_hidden_action scores
reset_hidden_action scores
correct_history versus zero_hidden action L2
wrong_history versus zero_hidden action L2
```

The reset/zero controls are diagnostics only. The main gate is correct history
versus same-pair wrong history.

## Result Classification

M1283 should classify the result, but not promote anything.

Infrastructure pass:

```text
all artifacts are written;
all rows finite;
checkpoint contract is canonical 72-value human-view online recurrent;
hidden replay uses projected M1280 response frames;
no training, PPO, promotion, private holdout, or actor-input expansion occurs.
```

History-signal positive threshold:

```text
both_directional_fraction >= 0.60
preferred_hidden_margin_positive_fraction >= 0.60
history_action_l2_mean >= 0.02
```

History-signal weak threshold:

```text
both_directional_fraction < 0.60
or preferred_hidden_margin_positive_fraction < 0.60
or history_action_l2_mean < 0.02
```

Interpretation:

```text
positive: the current checkpoint has action-level sensitivity to M1280 source
histories and can be routed to a no-training outcome/simulation replay design;

weak: the current checkpoint does not show enough action-level sensitivity on
this source corpus, so route to source-history objective/adapter design rather
than PPO.
```

Even a positive result remains action-level evidence. It does not prove
closed-loop avoidance, driver performance, or self-identification.

## Output Artifacts

M1283 should write:

```text
runs/m1283_source_history_policy_gate/summary.json
runs/m1283_source_history_policy_gate/policy_gate_rows.csv
runs/m1283_source_history_policy_gate/history_projection_audit.csv
```

`policy_gate_rows.csv` fields:

```text
history_intervention_id
intervention_id
pair_id
condition
probe_template
correct_history_id
wrong_history_id
preferred_candidate_id
rejected_candidate_id
logp_cp
logp_cr
logp_wp
logp_wr
correct_preference_margin
wrong_history_preference_margin
preferred_hidden_margin
rejected_hidden_margin
history_action_l2
correct_closer_to_preferred
wrong_closer_to_rejected
finite
```

The `pair_id`, `condition`, and `probe_template` fields are artifact metadata
only. The implementation must not feed them to the actor.

`history_projection_audit.csv` fields:

```text
history_id
frame_count
all_projected_finite
max_abs_response_value
drive_state_min
drive_state_max
brake_state_min
brake_state_max
prev_throttle_min
prev_throttle_max
prev_brake_min
prev_brake_max
zero_context_hidden_matches_current_context
```

`summary.json` should include:

```text
checkpoint
checkpoint_actor_encoder
row_count
finite_row_count
projection_valid_count
wrong_history_valid_count
both_directional_fraction
preferred_hidden_margin_positive_fraction
history_action_l2_mean
history_action_l2_median
result_class
labels_enter_actor_input
training_started
ppo_used
promoted
private_holdout_used
actor_input_contract_changed
accepted_thresholds_relaxed
high_fidelity_validation_claimed
```

## Tests

M1283 should add focused tests for:

```text
canonical projection shape is 72;
projected response indices match docs/observation-contract.md normalization;
cmd_* columns are not appended to actor observations;
metadata columns are not actor inputs;
zero-context and current-context prefix replay produce identical hidden states
for human-view online GRU;
policy gate rows are finite on a tiny synthetic fixture.
```

## Next Step

Admit implementation-only:

```text
m1283-paper-route-source-history-policy-gate-implementation
```

M1283 may implement and run the gate against the default public-gate checkpoint
as eval-only diagnostic evidence. It must not train, run PPO, promote, use
private holdout, expand actor inputs, or claim self-identification.
