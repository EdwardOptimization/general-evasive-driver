# M1519 Paper-Route Decisive History T5 Timing-Amplified Intervention Design

## Summary

M1519 designs the next bounded T5 intervention smoke after M1518 audited the
decision-step intervention as null/weak.

Decision:

```text
t5_timing_amplified_intervention_design_admit_bounded_implementation
```

The design keeps the same public checkpoint and same four admitted
`t5_high_speed_close_obstacle` retarget rows, but moves the intervention start
earlier than the decision step. The goal is to test whether M1517 was null
because the actor had already driven the vehicle into a viable physical state
before the intervention began.

This is design only. It does not materialize candidates, export a training
corpus, train, run PPO, promote, use private holdout, change actor inputs, or
claim level3 self-identification. Because this branch has reached the workflow
synthesis cadence, the next milestone must synthesize M1510-M1519 before any
timing-amplified implementation continues.

## Motivation

M1517 produced complete intervention artifacts but no outcome-relevant effect:

```text
target/donor replay failure count: 0/0
max margin gap from normal: 0.016497911642290308
outcome-relevant variant count: 0
success drop count: 0
```

The variant audit showed:

```text
reset_hidden_every_step changed first actions materially but did not change
outcomes;

wrong_history_donor_hidden, delayed_hidden_8, and zero_action_history barely
changed actions or margins;

zero_current_response created small margin degradation but still no outcome
drop.
```

This suggests that decision-step intervention is either too late, too local, or
applied on rows with too much slack. The next test should let interventions
change the pre-decision physical setup, while keeping the no-training and
no-materialization guardrails.

## Scope

Eligible source family:

```text
t5_high_speed_close_obstacle
```

Eligible retarget modes:

```text
close_wide
low_mu_close
late_reveal_high_speed
drift_required_focus
```

Checkpoint:

```text
runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
```

Actor contract:

```text
P0 human-view no-wheel 72-dim frame;
history_length = 1;
action_history_mode = full;
obstacle_relative_velocity_mode = zero;
no privileged hidden parameters;
no oracle labels;
no path/reference/TTC/clearance shortcuts.
```

## Intervention Anchors

M1520 should evaluate the same target under multiple start anchors:

```text
decision
  Control anchor matching M1517. Kept only for comparability.

decision_minus_8
  Start at max(reveal_step, decision_step - 8). This tests whether an
  eight-step pre-decision window is enough for history perturbations to affect
  the physical setup.

reveal_plus_4
  Start at min(decision_step - 1, reveal_step + 4). This tests a mid-window
  intervention after the obstacle has become visible.

reveal
  Start at reveal_step. This is the strongest timing-amplified public smoke and
  lets response/history perturbations affect the entire visible-obstacle phase.
```

If runtime is higher than expected, implementation may narrow to:

```text
decision_minus_8
reveal
```

and keep `decision` as an optional control copied from M1517.

## Variants

For each `(target, anchor)` pair, run:

```text
normal
reset_hidden_once_at_anchor
reset_hidden_every_step_from_anchor
zero_current_response_from_anchor
zero_action_history_from_anchor
delayed_hidden_8_at_anchor
wrong_history_donor_hidden_at_anchor
```

The donor mapping can reuse M1517:

```text
close_wide -> late_reveal_high_speed
low_mu_close -> close_wide
late_reveal_high_speed -> drift_required_focus
drift_required_focus -> low_mu_close
```

For `wrong_history_donor_hidden_at_anchor`, replay the donor to the same named
anchor and inject the donor hidden state into the target policy at the target
anchor. If donor replay fails, record the failure explicitly; do not drop the
row.

For `delayed_hidden_8_at_anchor`, use the target hidden from `anchor_step - 8`.
If the delayed hidden does not exist, mark `missing_delayed_hidden` and keep the
row.

## Execution Semantics

M1517 intervened at decision on the already-normal physical state. M1520 should
run a two-phase deterministic policy:

```text
1. replay the normal fixed policy from reset to anchor_step;
2. at anchor_step, switch only the policy-side hidden/observation ablation;
3. continue the simulator normally until terminal or bounded step budget.
```

The simulator state should not be cloned or mutated directly. A target/variant
rollout can always be reproduced from seed plus target config, anchor, and
variant.

This creates two interpretation classes:

```text
same-current diagnostic:
  decision anchor only. This is comparable to M1517 and does not prove history
  necessity if null.

timing-amplified diverging-trajectory diagnostic:
  reveal, reveal_plus_4, decision_minus_8. These allow intervention actions to
  change the physical setup before decision. A positive result would justify
  stronger candidate mining, but still would not by itself prove same-current
  level3 self-identification.
```

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
action at anchor
normal action L2 at anchor
state delta at decision:
  delta_x_body, delta_y_body, delta_vx, delta_vy, delta_yaw_rate
first post-anchor action L2
terminal_step
terminal_reason
collision
obstacle_completed
success
terminal_margin
min_margin_after_anchor
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

Guardrails should remain explicit:

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

## Outcome-Relevance Thresholds

Use the same primary M1517 threshold:

```text
success_drop_from_normal == true
or
margin_gap_from_normal >= 0.02
```

Add a secondary divergence diagnostic for earlier anchors:

```text
decision_state_divergence_l2 >= 0.10
or
first_post_anchor_action_l2 >= 0.05
```

The secondary divergence diagnostic is not candidate evidence by itself. It only
tells us whether the intervention is physically moving the trajectory before
outcome is measured.

## Acceptance Rule

A future timing-amplified implementation should pass as infrastructure if:

```text
all four eligible targets are attempted;
all configured anchors and variants are attempted or failures are explicit;
row, pair-summary, anchor-summary, guardrail, and summary artifacts are written;
guardrail_violation_count == 0;
no candidate materialization, corpus export, training, PPO, promotion, private
holdout, or actor-input change occurs.
```

That implementation should not promote or claim self-ID regardless of result.

## Follow-Up Rule

If a future timing-amplified implementation produces outcome-relevant gaps:

```text
route to mandatory result audit before any candidate materialization.
```

If it produces state/action divergence but no outcome-relevant gaps:

```text
route to terminal-boundary retarget repair, because intervention can perturb
the policy but rows still have too much slack.
```

If it is null across action, state, and outcome:

```text
route to branch synthesis or close this T5 subset as a history-necessity probe.
```

Do not continue with another narrow timing tweak without a synthesis or retarget
decision. M1520 is the mandatory bounded-runner branch synthesis required before
implementation.

## Next

```text
m1520-paper-route-decisive-history-bounded-runner-synthesis
```
