# M489 Tail Action-Sequence Amplification Design

## Purpose

M489 designs the next no-training diagnostic after M488. The goal is to
distinguish two explanations for the M487/M488 wrong-tail no-effect result:

```text
A. the policy starts from a wrong belief but corrects it quickly from current
   response observations;
B. the selected M486/M487 pairs are not outcome-sensitive even if the policy is
   forced to execute a wrong short-horizon maneuver.
```

No training, PPO, actor-input change, checkpoint update, proof expansion, or
checkpoint promotion is performed.

## Important Clarification

M487 `wrong_tail_once` is not an open-loop one-action replay. In the existing
`replay_outcome_variant` path, the actor starts the continuation with the
tail-aligned right hidden state, then updates hidden normally using the actual
left-environment observations and actions.

So M488's no-effect result means:

```text
wrong initial hidden state does change actions;
but the closed-loop recurrent policy corrects quickly enough that terminal
outcomes usually do not change.
```

This is stronger than "only the first action was wrong."

## Diagnostic Question

M490 should answer:

```text
If wrong-tail behavior is kept alive for K steps, does the left episode degrade?
```

Interpretation:

```text
If K-step wrong-tail forcing creates event rows:
  the M487 blocker is fast correction of a real wrong-belief branch.

If K-step wrong-tail forcing still creates no event rows:
  the M486/M487 pair surface is not outcome-sensitive enough, and mining or
  task construction must change.
```

## Variants

M490 should keep M487 controls and add short-horizon amplified variants.

Baseline/control variants:

```text
normal_tail
wrong_tail_once
reset_tail
zero_current_tail
```

Amplified diagnostic variants:

```text
wrong_tail_hidden_hold_2
wrong_tail_hidden_hold_4
wrong_tail_hidden_hold_8
wrong_tail_hidden_hold_12
```

`wrong_tail_hidden_hold_K` means:

```text
at the left tail state, use the matched right-tail hidden state as the actor
action hidden for K consecutive control steps, while the environment remains the
left environment and observations remain P0 human-view observations.
```

This is diagnostic only. It should not be described as deployable self-ID proof,
because the intervention manually keeps a wrong belief alive.

Optional second-stage diagnostic:

```text
wrong_tail_action_replay_K
```

This variant would first generate the K-step wrong-tail action sequence, then
replay those physical commands into a fresh copy of the left-tail environment.
It separates "the wrong actions themselves cross the boundary" from "the hidden
state after the wrong branch matters." This is useful, but M490 can start with
hidden-hold variants if action replay would require larger refactoring.

## Implementation Path

M490 should reuse existing infrastructure instead of inventing a new rollout
stack:

```text
collect_requested_outcome_snapshots
tail_requested_snapshot_steps
replay_persistent_variant
PersistentVariantSpec
summarize_tail_outcomes
```

The likely implementation is a new module:

```text
src/autodrift/tail_action_sequence_amplification_gate.py
```

It should:

```text
1. load M486/M487 targeted pairs split by critical_config;
2. collect left_step + S and right_step + S snapshots for S in {4, 8, 12, 16};
3. replay normal_tail, wrong_tail_once, reset_tail, zero_current_tail;
4. replay wrong_tail_hidden_hold_K for K in {2, 4, 8, 12};
5. write per-row outcomes and variant summaries;
6. keep proof/event accounting separate for natural and diagnostic variants.
```

For hidden-hold variants, use `PersistentVariantSpec` with:

```text
family: wrong_tail_hidden_hold
injection_start_step: 0
hold_steps: K
clamp_hidden: true
wrong_hidden: right_tail_hidden
```

## Run Plan

Use the same critical-window splits as M487:

```text
runs/m487_critical_window_tail_aligned_outcome_gate/targeted_pairs_near_threshold.csv
runs/m487_critical_window_tail_aligned_outcome_gate/targeted_pairs_late_high_energy.csv
```

Run the diagnostic separately for:

```text
configs/m484_critical_window_near_threshold_zero_relvel.json
configs/m484_critical_window_late_high_energy_zero_relvel.json
```

Then combine summaries into:

```text
runs/m490_tail_action_sequence_amplification_summary/combined_summary.json
runs/m490_tail_action_sequence_amplification_summary/combined_tail_outcomes.csv
runs/m490_tail_action_sequence_amplification_summary/variant_summary.csv
```

## Pass/Fail Criteria

M490 should not promote a checkpoint. It only decides the next proof path.

Diagnostic pass for quick-correction hypothesis:

```text
wrong_tail_hidden_hold_K event rows >= 4 for at least one K
wrong_tail_hidden_hold_K proof rows >= 16 for at least one K
probe_seed_count >= 4
obstacle_label_count >= 2
target_count >= 2
single_seed_share <= 0.60
single_label_share <= 0.85
```

The thresholds are looser than promotion proof because hidden-hold is diagnostic
and artificial.

Diagnostic rejection:

```text
all wrong_tail_hidden_hold_K variants have 0 event rows or remain source-narrow;
reset_tail and zero_current_tail still show many event rows;
high action/trajectory rows still do not cross terminal boundaries.
```

If hidden-hold succeeds, the next design should turn the signal into a less
artificial proof path, probably by mining for naturally persistent wrong-belief
rows or using a training-time objective that preserves wrong-history branch
separation.

If hidden-hold fails, the next design should stop tuning wrong-history
intervention timing and instead rebuild the task/pair selector around terminal
outcome sensitivity.

## Forbidden Interpretations

Do not claim:

```text
hidden-hold proof is deployable self-ID proof;
reset/zero-current rows are wrong-history rows;
forced action replay proves the actor naturally depends on history;
a single source pair or single label is enough for proof expansion.
```

The result is a mechanism diagnostic, not a driver promotion.

## Decision

```text
admit_m490_tail_action_sequence_amplification_gate_implementation
```

M490 should implement and run the diagnostic gate, then decide whether the
current blocker is fast correction of a real wrong-belief branch or a
non-outcome-sensitive pair/task surface.
