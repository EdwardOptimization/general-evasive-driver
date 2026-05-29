# M1572 Paper-Route Source-Diverse Flip-Anchor History-Intervention Design

## Summary

M1572 designs the first bounded history-intervention layer over the M1570
source-diverse flip-anchor active set.

Decision:

```text
source_diverse_flip_anchor_history_intervention_design_admit_bounded_implementation
```

This is design only. It does not run simulator traces, history interventions,
materialize candidates, export a corpus, train, run PPO, promote, use private
holdout, change actor inputs, or claim self-identification.

## Input Artifacts

The implementation should use the M1570 artifacts:

```text
runs/m1570_targeted_third_source_flip_anchor_smoke/source_spec_rows.csv
runs/m1570_targeted_third_source_flip_anchor_smoke/flip_anchor_rows.csv
runs/m1570_targeted_third_source_flip_anchor_smoke/targeted_flip_anchor_rows.csv
runs/m1570_targeted_third_source_flip_anchor_smoke/recoverable_active_anchor_rows.csv
```

Primary target anchors:

```text
all 14 rows from flip_anchor_rows.csv
```

Primary target coverage:

```text
source families:
  t5_boundary_axis_retarget: 5
  t5_high_speed_close_obstacle: 4
  t5_near_boundary_warmup: 5

windows:
  decision_minus_24: 6
  decision_minus_16: 5
  reveal: 2
  reveal_plus_4: 1
```

Diagnostic late-reveal anchors:

```text
up to 8 strongest late_reveal_boundary rows from recoverable_active_anchor_rows.csv
```

Late-reveal anchors are diagnostic only because M1570 produced:

```text
late_reveal_boundary recoverable anchors: 17
late_reveal_boundary flip anchors: 0
```

They must be reported separately and must not be used to weaken source-diverse
flip-anchor pass/fail criteria.

## Anchor Replay Contract

M1573 should reconstruct each target anchor from:

```text
source_spec_rows.csv;
flip_anchor_rows.csv;
targeted_flip_anchor_rows.csv;
recoverable_active_anchor_rows.csv.
```

For each target anchor:

```text
1. Rebuild the M1570 CalibrationSpec and P0 env hook from the calibration row.
2. Replay the fixed public actor from reset to exactly the anchor step.
3. Capture env state, current observation, actor hidden state, hidden_by_step,
   response/action frame, baseline action, and anchor info before the anchor action.
4. Verify P0 actor contract and no privileged inputs.
5. Continue from the anchor under each intervention for 64 steps.
```

The implementation may reuse M1534/M1547 intervention mechanics where possible,
but the artifact schema must be M1570-specific and include source family,
anchor window, and flip-anchor metadata.

## Donor Pairing

For each primary target anchor, choose at least two donors when available:

```text
1. nearest same-window different-source donor;
2. nearest different-window different-source donor;
3. prefer donors with a contrasting normal outcome when distances tie;
4. never use the same calibration_id as donor;
5. include high-speed targets and donors explicitly.
```

Distance keys:

```text
abs(anchor_step_target - anchor_step_donor);
same anchor_window first;
different source_family required;
opposite or different normal outcome preferred;
source-family round-robin for ties.
```

If fewer than two donors are available for a target, keep the target but record:

```text
donor_shortage_reason
```

Late-reveal diagnostic anchors can use donors from any primary source family,
but their rows must carry:

```text
diagnostic_late_reveal: true
```

## Intervention Variants

Required variants:

```text
normal
wrong_history_donor_hidden_at_anchor
donor_response_action_stream_from_anchor
donor_response_action_plus_hidden_from_anchor
delayed_hidden_8_at_anchor
delayed_hidden_16_at_anchor
reset_hidden_once_at_anchor
reset_hidden_every_step_from_anchor
zero_current_response_from_anchor
zero_action_history_from_anchor
zero_all_response_from_anchor
```

### Normal

Continue the target environment and target hidden state without surgery.

### Wrong-History Donor Hidden

Keep target:

```text
env state;
scene/context observation fields;
current response/action observation fields;
actuator state;
previous physical commands.
```

Replace only:

```text
actor recurrent hidden state = donor hidden state at donor anchor.
```

This is the cleanest hidden-history intervention.

### Donor Response/Action Stream

Keep target env and target scene/context, but replace deployable response/action
fields with donor values.

Variants:

```text
donor_response_action_stream_from_anchor:
  donor response/action frame, target hidden.

donor_response_action_plus_hidden_from_anchor:
  donor response/action frame, donor hidden.
```

These test whether current-frame response/action fields substitute for hidden
history.

### Delayed Hidden

Use the target's own older hidden state:

```text
delayed_hidden_8_at_anchor;
delayed_hidden_16_at_anchor.
```

If the earlier hidden state is missing, record `missing_delayed_hidden` and do
not count the row as replay-ok.

### Reset / Zero Controls

Controls:

```text
reset_hidden_once_at_anchor;
reset_hidden_every_step_from_anchor;
zero_current_response_from_anchor;
zero_action_history_from_anchor;
zero_all_response_from_anchor.
```

These are not self-ID evidence by themselves. They are required to detect
current-frame substitution and to separate hidden-history dependence from
immediate observation dependence.

## Metrics

Each intervention row must report:

```text
target_anchor_id
donor_anchor_id
target_source_family
donor_source_family
target_anchor_window
donor_anchor_window
target_anchor_step
donor_anchor_step
target_normal_success
target_normal_collision
donor_normal_success
donor_normal_collision
variant
target_replay_status
donor_replay_status
first_action_steer
first_action_throttle
first_action_brake
first_action_l2_vs_normal
prefix_action_l2_vs_normal
terminal_margin
terminal_margin_gap_from_normal
success
success_drop_from_normal
collision
collision_increase_from_normal
obstacle_completed
terminal_reason
continuation_steps
target_hidden_norm
donor_hidden_norm
target_donor_hidden_l2
target_donor_response_action_l2
diagnostic_late_reveal
```

Also write grouped summaries:

```text
history_intervention_variant_summary.csv
history_intervention_source_family_summary.csv
history_intervention_window_summary.csv
history_intervention_pair_summary.csv
history_intervention_guardrail_summary.csv
summary.json
```

## Public Smoke Gates For M1573

M1573 should pass only if:

```text
target_anchor_count >= 12
target_source_family_count >= 3
target_window_count >= 3
high_speed_target_anchor_count >= 4
history_variant_count >= 3
control_variant_count >= 5
intervention_row_count >= 240
anchor_replay_failure_count <= 4
wrong_history_row_count >= 20
donor_response_action_row_count >= 40
reset_zero_control_row_count >= 80
guardrail_violation_count == 0
history_interventions_executed == true
candidate_materialized == false
training_corpus_exported == false
training_started == false
ppo_used == false
promoted == false
private_holdout_used == false
actor_input_contract_changed == false
labels_enter_actor_input == false
level3_self_id_claim_made == false
```

Evidence-quality targets:

```text
max_wrong_history_margin_gap >= 0.02
or max_donor_response_action_margin_gap >= 0.02
or history_success_drop_count >= 1

history_positive_source_family_count >= 2
or high_speed_history_positive_count >= 1

control_to_history_gap_ratio <= 6.0
or history_success_drop_count >= 1
```

Null-result classification:

```text
history_null_current_control_positive:
  history max gap < 0.02, history success drops == 0,
  but zero_current/zero_all controls are positive.

history_null_all_controls_null:
  history and controls both null.

donor_mismatch_weak:
  target_donor_hidden_l2 and response/action l2 are too small.

late_reveal_family_null:
  late_reveal diagnostics remain null while primary sources are positive.
```

## Artifact Contract

M1573 should write:

```text
runs/m1573_source_diverse_flip_anchor_history_intervention_smoke/target_anchor_rows.csv
runs/m1573_source_diverse_flip_anchor_history_intervention_smoke/donor_pair_rows.csv
runs/m1573_source_diverse_flip_anchor_history_intervention_smoke/anchor_replay_rows.csv
runs/m1573_source_diverse_flip_anchor_history_intervention_smoke/history_intervention_rows.csv
runs/m1573_source_diverse_flip_anchor_history_intervention_smoke/history_intervention_variant_summary.csv
runs/m1573_source_diverse_flip_anchor_history_intervention_smoke/history_intervention_source_family_summary.csv
runs/m1573_source_diverse_flip_anchor_history_intervention_smoke/history_intervention_window_summary.csv
runs/m1573_source_diverse_flip_anchor_history_intervention_smoke/history_intervention_guardrail_summary.csv
runs/m1573_source_diverse_flip_anchor_history_intervention_smoke/summary.json
```

Do not write:

```text
training corpus;
checkpoint;
candidate materialization artifact;
private holdout artifact.
```

## Interpretation Rules

Positive history evidence requires outcome-relevant degradation under
wrong-history or donor-plus-hidden variants, not only reset/zero-current
controls.

If zero-current or zero-all controls are strong but wrong-history variants are
null, record current-frame substitution as the likely explanation.

If high-speed is positive and late-reveal is null, record a family-specific
result instead of claiming broad terminal-family self-identification.

Even if M1573 passes evidence-quality targets, it still routes to audit before
candidate materialization or corpus export.

## Guardrails

```text
history_interventions_executed: false in M1572
candidate_materialized: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
training_corpus_exported: false
labels_enter_actor_input: false
level3_self_id_claim_made: false
```

## Next

```text
m1573-paper-route-source-diverse-flip-anchor-history-intervention-implementation
```
