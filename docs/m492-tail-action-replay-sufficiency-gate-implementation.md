# M492 Tail Action-Replay Sufficiency Gate Implementation

## Purpose

M492 implements and runs the observer-hidden action-replay diagnostic designed
in M491. It asks whether the K-step wrong-tail physical action prefix is
sufficient to reproduce the M490 hidden-hold event rows.

No training, PPO, actor-input change, checkpoint update, or checkpoint promotion
is performed.

## Implementation

Added:

```text
src/autodrift/tail_action_replay_sufficiency_gate.py
tests/test_tail_action_replay_sufficiency_gate.py
```

Action replay uses this primary resume policy:

```text
observer_hidden starts from left_tail.hidden
for K forced steps:
  run actor on current observation and observer_hidden
  ignore actor action
  keep next_hidden as observer_hidden
  execute forced wrong-tail action in the left env
after K:
  resume normal actor control from observer_hidden
```

This keeps actor inputs P0-compatible and avoids resuming from the wrong hidden
state after the forced-action window.

## Commands

Near-threshold run:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.tail_action_replay_sufficiency_gate \
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
  --run-dir runs/m492_near_threshold_tail_action_replay_sufficiency_gate
```

Late high-energy run:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.tail_action_replay_sufficiency_gate \
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
  --run-dir runs/m492_late_high_energy_tail_action_replay_sufficiency_gate
```

Combined artifacts:

```text
runs/m492_tail_action_replay_sufficiency_summary/combined_summary.json
runs/m492_tail_action_replay_sufficiency_summary/combined_tail_action_replay_outcomes.csv
runs/m492_tail_action_replay_sufficiency_summary/variant_summary.csv
```

## Per-Config Results

```text
near_threshold:
  input pairs:                    157
  valid tail pairs:               535
  outcome rows:                  6420
  action-replay proof rows:         2
  action-replay event rows:         0
  hidden-hold proof rows:           7
  hidden-hold event rows:           0

late_high_energy:
  input pairs:                    155
  valid tail pairs:               545
  outcome rows:                  6540
  action-replay proof rows:        19
  action-replay event rows:         1
  hidden-hold proof rows:          83
  hidden-hold event rows:           4
```

## Combined Results

```text
input pairs:                         312
valid tail pairs:                   1080
outcome rows:                      12960

wrong_tail_once proof rows:           11
wrong_tail_once event rows:            0

hidden-hold proof rows:               90
hidden-hold event rows:                4

action-replay proof rows:             21
action-replay event rows:              1
action-replay probe seeds:             5
action-replay labels:                  1
action-replay targets:                 2
action-replay configs:                 2
single-seed share:              0.333333
single-label share:             1.000000

control proof rows:                  333
control event rows:                   41
```

Action-replay proof rows by variant:

```text
wrong_tail_action_replay_12: 11
wrong_tail_action_replay_8:   7
wrong_tail_action_replay_4:   3
wrong_tail_action_replay_2:   0
```

Action-replay events:

```text
wrong_tail_action_replay_12: 1
```

Action-replay proof rows by label:

```text
unavoidable: 21
```

Action-replay proof rows by target:

```text
future_braking_deceleration: 18
future_yaw_response:         3
```

Best action-replay variant:

```text
variant:                  wrong_tail_action_replay_12
proof rows:               11
event rows:                1
probe seeds:               5
labels:                    1
targets:                   2
configs:                   2
single-seed share:  0.363636
single-label share: 1.000000
trajectory mean:    0.051842
max margin gap:     0.187238
```

## Interpretation

M492 rejects action-sequence sufficiency on this surface:

```text
hidden-hold:   90 proof rows, 4 event rows
action replay: 21 proof rows, 1 event row
wrong once:    11 proof rows, 0 event rows
```

The wrong physical action prefix has some diagnostic effect, but it does not
reproduce the hidden-hold event signal. Action-replay proof rows are also
label-narrow: all `21` are `unavoidable`.

Therefore the M490 hidden-hold events are not explained by the first K wrong
physical actions alone. The dominant mechanism is persistent wrong hidden state
forcing, while the natural actor uses current observations to correct quickly.

## Decision

```text
action_replay_rejects_action_sequence_sufficiency_admit_m493_natural_belief_task_redesign
```

The current M486-M492 tail-intervention branch should not keep adding more
artificial forcing on the same surface. M493 should redesign the task or
pair-selection path to create a natural decision window where a belief formed
from command-response history matters before current-response correction can
wash out the effect.

No checkpoint is promoted.
