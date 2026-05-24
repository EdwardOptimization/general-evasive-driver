# M526 History-Value Event Audit

## Purpose

M526 audits the natural-surface event rows found by M524 before treating them as
strong recurrent-history evidence.

This milestone does not train, run PPO, change actor inputs, update a
checkpoint, or promote a checkpoint.

## Command

```bash
PYTHONPATH=src \
python -m autodrift.history_value_event_audit \
  --history-value-rows-csv runs/m524_natural_history_value_ablation/history_value_rows.csv \
  --run-dir runs/m526_history_value_event_audit
```

## Artifacts

```text
runs/m526_history_value_event_audit/summary.json
runs/m526_history_value_event_audit/event_rows.csv
runs/m526_history_value_event_audit/event_source_summary.csv
runs/m526_history_value_event_audit/event_duplicate_summary.csv
runs/m526_history_value_event_audit/event_margin_action_summary.csv
```

## Implementation

M526 adds:

```text
src/autodrift/history_value_event_audit.py
tests/test_history_value_event_audit.py
```

The audit selects L0 rows where any event predicate is true:

```text
success_drop_vs_l3
collision_gap_vs_l3
obstacle_completion_drop_vs_l3
```

It then summarizes event type, source diversity, duplicate rates, margin/action
differences, projected-row contamination, and an audit classification.

## Result

Summary:

```text
classification:                         source_diverse_history_value_events
event_row_count:                        18
event_surface_count:                     2
event_probe_seed_count:                  5
event_target_count:                      2
event_tail_offset_count:                 5

success_drop_event_count:                0
collision_gap_event_count:               0
obstacle_completion_drop_event_count:   18
projected_event_row_count:               0

single_seed_share:                    0.333333
single_surface_share:                 0.777778
single_target_share:                  0.611111

events_by_surface:
  m487_critical_window:                 14
  m497_natural_belief:                   4

events_by_target:
  future_braking_deceleration:           7
  future_yaw_response:                  11

actor_contract_changed:              false
training_or_promotion_performed:     false
```

Duplicate audit:

```text
full_event:
  unique_key_count:       18
  duplicate_row_count:     0
  duplicate_share:       0.0
  max_key_count:           1

left_state:
  unique_key_count:        9
  duplicate_row_count:     9
  duplicate_share:       0.5
  max_key_count:           4

left_target:
  unique_key_count:       10
  duplicate_row_count:     8
  duplicate_share:       0.444444
  max_key_count:           4

audit_source:
  unique_key_count:       11
  duplicate_row_count:     7
  duplicate_share:       0.388889
  max_key_count:           4
```

Margin/action audit:

```text
m487 future_braking_deceleration:
  events: 7
  margin_gap_mean: -0.048738
  first_action_distance_mean: 0.799857
  trajectory_distance_mean: 0.961851

m487 future_yaw_response:
  events: 7
  margin_gap_mean: -0.005550
  first_action_distance_mean: 0.965085
  trajectory_distance_mean: 1.015701

m497 future_yaw_response:
  events: 4
  margin_gap_mean: 0.039562
  first_action_distance_mean: 0.921518
  trajectory_distance_mean: 1.078726
```

## Interpretation

M526 supports the M524 natural history-value finding:

```text
event rows survive full-key deduplication;
events span 2 natural surfaces, 5 probe seeds, 2 targets, and 5 tail offsets;
projected rows are not part of the event claim;
all events are explicitly obstacle-completion drops.
```

This is real diagnostic evidence that the L3 recurrent rollout can complete
obstacle-zone behavior that the reset-hidden L0 diagnostic loses.

Residual risks remain:

```text
single_surface_share is 0.777778, dominated by M487;
left-state duplicate share is 0.5 because multiple right histories can map to
the same left state;
event semantics are obstacle-completion drops, not collisions or success drops;
L0 is still a reset-hidden diagnostic over the same recurrent actor, not a
separately trained feedforward policy.
```

The next step should design matched L0/L1/L2 baseline training or a finite-window
diagnostic so this history-value result can be separated from the reset-hidden
intervention artifact.

## Decision

```text
source_diverse_history_value_events_admit_m527_matched_history_baseline_design
```

Failure classification:

```text
none
```

Next blocker:

```text
m527-matched-history-baseline-design
```
