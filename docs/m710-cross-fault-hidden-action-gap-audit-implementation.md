# M710 Cross-Fault Hidden-Action Gap Audit Implementation

## Purpose

M710 implements the M709 no-training hidden/action gap audit.

M708 showed that M707 cross-fault wrong histories do not produce wrong-history
action or margin gaps. M710 localizes where the signal disappears:

```text
raw hidden
next hidden
fused actor feature
actor action
closed-loop margin
```

This milestone is diagnostic-only:

```text
no actor update
no optimizer
no PPO
no checkpoint promotion
no actor-input change
```

## Implementation

M710 adds:

```text
src/autodrift/cross_fault_hidden_action_gap_audit.py
tests/test_cross_fault_hidden_action_gap_audit.py
```

The runner reuses the M707 cross-fault matching logic and replay path, then
computes per-pair variant gaps:

```text
normal_vs_wrong_history
normal_vs_reset_hidden
```

The feature audit uses the deployed actor path:

```text
model.recurrent_features_tensor(obs, hidden)
model.actor_mean(features)
```

No new actor input is added. Hidden fault labels remain pairing and logging
metadata only.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.cross_fault_hidden_action_gap_audit \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --config configs/cross_fault_hidden_condition_scenarios.json \
  --seed-start 41000 \
  --seed-count 512 \
  --device cpu \
  --run-dir runs/m710_cross_fault_hidden_action_gap_audit
```

## Artifacts

```text
runs/m710_cross_fault_hidden_action_gap_audit/summary.json
runs/m710_cross_fault_hidden_action_gap_audit/row_hidden_action_gaps.csv
runs/m710_cross_fault_hidden_action_gap_audit/variant_summary.csv
runs/m710_cross_fault_hidden_action_gap_audit/fault_family_pair_variant_summary.csv
runs/m710_cross_fault_hidden_action_gap_audit/sentinel_summary.csv
runs/m710_cross_fault_hidden_action_gap_audit/matched_cross_fault_pairs.csv
runs/m710_cross_fault_hidden_action_gap_audit/intervention_rollouts.csv
```

## Result

Summary:

```text
scenario_count:                 9728
snapshot_count:                33026
matched_pair_count:             2048
row_count:                      4096
wrong_rows:                     2048
reset_rows:                     2048
wrong_raw_positive_rows:        1653
wrong_fused_positive_rows:      1365
wrong_action_positive_rows:        0
wrong_outcome_positive_rows:       0
wrong_joint_positive_rows:         0
reset_action_positive_rows:     2014
reset_outcome_positive_rows:      15
result_class: action_washout
actor_parameters_changed: false
training_started: false
optimizer_started: false
ppo_used: false
promoted: false
```

## Variant Summary

| Variant | Rows | Raw Hidden L2 Mean | Next Hidden L2 Mean | Fused Feature L2 Mean | Action L2 Mean | Action L2 P95 | Margin Gap Mean | Margin Gap P95 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| normal_vs_wrong_history | 2048 | 0.101285 | 0.043808 | 0.015664 | 0.001587 | 0.005282 | -0.000001 | 0.000031 |
| normal_vs_reset_hidden | 2048 | 0.653912 | 0.266605 | 0.099829 | 0.020228 | 0.025853 | 0.000177 | 0.006699 |

Retention ratios:

| Variant | Next / Raw | Fused / Raw | Action / Fused |
| --- | ---: | ---: | ---: |
| normal_vs_wrong_history | 0.435647 | 0.155083 | 0.092014 |
| normal_vs_reset_hidden | 0.406729 | 0.152615 | 0.202227 |

## Interpretation

M710 rejects:

```text
cross-fault wrong histories are absent at the recurrent-state level:
  wrong_raw_positive_rows = 1653 / 2048

the GRU update fully erases wrong-history differences:
  wrong next/raw retention mean = 0.435647

the response/context fusion fully erases wrong-history differences:
  wrong_fused_positive_rows = 1365 / 2048
```

M710 supports:

```text
action_washout
```

Reason:

```text
Wrong-history signal survives into fused features, but the actor action head
compresses it below the action threshold for all 2048 pairs.
```

Concrete evidence:

```text
wrong action L2:
  mean: 0.0015866
  p95:  0.0052821
  max:  0.0132044
  threshold: 0.015

wrong margin gap:
  mean: -0.0000011
  p95:   0.0000310
  max:   0.0003494
  threshold: 0.02
```

Reset-hidden still creates action changes:

```text
reset_action_positive_rows: 2014 / 2048
reset_outcome_positive_rows: 15 / 2048
```

So the current best explanation is:

```text
the actor has recurrent/fused feature differences for cross-fault histories,
but the learned action map treats those differences as behaviorally irrelevant
under the tested current observations.
```

## Decision

M710 passes as a no-training implementation and diagnostic result:

```text
artifacts written
raw/next/fused/action/margin gaps separated
actor checksum unchanged
no training, no PPO, no promotion
```

M710 does not admit source export, actor update, PPO, or promotion:

```text
history_incompatibility_positive: false
result_class: action_washout
```

Next blocker:

```text
m711-cross-fault-hidden-action-gap-audit
```
