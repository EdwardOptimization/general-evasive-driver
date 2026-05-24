# M522 History-Value Ablation Runner

## Purpose

M522 implements and runs the first diagnostic history-value ablation after M521.
It measures whether the existing online GRU recurrent policy shows value over a
reset-hidden diagnostic on the M520 projected mechanism surface.

This milestone does not train, run PPO, change actor inputs, update a
checkpoint, or promote a checkpoint.

## Command

```bash
PYTHONPATH=src \
python -m autodrift.history_value_ablation_runner \
  --outcomes-csv runs/m520_valid_offset_projection_outcome_gate/projected_outcomes.csv \
  --surface-name m520_valid_offset_projection \
  --min-margin-gap 0.02 \
  --run-dir runs/m522_history_value_ablation_runner
```

## Artifacts

```text
runs/m522_history_value_ablation_runner/summary.json
runs/m522_history_value_ablation_runner/history_value_rows.csv
runs/m522_history_value_ablation_runner/history_value_summary.csv
```

## Implementation

M522 adds:

```text
src/autodrift/history_value_ablation_runner.py
tests/test_history_value_ablation_runner.py
```

The first runner consumes an existing outcome table instead of rerunning
simulation. For M522 it maps:

```text
L3_online_gru                <- normal_projected
L0_reset_hidden_each_step    <- reset_projected
```

This is intentionally diagnostic:

```text
L0_reset_hidden_each_step is a reset-hidden diagnostic over the existing
recurrent actor, not a separately trained feedforward policy.

L1 and L2 matched-capacity baselines are not implemented yet.

Projected mechanism rows must not be claimed as broad natural-scenario
generalization.
```

## Result

Summary:

```text
classification:                  margin_only_history_value_signal
row_count:                       1276
history_levels:
  L0_reset_hidden_each_step
  L3_online_gru

l0_row_count:                     638
l0_candidate_count:                 8
l0_event_row_count:                 0
l0_probe_seed_count:                2
l0_config_count:                    2
l0_target_count:                    2
l0_single_seed_share:           0.625
l0_single_config_share:         0.625
l0_candidate_by_target:
  future_braking_deceleration:      4
  future_yaw_response:              4

actor_contract_changed:         false
training_or_promotion_performed: false
```

Per-target L0 diagnostic summary:

```text
future_braking_deceleration:
  rows: 161
  candidates: 4
  events: 0
  l3_success_rate: 0.086957
  l0_success_rate: 0.086957
  margin_gap_mean: 0.000682
  margin_gap_max: 0.275706
  first_action_distance_mean: 0.792640
  trajectory_distance_mean: 0.812594

future_lateral_accel_response:
  rows: 240
  candidates: 0
  events: 0
  l3_success_rate: 0.145833
  l0_success_rate: 0.145833
  margin_gap_mean: -0.000191
  margin_gap_max: 0.002029
  first_action_distance_mean: 0.752107
  trajectory_distance_mean: 0.736056

future_yaw_response:
  rows: 237
  candidates: 4
  events: 0
  l3_success_rate: 0.025316
  l0_success_rate: 0.025316
  margin_gap_mean: 0.000391
  margin_gap_max: 0.199984
  first_action_distance_mean: 0.988536
  trajectory_distance_mean: 1.004912
```

## Interpretation

M522 proves the diagnostic runner works and that L3 versus L0 can produce large
action-trajectory differences on the M520 projected surface. The margin-only
candidate rows show that recurrent history can matter locally:

```text
L0 candidate count: 8
L0 event rows:      0
```

This is not yet strong history-value proof. The signal is still margin-only,
source-narrow, and measured on a projected mechanism surface. It should be used
as infrastructure and a weak diagnostic signal, not as a paper-level claim.

The next step should generalize the runner to multiple recent surfaces and
variant naming schemes, then rerun L3-vs-L0 on both projected and natural
surfaces before any matched L0/L1/L2 training.

## Decision

```text
margin_only_history_value_signal_admit_m523_multisurface_history_value_design
```

Failure classification:

```text
none
```

Next blocker:

```text
m523-multisurface-history-value-ablation-design
```
