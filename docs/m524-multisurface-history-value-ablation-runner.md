# M524 Multisurface History-Value Ablation Runner

## Purpose

M524 upgrades the M522 diagnostic runner to support configurable level-to-variant
mappings and runs history-value diagnostics on both projected and natural recent
outcome surfaces.

This milestone does not train, run PPO, change actor inputs, update a
checkpoint, or promote a checkpoint.

## Commands

Projected M520 surface:

```bash
PYTHONPATH=src \
python -m autodrift.history_value_ablation_runner \
  --surface-outcomes m520_projected=runs/m520_valid_offset_projection_outcome_gate/projected_outcomes.csv \
  --level-variant L3_online_gru=normal_projected \
  --level-variant L0_reset_hidden_each_step=reset_projected \
  --min-margin-gap 0.02 \
  --run-dir runs/m524_projected_history_value_ablation
```

Natural M497/M487 surfaces:

```bash
PYTHONPATH=src \
python -m autodrift.history_value_ablation_runner \
  --surface-outcomes m497_natural_belief=runs/m497_natural_belief_decision_window_outcome_summary/combined_tail_outcomes.csv \
  --surface-outcomes m487_critical_window=runs/m487_critical_window_tail_aligned_outcome_summary/combined_tail_outcomes.csv \
  --level-variant L3_online_gru=normal_tail \
  --level-variant L0_reset_hidden_each_step=reset_tail \
  --min-margin-gap 0.02 \
  --run-dir runs/m524_natural_history_value_ablation
```

## Artifacts

```text
runs/m524_projected_history_value_ablation/summary.json
runs/m524_projected_history_value_ablation/history_value_rows.csv
runs/m524_projected_history_value_ablation/history_value_summary.csv
runs/m524_projected_history_value_ablation/invalid_surfaces.csv

runs/m524_natural_history_value_ablation/summary.json
runs/m524_natural_history_value_ablation/history_value_rows.csv
runs/m524_natural_history_value_ablation/history_value_summary.csv
runs/m524_natural_history_value_ablation/invalid_surfaces.csv
```

## Implementation

M524 extends:

```text
src/autodrift/history_value_ablation_runner.py
tests/test_history_value_ablation_runner.py
```

The runner now accepts:

```text
--surface-outcomes surface_name=path
--level-variant LEVEL=variant
```

It can run multiple surfaces with the same variant mapping, reports invalid
surface mappings instead of silently dropping them, and preserves
projected-vs-natural provenance in every row and summary.

## Result

Projected M520 result:

```text
classification:            margin_only_history_value_signal
surface_count:             1
invalid_surface_count:     0
row_count:                 1276
l0_row_count:              638
l0_candidate_count:        8
l0_event_row_count:        0
l0_probe_seed_count:       2
l0_config_count:           2
l0_target_count:           2
l0_single_seed_share:      0.625
l0_single_config_share:    0.625
```

Natural M497/M487 result:

```text
classification:            event_history_value_signal
surface_count:             2
invalid_surface_count:     0
row_count:                 4408
l0_row_count:              2204
l0_candidate_count:        480
l0_event_row_count:        18
l0_probe_seed_count:       12
l0_config_count:           2
l0_target_count:           3
l0_single_seed_share:      0.191667
l0_single_config_share:    0.489583
l0_candidate_by_target:
  future_braking_deceleration: 174
  future_lateral_accel_response: 20
  future_yaw_response: 286
```

Natural surface classifications:

```text
m497_natural_belief:
  classification:       event_history_value_signal
  l0_candidate_count:   298
  l0_event_row_count:   4
  l0_probe_seed_count:  6
  l0_config_count:      2
  l0_target_count:      3

m487_critical_window:
  classification:       event_history_value_signal
  l0_candidate_count:   182
  l0_event_row_count:   14
  l0_probe_seed_count:  6
  l0_config_count:      0
  l0_target_count:      3
```

Per-target natural L0 event rows:

```text
m487 future_braking_deceleration: 7
m487 future_yaw_response:         7
m497 future_yaw_response:         4
```

The event rows are obstacle-completion drops, not success drops or collision
gaps. L3 and L0 success rates are equal in the summarized target groups, but L0
can fail to complete the obstacle zone where L3 does.

## Interpretation

M524 changes the evidence level. M520/M522 projected mechanism diagnostics were
margin-only and source-narrow. On natural recent outcome surfaces, the same L3
vs L0 diagnostic produces source-diverse event-level history-value signal:

```text
480 L0 margin/event candidates
18 L0 event rows
12 probe seeds
3 targets
2 natural surface families
```

This is not a final proof that the policy has an ideal self-identification
latent. L0 is still a reset-hidden diagnostic over the same recurrent actor,
not a separately trained feedforward baseline, and the event rows are obstacle
completion drops rather than collisions or success drops. But M524 is the
strongest recent evidence that recurrent history has measurable closed-loop
value on natural surfaces.

The next step should audit the M524 event rows before training matched L0/L1/L2
baselines or claiming paper-level evidence.

## Decision

```text
event_history_value_signal_admit_m525_history_value_event_audit_design
```

Failure classification:

```text
none
```

Next blocker:

```text
m525-history-value-event-audit-design
```
