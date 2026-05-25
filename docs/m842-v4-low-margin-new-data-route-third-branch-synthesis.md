# M842 V4 Low-Margin New-Data Route Third Branch Synthesis

## Purpose

M842 synthesizes the post-M831 low-margin new-data route before any further
narrow implementation.

This is required by the workflow cadence: M841 completes the tenth
non-synthesis milestone after M831.

M842 is synthesis-only:

```text
no replay
no actor update
no M761 residual-head update
no calibrator training
no PPO
no checkpoint promotion
```

## Evidence Summary

### M832 Boundary-First Pair Mining

M832 fixed the wide-margin problem found in M828/M829:

```text
accepted_boundary_rows: 39
boundary_margin_min: 0.0000494
boundary_margin_median: 0.009952
near_boundary_pair_rows: 60
```

But hidden-only wrong-history remained weak:

```text
accepted_primary_wrong_history_rows: 0
wrong_hidden max_action: 0.00665 < 0.014
wrong_hidden max_gap: 0.0000369 << 0.01
```

Conclusion:

```text
boundary slack was fixed, but hidden-only first-step wrong-history evidence was
not found.
```

### M835 Full Response/Action Intervention

M835 swapped deployable response/action observation fields from matched wrong
history sources.

Result:

```text
response_intervention_replay_rows: 540
accepted_primary_response_history_rows: 0
accepted_component_attribution_rows: 0
accepted_mitigation_rows: 0
zero_command_component_like_rows: 0
```

Some variants moved action:

```text
wrong_response_action_hidden max_action: 0.0196
wrong_action_history_hidden max_action:  0.0172
```

but margins stayed weak:

```text
wrong_response_action_hidden max_gap: 0.000302
zero_command_obs max_gap:             0.00467
primary_margin_gap_threshold:         0.01
```

Conclusion:

```text
response/action swaps create action drift, but not outcome evidence on M832.
```

### M838 Direct First-Action Override

M838 tested whether the states were locally controllable by one direct action
override.

Result:

```text
action_effectiveness_rows: 1920
accepted_primary_action_effective_rows: 0
success_flip_rows: 0
collision_flip_rows: 0
max_abs_margin_delta: 0.0026495
```

Conclusion:

```text
M832 states are poor first-step control surfaces; a one-step action objective
would be poorly supported.
```

### M841 Short-Horizon Sequence Override

M841 tested whether sustained bounded action intent over `[2, 4, 6]` steps can
move terminal margin.

Result:

```text
sequence_effectiveness_rows: 5760
accepted_primary_sequence_effective_rows: 73
accepted_directional_degradation_rows: 65
accepted_directional_improvement_rows: 8
success_flip_rows: 59
collision_flip_rows: 59
max_abs_margin_delta: 0.0158369
```

The signal appears at longer holds:

```text
hold_steps=2: 0 accepted rows
hold_steps=4: accepted rows appear
hold_steps=6: strongest effects
```

But the result is sparse and concentrated:

```text
unique_left_source_group_count: 4 < 8
unique_left_fault_family_count: 4 < 5
max_left_source_group_dominance: 0.5616 > 0.30
```

Conclusion:

```text
sequence-level controllability exists, but current evidence is not
source-diverse enough for objective training or promotion.
```

## Supported Claims

The current branch supports:

1. Boundary-first mining can construct truly low-margin states from the M825
   route.
2. The current M568/M761 behavior does not show useful hidden-only or
   response/action wrong-history outcome sensitivity on the M832 pair set.
3. One-step direct action override is too weak on M832; the policy likely
   cancels the perturbation or terminal margin is dominated by later maneuver
   evolution.
4. Short-horizon sequence overrides can move terminal margin and cause
   success/collision flips on at least a sparse subset of M832 states.
5. Sequence-level maneuver intent is now the more promising control variable
   than single-step action drift.

## Falsified Claims

The branch falsifies or strongly weakens:

1. More hidden-only wrong-history replay on M832 will likely reveal strong
   self-ID evidence by itself.
2. Swapping current response/action observation fields for one step is enough
   to produce outcome-level self-ID evidence.
3. A one-step action-effectiveness objective on M832 is well supported.
4. M832 sequence positives are broad enough for training or promotion.
5. Direct override evidence can be interpreted as learned policy self-ID proof.

The branch does not falsify:

```text
sequence-level response-history self-ID
fresh source-diverse boundary mining
outcome-coupled sequence objectives
the long-term driver goal
```

## Failure Taxonomy Summary

### scenario_sampling_failure

Primary recurring failure. M832 created true near-boundary states, but pair and
accepted sequence evidence remain source-concentrated.

Examples:

```text
M832 near_boundary_pair_rows: 60 < 80 target
M841 accepted unique_left_source_group_count: 4 < 8
M841 max_left_source_group_dominance: 0.5616 > 0.30
```

### metric_artifact

Repeatedly observed when action movement existed but terminal outcome did not:

```text
M835 action drift without margin evidence
M838 one-step action override without margin evidence
```

### not contract_violation

Across M832-M841:

```text
no actor input contract change
no forbidden hidden/oracle actor inputs
actor and residual-head checksums preserved in no-training probes
no PPO
no checkpoint promotion
```

## Public Gate Overfit Risk

The current evidence is still public-corpus evidence, not promotion evidence.

Main risks:

```text
M832 pair set has only 60 pairs
M841 positives come from only 4 left source groups
M841 positives are dominated by hold_steps=6
M841 positives are direct interventions, not learned behavior
no private holdout was used
no multi-seed trained policy result exists
```

Therefore:

```text
do not train PPO from M841
do not promote any checkpoint
do not claim self-ID
do not tune thresholds around the M841 positives
```

## Next Branch Decision

Decision:

```text
continue
```

But continue into a narrower no-training data-quality branch:

```text
source-diverse sequence-effective corpus refresh
```

Rationale:

```text
M841 proves sequence-level controllability exists, but the source diversity is
too weak for objective design.
```

The next branch should ask:

```text
Can we mine a broader source-diverse corpus of near-boundary states where
bounded short-horizon sequence interventions change terminal margin?
```

Suggested target for the next implementation branch:

```text
accepted_primary_sequence_effective_rows >= 120
unique_left_source_group_count >= 10
unique_left_seed_count >= 4
unique_left_fault_family_count >= 5
unique_fault_family_pair_count >= 8
unique_hold_steps_count >= 2
unique_direction_family_count >= 3
max_left_source_group_dominance <= 0.30
```

If this passes, the project can design an outcome-coupled sequence objective.
If it fails, the branch should pivot to fresh action-leverage boundary mining
or a richer scenario distribution rather than PPO.

## Decision

Decision:

```text
v4_low_margin_new_data_route_continue_to_source_diverse_sequence_effective_corpus
```

Next:

```text
m843-v4-source-diverse-sequence-effective-corpus-design
```

PPO, checkpoint promotion, actor training, residual-head training, learned
gating, and outcome-coupled objective training remain blocked.
