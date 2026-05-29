# M1523 Paper-Route T5 Response Mismatch Intervention Design

## Summary

M1523 designs a stricter diagnostic after M1522 audited the timing-amplified
result as positive timing sensitivity but wrong-history near-null.

Decision:

```text
t5_response_mismatch_design_admit_bounded_implementation
```

The design keeps the deployed P0 actor contract unchanged. It uses diagnostic
observation intervention during evaluation only: keep the target scene context,
but replace parts of the response/action-history stream with donor history.

This is design only. It does not materialize candidates, export a training
corpus, train, run PPO, promote, use private holdout, change actor inputs, or
claim self-identification.

## Motivation

M1521 showed that earlier reset/zero-current interventions can reduce terminal
margin:

```text
max_margin_gap_from_normal: 0.027952724375794435
outcome_relevant_variant_count: 9
```

But hidden-only wrong-history donor injection remained near-null:

```text
max wrong-history gap magnitude: about 0.000031
wrong-history success drops: 0
```

This suggests that donor hidden alone is too weak or too similar. The next
diagnostic should perturb the stream the policy is supposed to use for
closed-loop response inference:

```text
ego response features: indices 0-8
previous physical commands: indices 9-11
scene context: indices 12-71
```

## Core Principle

Keep target scene context:

```text
road/free-space/obstacle geometry in ego frame stays from the target rollout.
```

Perturb only response/action-history stream:

```text
target observation[0:12] <- donor observation[0:12]
target observation[12:72] unchanged
```

This is not a deployed sensor design. It is a diagnostic intervention that asks:

```text
if the policy sees the same target obstacle/road context but a mismatched
response/action history, does its action or outcome change?
```

## Scope

Checkpoint:

```text
runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
```

Targets:

```text
t5_high_speed_close_obstacle
  close_wide
  low_mu_close
  late_reveal_high_speed
  drift_required_focus
```

Anchors:

```text
reveal
decision_minus_8
decision
```

The implementation may narrow to `reveal` and `decision_minus_8` if runtime or
schema complexity becomes too high. `decision` is a control anchor only.

Donor cycle:

```text
close_wide -> late_reveal_high_speed
low_mu_close -> close_wide
late_reveal_high_speed -> drift_required_focus
drift_required_focus -> low_mu_close
```

## Variants

Use these variants:

```text
normal

donor_response_current_frame_at_anchor
  At the anchor first action only, replace target observation[0:12] with donor
  observation[0:12]. After that, run normal target observations.

donor_ego_response_stream_from_anchor
  From anchor onward, replace target observation[0:9] with donor observation[0:9]
  at the corresponding relative step. Keep target previous commands and target
  scene context.

donor_action_history_stream_from_anchor
  From anchor onward, replace target observation[9:12] with donor observation
  [9:12]. Keep target ego response and target scene context.

donor_response_action_stream_from_anchor
  From anchor onward, replace target observation[0:12] with donor observation
  [0:12]. Keep target scene context.

donor_response_action_plus_hidden_from_anchor
  Inject donor hidden at anchor and replace target observation[0:12] with donor
  observation[0:12] from anchor onward. This is the strongest diagnostic and
  must be reported separately from hidden-only donor results.

zero_current_response_from_anchor
  Control copied from M1521 to preserve comparability.
```

Do not include privileged hidden parameters, labels, TTC, feasibility, path
errors, or controller modes in actor input. The observation surgery only swaps
values that are already inside the P0 frame.

## Execution Semantics

For each target/donor/anchor:

```text
1. Replay target under normal fixed policy to the anchor.
2. Replay donor under normal fixed policy and record donor observations from
   anchor through the bounded horizon.
3. Continue target simulator from the target anchor.
4. Before each actor call, construct a diagnostic observation:
   - target scene context is preserved;
   - configured response/action indices come from donor or zeros;
   - target simulator state is never mutated directly.
5. Step the target simulator with the actor action.
```

The implementation should record donor availability explicitly. If the donor
trajectory terminates early, reuse the last donor response frame and mark
`donor_exhausted_after_step`; do not silently drop rows.

## Metrics

Write one row per `(candidate, anchor, variant)`:

```text
candidate_id
retarget_mode
anchor_name
anchor_step
variant
donor_candidate_id
donor_status
target_replay_status
donor_response_l2_at_anchor
donor_response_l2_mean
donor_action_history_l2_mean
first_action_steer/throttle/brake
normal_first_action_l2
decision_action_l2
decision_state_delta_l2
terminal_reason
collision
obstacle_completed
success
terminal_margin
normal_terminal_margin
margin_gap_from_normal
success_drop_from_normal
reward_sum_after_anchor
```

Pair summaries should group by:

```text
candidate_id
retarget_mode
anchor_name
```

Anchor summaries should group by:

```text
anchor_name
```

Variant summaries should group by:

```text
variant
```

## Thresholds

Primary outcome relevance:

```text
success_drop_from_normal == true
or
margin_gap_from_normal >= 0.02
```

Secondary action/state relevance:

```text
normal_first_action_l2 >= 0.05
or
decision_state_delta_l2 >= 0.10
```

Response mismatch strength:

```text
donor_response_l2_mean > 0.05
```

If response mismatch strength is low, a null result is not informative and the
audit should route to donor selection repair rather than close the subset.

## Interpretation Rules

Allowed claims:

```text
response/action-stream mismatch changes or does not change policy behavior;
hidden-only donor injection was weaker than response-stream mismatch;
diagnostic observation surgery is or is not worth turning into stricter corpus
mining.
```

Forbidden claims:

```text
level3 self-identification;
deployable sensor/input change;
candidate materialization;
training corpus export;
policy superiority.
```

Even if response mismatch produces outcome-relevant gaps, it must be audited
before any materialization. It is still diagnostic evidence, not a deployable
intervention.

## Follow-Up Rule

If response/action mismatch produces outcome-relevant gaps:

```text
route to result audit, then decide whether to mine matched-current wrong-history
rows or tighten boundary around response-mismatch positives.
```

If only action/state divergence appears:

```text
route to terminal-boundary retarget repair before any corpus export.
```

If response/action mismatch remains null but donor_response_l2_mean is high:

```text
close this T5 subset as a weak wrong-history probe or synthesize the branch.
```

If response/action mismatch remains null and donor_response_l2_mean is low:

```text
repair donor selection before drawing a conclusion.
```

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

## Next

```text
m1524-paper-route-t5-response-mismatch-intervention-implementation
```
