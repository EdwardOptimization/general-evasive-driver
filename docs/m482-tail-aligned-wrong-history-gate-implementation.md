# M482 Tail-Aligned Wrong-History Gate Implementation

## Purpose

M482 implements the tail-aligned one-shot wrong-history gate designed in M481.
The goal is to test whether M480's late-one-shot signal was weakened because it
injected a stale right hidden state at a later left physical state.

No training, PPO, actor-input change, checkpoint update, or checkpoint promotion
is performed.

## Implementation

New module:

```text
src/autodrift/tail_aligned_wrong_history_gate.py
```

Focused tests:

```text
tests/test_tail_aligned_wrong_history_gate.py
```

For each source pair and tail offset `S`, the gate collects:

```text
left_tail_snapshot  = left_seed at left_step + S
right_tail_snapshot = right_seed at right_step + S
```

It then replays the left tail snapshot with:

```text
normal_tail
wrong_tail_once
reset_tail
zero_current_tail
```

The `wrong_tail_once` variant uses the aligned right tail hidden state for only
the first action and then lets recurrent dynamics update normally. It does not
clamp hidden state.

## Smoke Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.tail_aligned_wrong_history_gate \
  --checkpoint-policy m399=runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt \
  --env-config configs/m457_history_necessity_late_reveal_zero_relvel.json \
  --pairs-csv runs/m474_combined_fresh_anchor_adversarial_search/adversarial_pairs.csv \
  --tail-offsets 4,8,12,16 \
  --max-continuation-steps 80 \
  --min-margin-gap 0.02 \
  --max-pairs-per-checkpoint-target 160 \
  --pair-label-mode matching \
  --device cpu \
  --run-dir runs/m482_tail_aligned_wrong_history_gate
```

Artifacts:

```text
runs/m482_tail_aligned_wrong_history_gate/summary.json
runs/m482_tail_aligned_wrong_history_gate/tail_outcomes.csv
runs/m482_tail_aligned_wrong_history_gate/tail_invalid_pairs.csv
runs/m482_tail_aligned_wrong_history_gate/tail_variant_summary.csv
```

## Results

```text
input pairs:              197
valid tail pairs:         611
invalid tail pairs:       177
outcome rows:            2444
summary rows:              48
tail offsets:       4, 8, 12, 16
```

Best single offset:

```text
best_tail_offset:                         4
best_tail_proof_candidate_count:          4
best_tail_event_rows:                     0
best_tail_probe_seed_count:               2
best_tail_label_count:                    1
best_tail_target_count:                   2
best_tail_single_seed_share:           0.75
best_tail_single_label_share:          1.00
```

Across all tail offsets:

```text
wrong_tail_once_total_proof_candidate_count: 14
wrong_tail_once_total_event_rows:             3
```

Tail one-shot proof-style rows by offset:

```text
offset 4:   4 proof rows, 0 event rows, 2 seeds, 1 label, 2 targets
offset 8:   3 proof rows, 1 event row,  3 seeds, 1 label, 2 targets
offset 12:  4 proof rows, 1 event row,  3 seeds, 1 label, 2 targets
offset 16:  3 proof rows, 1 event row,  2 seeds, 1 label, 1 target
```

Proof rows by seed:

```text
10800: 5
10500: 5
11000: 4
```

Proof rows by label:

```text
unavoidable: 14
```

Proof rows by target:

```text
future_yaw_response:           9
future_lateral_accel_response: 5
```

The event rows are all the same physical pair repeated at offsets `8`, `12`,
and `16`:

```text
pair_id: 150
probe_seed: 11000
label: unavoidable
target: future_yaw_response
event: collision / success drop / obstacle completion drop
```

## Interpretation

Tail alignment is a useful diagnostic improvement over M480:

```text
M480 late one-shot event rows: 0
M482 tail-aligned event rows:  3
```

But M482 still fails the natural wrong-history proof gate. The event evidence is
source-narrow and comes from one physical pair. All proof rows are
`unavoidable`, so this does not yet prove a general recurrent self-ID mechanism
across the intended AEB-infeasible / drift-required family.

The result is best classified as:

```text
tail_aligned_event_signal_source_narrow
```

It shows that stale hidden state was part of the M480 weakness, but the current
task/pair surface still gives the actor enough recovery or correction capacity
on most sources.

## Decision

```text
tail_aligned_event_signal_source_narrow_admit_m483_critical_window_config_design
```

M483 should design a critical-window task/config path that reduces recovery time
and creates source-diverse tail-aligned event opportunities, without training or
loosening the source-diversity gates.

No checkpoint is promoted.
