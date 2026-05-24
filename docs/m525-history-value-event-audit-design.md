# M525 History-Value Event Audit Design

## Purpose

M525 designs an audit for the M524 natural-surface event rows before treating
them as strong recurrent-history evidence.

No audit is run in M525. No training, PPO, actor-input change, checkpoint
update, or checkpoint promotion is performed.

## Motivation

M524 finds a meaningful diagnostic result:

```text
natural surfaces:
  l0_candidate_count: 480
  l0_event_row_count: 18
  probe_seed_count: 12
  target_count: 3
```

But all event rows are obstacle-completion drops:

```text
success_drop_count: 0
collision_gap_count: 0
obstacle_completion_drop_count: 18
```

This is still useful, because obstacle completion is part of the emergency
avoidance task. But before using it as strong self-identification evidence, the
workflow should audit whether these rows are:

```text
real closed-loop behavior differences;
source-diverse enough after deduplication;
not a bookkeeping artifact of tail replay;
not dominated by one seed, offset, or target;
not simply duplicated across surfaces.
```

## M526 Audit Target

M526 should implement or run an event-row audit over:

```text
runs/m524_natural_history_value_ablation/history_value_rows.csv
runs/m524_natural_history_value_ablation/history_value_summary.csv
```

It should export:

```text
event_rows.csv
event_source_summary.csv
event_duplicate_summary.csv
event_margin_action_summary.csv
summary.json
```

Required checks:

```text
event row count by surface, target, seed, tail_offset
unique left/right seed-step keys
duplicate rate under source keys
L3 vs L0 terminal reason and obstacle_completed fields
L3 vs L0 clearance margin deltas
first action and trajectory distance distributions
whether events survive source-level deduplication
whether projected rows are excluded from the natural event claim
```

## Decision Rules

M526 should classify:

```text
source_diverse_history_value_events:
  event rows survive deduplication and span multiple surfaces/seeds/targets.

source_narrow_history_value_events:
  events are real but dominated by one source or duplicated key.

metric_artifact_history_value_events:
  events come from terminal bookkeeping or inconsistent replay metadata.

invalid_history_value_event_audit:
  required fields are missing or the audit cannot reconstruct the comparison.
```

If M526 passes `source_diverse_history_value_events`, the next branch can design
matched L0/L1/L2 baseline training or a stronger L2 finite-window diagnostic.
If it is source-narrow or metric-artifact, fix the surface before training.

## Guardrails

Do not:

```text
train matched baselines before auditing the event rows;
promote a checkpoint;
add privileged actor inputs;
mix projected mechanism rows into the natural event claim;
hide duplicate or source-dominance findings;
call obstacle-completion events collision/success events.
```

## Decision

```text
admit_m526_history_value_event_audit
```

Next blocker:

```text
m526-history-value-event-audit
```
