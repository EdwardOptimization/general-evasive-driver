# M1533 Paper-Route Fresh Ambiguity History-Intervention Design

## Summary

M1533 designs bounded history interventions over the M1531 accepted measured
pairs.

Decision:

```text
fresh_ambiguity_history_intervention_design_admit_bounded_implementation
```

This is design only. It does not run history interventions, materialize
candidates, export a corpus, train, run PPO, promote, use private holdout,
change actor inputs, or claim self-identification.

## Input Pairs

M1531 accepted three measured pairs:

```text
pair-0000:
  t4_staged_warmup_capability -> t4_actuator_delay_response
  scene_context_distance: 0.0537515937505914
  current_ego_distance: 0.0887242820667605
  first_action_l2: 0.33857090172787957
  terminal_margin_gap: 24.887879066124782

pair-0002:
  t4_actuator_delay_response -> capability_step_up
  scene_context_distance: 0.02335932759849905
  current_ego_distance: 0.06534562493267661
  first_action_l2: 0.2611559180120488
  terminal_margin_gap: 12.893350460655034

pair-0006:
  capability_step_down -> capability_step_up
  scene_context_distance: 0.03301448947714787
  current_ego_distance: 0.03275207306630136
  first_action_l2: 0.12691066088758446
  terminal_margin_gap: 4.39923914583456
```

These are useful measured pair targets, but they are not self-ID evidence until
history interventions are executed and audited.

## Anchor Replay Contract

M1534 should reconstruct each accepted pair from:

```text
runs/m1531_fresh_ambiguity_measured_mining_smoke/measured_pair_candidates.csv
runs/m1531_fresh_ambiguity_measured_mining_smoke/measured_source_spec_rows.csv
```

For each left/right trace:

```text
1. Rebuild the fresh source row and P0 env hook spec.
2. Replay the fixed public actor from reset to the anchor.
3. Capture env state, current observation, actor hidden state, action history,
   response stream, and previous physical commands exactly before the anchor
   action.
4. Verify the anchor was reached and the actor contract remains P0.
```

Primary anchor:

```text
decision
```

Fallback anchors:

```text
decision_minus_8
reveal_plus_4
```

Fallback anchors are allowed only if the decision anchor cannot be replayed for
a source. The artifact must record the selected anchor and replay failure type.

## Intervention Variants

Required variants for each accepted pair and anchor:

```text
normal
reset_hidden_once_at_anchor
reset_hidden_every_step_from_anchor
zero_current_response_from_anchor
zero_action_history_from_anchor
delayed_hidden_8_at_anchor
delayed_hidden_16_at_anchor
wrong_history_donor_hidden_at_anchor
donor_response_action_stream_from_anchor
donor_response_action_plus_hidden_from_anchor
```

### Normal

Run the target env from the target anchor without intervention. This is the
baseline for action and terminal-margin gaps.

### Reset / Zero Controls

These test response/current-frame dependence:

```text
reset_hidden_once_at_anchor
reset_hidden_every_step_from_anchor
zero_current_response_from_anchor
zero_action_history_from_anchor
```

They are useful positive controls but are not sufficient self-ID evidence.

### Delayed Hidden

Use target hidden state from earlier in the same target rollout:

```text
delayed_hidden_8_at_anchor
delayed_hidden_16_at_anchor
```

This tests whether recent temporal evidence changes behavior.

### Wrong-History Donor Hidden

At the target anchor, keep:

```text
target env state;
target scene/context;
target current observation;
target actuator state;
target previous command fields.
```

Replace only:

```text
actor recurrent hidden state = donor hidden state at matched anchor.
```

This is the cleanest direct wrong-history test.

### Donor Response/Action Stream

At the target anchor, keep target scene/context fields and target env state, but
replace deployable response/action-history observation fields:

```text
ego response stream;
actuator response fields;
previous physical command fields.
```

Variants:

```text
donor_response_action_stream_from_anchor:
  donor response/action fields, target hidden.

donor_response_action_plus_hidden_from_anchor:
  donor response/action fields and donor hidden.
```

These are diagnostic observation-surgery interventions, not deployable actor
inputs.

## Metrics

Each intervention row must report:

```text
pair_id
target_side: left/right
donor_side: right/left
anchor_name
anchor_step
variant
target_replay_status
donor_replay_status
first_action_steer/throttle/brake
first_action_l2_vs_normal
prefix_action_l2_vs_normal
terminal_margin
terminal_margin_gap_from_normal
success
success_drop_from_normal
collision
obstacle_completed
road_departure_or_spin if available
continuation_steps
```

Also report measured preconditions:

```text
anchor_scene_context_distance
anchor_current_ego_distance
anchor_recent_window_distance if available
target_donor_hidden_l2
target_donor_response_l2
target_donor_action_history_l2
```

## Artifact Contract

M1534 should write:

```text
accepted_pair_rows.csv
anchor_replay_rows.csv
history_intervention_rows.csv
history_intervention_pair_summary.csv
history_intervention_variant_summary.csv
history_intervention_guardrail_summary.csv
summary.json
```

The summary should include:

```text
accepted_pair_count
anchor_replay_success_count
anchor_replay_failure_count
intervention_row_count
wrong_history_row_count
donor_response_action_row_count
reset_zero_control_row_count
max_wrong_history_margin_gap
max_donor_response_action_margin_gap
success_drop_count
guardrail_violation_count
```

## Public Smoke Gates

Pass conditions:

```text
accepted_pair_count >= 3
anchor_replay_success_count >= 2
wrong_history_row_count >= 2
donor_response_action_row_count >= 2
reset_zero_control_row_count >= 2
guardrail_violation_count == 0
candidate_materialized == false
training/replay/PPO/promoted/private holdout all false
actor_input_contract_changed == false
```

Evidence-quality targets:

```text
wrong-history or donor-response/action terminal margin gap >= 0.02;
or wrong-history or donor-response/action success drop >= 1;
and reset/zero-current effects are reported separately.
```

If evidence-quality targets fail, route to audit. Do not materialize candidates
or weaken the self-ID standard.

## Guardrails

```text
candidate_materialized: false
training_started: false
evaluation_started: false
replay_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
training_corpus_exported: false
labels_enter_actor_input: false
level3_self_id_claim_made: false
```

## Next Milestone

Next:

```text
m1534-paper-route-fresh-ambiguity-history-intervention-implementation
```

M1534 should implement the bounded intervention runner and run one public smoke.
It must still block candidate materialization, corpus export, training, PPO,
promotion, private holdout, actor-input changes, and self-ID claims.
