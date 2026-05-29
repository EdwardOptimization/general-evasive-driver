# M1516 Paper-Route Decisive History T5 Intervention Design

## Summary

M1516 designs a bounded measured-intervention probe for the M1515-admitted
`t5_high_speed_close_obstacle` subset.

Decision:

```text
t5_intervention_design_admit_bounded_implementation
```

This milestone is design only. It does not run intervention continuations,
materialize candidates, export a training corpus, run replay gates, run PPO,
train, promote, use private holdout, change actor inputs, or claim level3
self-identification.

## Eligible Rows

Only this source family is eligible:

```text
t5_high_speed_close_obstacle
```

Eligible retarget rows from M1514:

```text
candidate_id                                           mode                    min_margin  label        decision_ok
t5_high_speed_close_obstacle-000-close_wide            close_wide                 0.513    unavoidable true
t5_high_speed_close_obstacle-000-low_mu_close           low_mu_close               1.347    unavoidable true
t5_high_speed_close_obstacle-000-late_reveal_high_speed late_reveal_high_speed     0.234    unavoidable true
t5_high_speed_close_obstacle-000-drift_required_focus   drift_required_focus       0.567    unavoidable true
```

Excluded rows:

```text
T4 source families:
  still high-margin and aeb_feasible.

t5_near_boundary_warmup:
  still high-margin and aeb_feasible.

t5_boundary_axis_retarget:
  one near-boundary row collided before decision; other rows remain high-margin.
```

## Probe Question

The probe should answer only:

```text
Do bounded post-decision interventions change closed-loop terminal margin or
success for the eligible T5 high-speed rows?
```

It should not answer yet:

```text
Does the policy prove level3 self-identification?
Can a candidate be materialized?
Is a checkpoint promotable?
```

## Deterministic Replay Boundary

M1517 should avoid direct environment state mutation.

For each target row and each intervention variant:

```text
1. rebuild the deterministic retarget spec;
2. reset the env with the recorded seed;
3. run the fixed checkpoint policy normally until the target decision step;
4. store prefix observations, actions, hidden states, margins, and info fields;
5. apply the intervention only at or after the decision step;
6. continue for a bounded horizon or until termination/truncation.
```

This makes every variant start from the same deterministic target env state.
Only policy-side hidden state or observation transformation changes.

## Intervention Variants

Required initial variants:

```text
normal:
  continue from the target decision step with the original policy hidden.

reset_hidden_once:
  set recurrent hidden to None at the decision step, then continue normally.

reset_hidden_every_step:
  reset hidden before every continuation action.

zero_current_response:
  zero response/action-history indices in the current 72-value observation
  before each continuation action.

zero_action_history:
  zero previous-command indices 9..11 before each continuation action.

delayed_hidden_8:
  replace decision hidden with the target hidden from 8 steps earlier, then
  continue normally.

wrong_history_donor_hidden:
  replace target decision hidden with a donor hidden from another eligible
  high-speed retarget row, then continue normally.
```

The `wrong_history_donor_hidden` variant is diagnostic only. It is not a
same-current / same-recent / different-older T4 proof because the donor row is
not guaranteed to be matched in current scene state. It can still reveal
whether using a wrong recurrent state changes the post-decision maneuver.

## Donor Map

Use a deterministic mode-cycle donor map:

```text
target close_wide            <- donor late_reveal_high_speed
target low_mu_close          <- donor close_wide
target late_reveal_high_speed <- donor drift_required_focus
target drift_required_focus  <- donor low_mu_close
```

If a donor replay fails before its decision step, mark the wrong-history row as
`donor_failed` and continue with the other intervention variants.

## Horizon And Stops

Use a bounded continuation horizon:

```text
continuation_steps: 64
stop on terminated or truncated
stop on obstacle_completed or collision if env terminates/truncates
do not exceed env max_steps
```

For M1517, one seed and the four eligible rows are enough. The goal is to
validate intervention plumbing and identify outcome-relevant variants, not to
claim statistical significance.

## Metrics

Every target/variant row should record:

```text
candidate_id
retarget_mode
variant
seed
reveal_step
decision_step
donor_candidate_id
donor_status
decision_margin
decision_hidden_norm
intervention_hidden_norm
first_action_steer
first_action_throttle
first_action_brake
normal_first_action_l2
terminal_step
terminal_reason
collision
obstacle_completed
terminal_margin
min_continuation_margin
normal_terminal_margin
margin_gap_from_normal
success_drop_from_normal
reached_decision
reached_post_decision
```

Success should be derived consistently for the audit:

```text
success = obstacle_completed and not collision and terminal_margin > 0
```

The implementation should save raw rows even when success is false.

## Artifact Contract

M1517 should write:

```text
runs/m1517_decisive_history_t5_intervention_smoke/intervention_rows.csv
runs/m1517_decisive_history_t5_intervention_smoke/intervention_pair_summary.csv
runs/m1517_decisive_history_t5_intervention_smoke/intervention_guardrail_summary.csv
runs/m1517_decisive_history_t5_intervention_smoke/summary.json
```

Summary fields:

```text
result_class: decisive_history_t5_intervention_smoke
eligible_target_count: 4
variant_count
intervention_row_count
normal_row_count
ablation_row_count
wrong_history_row_count
target_replay_failure_count
donor_replay_failure_count
outcome_relevant_variant_count
max_margin_gap_from_normal
success_drop_count
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

## Acceptance Criteria For M1517

M1517 should pass as infrastructure if:

```text
the implementation has focused tests;
all four eligible targets are attempted;
normal replay reaches decision for every attempted target or failure is explicit;
all required intervention variants are attempted when prerequisites exist;
artifacts are written;
guardrail_violation_count == 0;
candidate_materialized == false;
training/replay/PPO/promotion/private holdout remain false.
```

M1517 does not need positive margin gaps to pass. The next audit should decide
whether gaps are meaningful, null, or too noisy.

## Claim Discipline

Allowed claims after M1517 implementation:

```text
measured intervention plumbing works or fails;
specific intervention variants do or do not change terminal margin on this
public T5 subset;
candidate materialization remains blocked until an audit.
```

Forbidden claims:

```text
level3 self-identification;
source-diverse history necessity;
checkpoint promotion;
policy superiority;
training corpus validity.
```

## Next Milestone

Next:

```text
m1517-paper-route-decisive-history-t5-intervention-implementation
```

M1517 should implement and run the bounded T5 intervention smoke. M1518 should
then audit the measured intervention rows before any candidate materialization.
