# M487 Critical-Window Tail-Aligned Outcome Gate

## Purpose

M487 runs tail-aligned wrong-history outcome gates on the M486 targeted critical
window pairs.

No training, PPO, actor-input change, checkpoint update, or checkpoint promotion
is performed.

## Split

M486 targeted pairs were split by `critical_config`:

```text
near_threshold:   157
late_high_energy: 155
```

Split artifacts:

```text
runs/m487_critical_window_tail_aligned_outcome_gate/targeted_pairs_near_threshold.csv
runs/m487_critical_window_tail_aligned_outcome_gate/targeted_pairs_late_high_energy.csv
```

## Commands

Both splits were run with:

```text
tail_offsets: 4, 8, 12, 16
max_continuation_steps: 80
min_margin_gap: 0.02
max_pairs_per_checkpoint_target: 0
pair_label_mode: matching
```

Near-threshold command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.tail_aligned_wrong_history_gate \
  --checkpoint-policy m399=runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt \
  --env-config configs/m484_critical_window_near_threshold_zero_relvel.json \
  --pairs-csv runs/m487_critical_window_tail_aligned_outcome_gate/targeted_pairs_near_threshold.csv \
  --tail-offsets 4,8,12,16 \
  --max-continuation-steps 80 \
  --min-margin-gap 0.02 \
  --max-pairs-per-checkpoint-target 0 \
  --pair-label-mode matching \
  --device cpu \
  --run-dir runs/m487_near_threshold_tail_aligned_gate
```

Late high-energy command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.tail_aligned_wrong_history_gate \
  --checkpoint-policy m399=runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt \
  --env-config configs/m484_critical_window_late_high_energy_zero_relvel.json \
  --pairs-csv runs/m487_critical_window_tail_aligned_outcome_gate/targeted_pairs_late_high_energy.csv \
  --tail-offsets 4,8,12,16 \
  --max-continuation-steps 80 \
  --min-margin-gap 0.02 \
  --max-pairs-per-checkpoint-target 0 \
  --pair-label-mode matching \
  --device cpu \
  --run-dir runs/m487_late_high_energy_tail_aligned_gate
```

Run dirs:

```text
runs/m487_near_threshold_tail_aligned_gate
runs/m487_late_high_energy_tail_aligned_gate
```

Combined artifacts:

```text
runs/m487_critical_window_tail_aligned_outcome_summary/combined_tail_outcomes.csv
runs/m487_critical_window_tail_aligned_outcome_summary/combined_summary.json
runs/m487_critical_window_tail_aligned_outcome_summary/variant_summary.csv
```

## Per-Config Results

```text
near_threshold:
  input pairs:                 157
  valid tail pairs:            535
  invalid tail pairs:           93
  wrong_tail_once proof rows:    2
  wrong_tail_once event rows:    0
  best offset:                  12

late_high_energy:
  input pairs:                 155
  valid tail pairs:            545
  invalid tail pairs:           75
  wrong_tail_once proof rows:    9
  wrong_tail_once event rows:    0
  best offset:                  12
```

## Combined Wrong-Tail Results

```text
input pairs:                         312
valid tail pairs:                   1080
invalid tail pairs:                  168
wrong_tail_once proof rows:           11
wrong_tail_once event rows:            0
wrong_tail_once probe seeds:           5
wrong_tail_once labels:                2
wrong_tail_once targets:               2
wrong_tail_once configs:               2
single-seed share:              0.363636
single-label share:             0.909091
tail gate pass:                    false
```

Wrong-tail proof rows by config:

```text
late_high_energy: 9
near_threshold:   2
```

Wrong-tail proof rows by offset:

```text
4:  1
8:  2
12: 4
16: 4
```

Wrong-tail proof rows by label:

```text
unavoidable:    10
drift_required:  1
```

Wrong-tail proof rows by target:

```text
future_braking_deceleration: 8
future_yaw_response:        3
```

## Controls

The same tail states are not outcome-insensitive in general:

```text
reset_tail / zero_current_tail proof rows: 333
reset_tail / zero_current_tail event rows:  41
```

By config:

```text
late_high_energy:
  reset_tail proof rows:        135
  reset_tail event rows:         14
  zero_current proof rows:      110
  zero_current event rows:       25

near_threshold:
  reset_tail proof rows:         47
  reset_tail event rows:          0
  zero_current proof rows:       41
  zero_current event rows:        2
```

## Interpretation

M487 rejects the natural wrong-tail proof claim. The critical-window configs and
targeted pairs are sensitive to response ablations, but `wrong_tail_once` remains
mostly no-effect:

```text
wrong_tail_once: 11 proof rows, 0 event rows
controls:       333 proof rows, 41 event rows
```

This says the current wrong-history selection is still not aligned with
closed-loop outcome degradation. The problem is no longer simply that the task
is too easy or that tail alignment was stale; it is likely that the wrong hidden
state perturbation is too weak, too quickly corrected, or selected by a target
score that does not predict outcome-relevant action error.

## Decision

```text
critical_window_tail_gate_reject_wrong_tail_proof_admit_m488_no_effect_audit
```

M488 should audit the M487 no-effect mechanism: compare wrong-tail action and
trajectory distances against reset/zero-current controls, inspect the 11
wrong-tail margin rows, and decide whether the next repair should target action
distance, tail offset, pair selection, or task construction.

No checkpoint is promoted.
