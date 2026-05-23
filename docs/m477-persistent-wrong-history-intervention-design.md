# M477 Persistent Wrong-History Intervention Design

## Purpose

M477 designs the next diagnostic after M476 found that one-shot wrong matched
history changes first actions but does not create persistent trajectory or
terminal-margin degradation.

No training, PPO, actor-input change, proof expansion, or checkpoint promotion
is performed.

## M476 Mechanism To Test

M476 classified the blocker as:

```text
wrong_history_action_and_trajectory_perturbations_are_too_weak_or_too_quickly_corrected_relative_to_reset_zero_current
```

Key numbers:

```text
variant                 action_mean  traj_mean  success_drop  outcome_critical
wrong_matched_history     0.053586   0.045794             0                 0
reset_hidden              0.620908   0.883482            10                46
zero_current_response     0.122251   0.395153            10                36
```

The current wrong-history test injects the wrong hidden state once at the
snapshot step. After that, the recurrent state is updated from the left
episode's actual observations. M476 suggests that this one-shot intervention is
quickly corrected by current feedback.

## Design Principle

The next experiment must be explicitly diagnostic:

- It may force a wrong hidden state for analysis.
- It must not change the deployable actor input contract.
- It must not be counted as deployable self-ID proof by itself.
- It should answer whether wrong belief can become outcome-critical when it is
  active during the emergency decision window.

This is analogous to a causal intervention on the recurrent belief state, not a
new policy or controller.

## M478 Tool Design

Implement a new module:

```text
autodrift.persistent_wrong_history_intervention_gate
```

Inputs:

```text
--checkpoint-policy
--env-config
--pairs-csv
--delay-steps
--max-continuation-steps
--min-margin-gap
--max-pairs-per-checkpoint-target
--pair-label-mode
--device
--run-dir
```

Initial pair source:

```text
runs/m474_combined_fresh_anchor_adversarial_search/adversarial_pairs.csv
```

The tool should reuse the snapshot reconstruction and rollout logic from
`matched_history_outcome_gate`, but add variants that control when and how long
the wrong hidden state is active.

## Intervention Variants

Baseline variants:

```text
normal
wrong_once
reset_hidden
zero_current_response
```

Persistent wrong-hidden variants:

```text
wrong_hold_4
wrong_hold_8
wrong_hold_16
```

For `wrong_hold_K`, during continuation step `i`:

```text
if i < K:
    action_hidden = right.hidden
    next_hidden_after_action = right.hidden
else:
    action_hidden = recurrent hidden from the left rollout
    next_hidden_after_action = model update
```

This tests a hard clamp: what happens if the wrong belief remains active for
the first K emergency-control steps?

Later wrong-hidden variants:

```text
wrong_late_4_hold_4
wrong_late_8_hold_4
wrong_late_4_hold_8
```

For `wrong_late_S_hold_K`, run normal for `S` continuation steps, then hold the
wrong hidden state for the next `K` steps:

```text
if S <= i < S + K:
    action_hidden = right.hidden
    next_hidden_after_action = right.hidden
else:
    use normal recurrent hidden update
```

This tests whether the current one-shot injection is too early relative to the
critical maneuver window.

Optional softer variant if implementation is cheap:

```text
wrong_reseed_4
```

For reseed, use `right.hidden` as `action_hidden` for K steps but allow
`next_hidden` to update from the left observation. This separates "wrong action
selection" from "persistent hidden-state clamping".

## Metrics

For every pair and variant, write one row with the same outcome columns used by
`matched_history_outcome_gate`, plus:

```text
variant_family
injection_start_step
hold_steps
clamp_hidden
normal_margin
variant_margin
margin_gap
success_drop
collision_gap
obstacle_completion_drop
first_action_distance
action_trajectory_distance_mean
action_trajectory_distance_max
```

Then run a selector equivalent to the M475 near-boundary proof selector over
the persistent variants.

## Diagnostic Pass Criteria

M478 is not a deployable proof gate. It is a mechanism test.

Diagnostic pass:

```text
at least one persistent/later wrong-hidden variant has:
  proof_candidate_count >= 16
  proof_success_or_collision_or_completion_rows >= 4
  proof_probe_seed_count >= 6
  proof_obstacle_label_count >= 2
  proof_target_count >= 2
  proof_single_seed_share <= 0.50
  proof_single_label_share <= 0.70

and:
  wrong_once remains near M475 no-effect baseline
```

Interpretation if pass:

```text
wrong belief can be outcome-critical if it persists into the emergency window;
the current failure is likely fast correction / too-early one-shot injection.
```

Interpretation if fail:

```text
even persistent wrong hidden does not affect outcomes enough;
the task/pair surface may still be solved from current response and geometry,
so the next path should be shorter-emergency task design or stronger
outcome-sensitive pair scoring.
```

## Guardrails

M478 must not:

```text
train or update a checkpoint
promote a checkpoint
change the actor observation contract
call persistent intervention deployable behavior proof
relax the near-boundary normal-margin ceiling
count reset/zero-current degradation as wrong-history proof
```

## Decision

```text
admit_m478_persistent_wrong_history_intervention_implementation
```

No checkpoint is promoted.
