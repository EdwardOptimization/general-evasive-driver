# M523 Multisurface History-Value Ablation Design

## Purpose

M523 designs the next history-value evidence step after M522 proves the first
runner but finds only margin-only, source-narrow L3-vs-L0 signal on the M520
projection surface.

No ablation is run in M523. No training, PPO, actor-input change, checkpoint
update, or checkpoint promotion is performed.

## Motivation

M522 answers an infrastructure question:

```text
Can the harness measure L3 recurrent policy outcomes against a reset-hidden
diagnostic from existing replay artifacts?
```

Answer: yes.

It does not yet answer the stronger research question:

```text
Does recurrent belief add source-diverse history value across natural and
projected handling-limit surfaces?
```

The current runner is also tied to M520 variant names:

```text
normal_projected
reset_projected
```

Recent natural outcome artifacts use other names:

```text
normal_tail
reset_tail
wrong_tail_once
zero_current_tail
```

The next implementation should generalize variant mapping and run the same
summary over multiple surfaces.

## M524 Implementation Target

M524 should extend `history_value_ablation_runner` to accept configurable level
variant mappings, for example:

```text
--level-variant L3_online_gru=normal_projected
--level-variant L0_reset_hidden_each_step=reset_projected

--level-variant L3_online_gru=normal_tail
--level-variant L0_reset_hidden_each_step=reset_tail
```

It should also accept multiple input tables or run once per table and write a
combined summary:

```text
M520 projected terminal-boundary:
  runs/m520_valid_offset_projection_outcome_gate/projected_outcomes.csv

M497 natural belief decision-window:
  runs/m497_natural_belief_decision_window_outcome_summary/combined_tail_outcomes.csv

M487 critical-window:
  runs/m487_critical_window_tail_aligned_outcome_summary/combined_tail_outcomes.csv
```

If a surface lacks the requested variants, the runner should mark that surface
invalid for the requested level mapping rather than silently dropping it.

## Metrics

For each surface and level:

```text
row_count
history_value_candidate_count
event_row_count
success_drop_count
collision_gap_count
obstacle_completion_drop_count
L3 and level success rates
L3 and level clearance margins
margin_gap mean/p10/p90/max
first_action_distance_to_L3
trajectory_distance_to_L3
probe_seed_count
config_count
single_seed_share
single_config_share
```

The combined summary should include:

```text
classification per surface
classification overall
candidate/event counts per surface family
projected-vs-natural provenance
diagnostic limitations
```

## Decision Rules

M524 should classify:

```text
event_history_value_signal:
  L0 or weaker history creates event rows versus L3.

margin_only_history_value_signal:
  L0 or weaker history creates margin candidates but no events.

no_diagnostic_history_value_signal:
  L0 or weaker history does not produce meaningful margin or event gaps.

invalid_history_value_ablation:
  requested level mapping cannot be evaluated.
```

Positive evidence should require source-diverse rows. A source-narrow margin
signal like M522 is useful for debugging but not enough to claim history-value
proof.

## Guardrails

Do not:

```text
train matched L0/L1/L2 actors yet;
promote a checkpoint;
add hidden dynamics or oracle labels to actor inputs;
mix projected mechanism rows with natural-scenario claims;
hide surfaces where variant mapping fails;
overclaim L1/L2 unless those levels are actually implemented.
```

If M524 still shows only source-narrow margin-only signal, the next step should
design matched-capacity baseline training or a better natural history-value
surface. It should not return to one-shot wrong-history event mining unless a
specific source of fast correction is isolated.

## Decision

```text
admit_m524_multisurface_history_value_ablation_runner
```

Next blocker:

```text
m524-multisurface-history-value-ablation-runner
```
