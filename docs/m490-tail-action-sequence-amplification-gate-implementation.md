# M490 Tail Action-Sequence Amplification Gate Implementation

## Purpose

M490 implements and runs the diagnostic gate designed in M489. It tests whether
the M487/M488 wrong-tail no-effect result is caused by fast recurrent correction
of a real wrong-belief branch.

No training, PPO, actor-input change, checkpoint update, or checkpoint promotion
is performed.

## Implementation

Added:

```text
src/autodrift/tail_action_sequence_amplification_gate.py
tests/test_tail_action_sequence_amplification_gate.py
```

The gate reuses:

```text
collect_requested_outcome_snapshots
tail_requested_snapshot_steps
PersistentVariantSpec
replay_persistent_variant
```

Variants:

```text
normal_tail
wrong_tail_once
reset_tail
zero_current_tail
wrong_tail_hidden_hold_2
wrong_tail_hidden_hold_4
wrong_tail_hidden_hold_8
wrong_tail_hidden_hold_12
```

`wrong_tail_hidden_hold_K` keeps the matched right-tail hidden state as the
actor action hidden for K consecutive control steps in the left environment. It
is diagnostic only and must not be treated as deployable self-ID proof.

## Commands

Near-threshold run:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.tail_action_sequence_amplification_gate \
  --checkpoint-policy m399=runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt \
  --env-config configs/m484_critical_window_near_threshold_zero_relvel.json \
  --pairs-csv runs/m487_critical_window_tail_aligned_outcome_gate/targeted_pairs_near_threshold.csv \
  --tail-offsets 4,8,12,16 \
  --hold-steps 2,4,8,12 \
  --max-continuation-steps 80 \
  --min-margin-gap 0.02 \
  --max-pairs-per-checkpoint-target 0 \
  --pair-label-mode matching \
  --device cpu \
  --run-dir runs/m490_near_threshold_tail_action_sequence_amplification_gate
```

Late high-energy run:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.tail_action_sequence_amplification_gate \
  --checkpoint-policy m399=runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt \
  --env-config configs/m484_critical_window_late_high_energy_zero_relvel.json \
  --pairs-csv runs/m487_critical_window_tail_aligned_outcome_gate/targeted_pairs_late_high_energy.csv \
  --tail-offsets 4,8,12,16 \
  --hold-steps 2,4,8,12 \
  --max-continuation-steps 80 \
  --min-margin-gap 0.02 \
  --max-pairs-per-checkpoint-target 0 \
  --pair-label-mode matching \
  --device cpu \
  --run-dir runs/m490_late_high_energy_tail_action_sequence_amplification_gate
```

Combined artifacts:

```text
runs/m490_tail_action_sequence_amplification_summary/combined_summary.json
runs/m490_tail_action_sequence_amplification_summary/combined_tail_amplification_outcomes.csv
runs/m490_tail_action_sequence_amplification_summary/variant_summary.csv
```

## Per-Config Results

```text
near_threshold:
  input pairs:                   157
  valid tail pairs:              535
  outcome rows:                 4280
  wrong_tail_once proof rows:      2
  wrong_tail_once event rows:      0
  hidden-hold proof rows:          7
  hidden-hold event rows:          0
  control proof rows:             88
  control event rows:              2

late_high_energy:
  input pairs:                   155
  valid tail pairs:              545
  outcome rows:                 4360
  wrong_tail_once proof rows:      9
  wrong_tail_once event rows:      0
  hidden-hold proof rows:         83
  hidden-hold event rows:          4
  control proof rows:            245
  control event rows:             39
```

## Combined Results

```text
input pairs:                         312
valid tail pairs:                   1080
outcome rows:                       8640

wrong_tail_once proof rows:           11
wrong_tail_once event rows:            0

hidden-hold proof rows:               90
hidden-hold event rows:                4
hidden-hold probe seeds:               6
hidden-hold labels:                    2
hidden-hold targets:                   2
hidden-hold configs:                   2
hidden-hold single-seed share:  0.544444
hidden-hold single-label share: 0.544444

control proof rows:                  333
control event rows:                   41
```

Hidden-hold proof rows by variant:

```text
wrong_tail_hidden_hold_12: 31
wrong_tail_hidden_hold_8:  27
wrong_tail_hidden_hold_4:  17
wrong_tail_hidden_hold_2:  15
```

Hidden-hold event rows:

```text
wrong_tail_hidden_hold_12: 3
wrong_tail_hidden_hold_8:  1
```

By event source:

```text
config:
  late_high_energy: 4

label:
  unavoidable:    3
  drift_required: 1

target:
  future_braking_deceleration: 3
  future_yaw_response:        1
```

Best single hidden-hold variant:

```text
variant:                  wrong_tail_hidden_hold_12
proof rows:               31
event rows:                3
probe seeds:               6
labels:                    2
targets:                   2
configs:                   2
single-seed share:  0.612903
single-label share: 0.516129
trajectory mean:    0.096028
max margin gap:     0.184041
```

## Interpretation

M490 confirms the quick-correction hypothesis as a diagnostic signal:

```text
natural wrong_tail_once: 11 proof rows, 0 events
hidden-hold variants:   90 proof rows, 4 events
```

Keeping the wrong hidden state alive for multiple steps can push the same tail
states across outcome boundaries. That means the M487/M488 failure was not
because the critical-window surface is completely insensitive. The natural
wrong hidden branch is corrected too quickly to create robust terminal events.

However, this is not deployable self-ID proof:

```text
hidden-hold is artificial;
event rows appear only in late_high_energy;
the best single variant has single-seed share 0.612903;
controls remain much stronger with 333 proof rows and 41 events.
```

So M490 should not promote a checkpoint and should not expand the natural proof
gate yet.

## Decision

```text
hidden_hold_confirms_quick_correction_diagnostic_admit_m491_action_replay_sufficiency_design
```

M491 should design a follow-up action-replay sufficiency diagnostic. It should
ask whether the K-step wrong-tail physical action sequence itself is enough to
degrade the left episode when the persistent wrong hidden state is not kept
alive after the forced action window.

No checkpoint is promoted.
