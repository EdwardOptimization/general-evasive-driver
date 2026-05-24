# M562 L2 Teacher Corpus Exporter

## Purpose

M562 implements the first step of the M561 distillation pivot.

The goal is to export L2 teacher actions for an L3 recurrent student without
changing the deployable actor input contract.

This milestone does not train or promote a checkpoint.

## Implementation

M562 adds:

```text
src/autodrift/l2_teacher_corpus.py
tests/test_l2_teacher_corpus.py
```

The exporter rolls out a finite-window L2 teacher and writes:

```text
student_obs_seq       shape (N, 72)
teacher_action_seq    shape (N, 3)
done_seq              shape (N,)
episode_start_seq     shape (N,)
seed_seq              shape (N,)
episode_id_seq        shape (N,)
step_seq              shape (N,)
```

The student input tensor is only the canonical current P0 frame:

```text
P0 human-view no-wheel/no-oracle 72-value frame
```

The L2 teacher uses the 4-frame stack only inside the teacher policy call. The
stack is not stored as a student input array.

## Boundary Checks

The exporter rejects:

```text
history_length < 2
privileged teacher observations
wheel teacher observations
non-72 base P0 frames
online recurrent teacher checkpoints
```

This keeps the M562 corpus compatible with the later L3 online-GRU student.

## Smoke Export

Command:

```text
PYTHONPATH=src python -m autodrift.l2_teacher_corpus \
  --teacher-checkpoint runs/m542_matched_l2_variance_seed3540/checkpoint.pt \
  --teacher-env-config configs/ppo_m541_matched_l2_variance_4096.json \
  --seeds 18000:18001 \
  --device cpu \
  --run-dir runs/m562_l2_teacher_corpus_exporter_smoke
```

Artifacts:

```text
runs/m562_l2_teacher_corpus_exporter_smoke/l2_teacher_corpus.npz
runs/m562_l2_teacher_corpus_exporter_smoke/summary.json
runs/m562_l2_teacher_corpus_exporter_smoke/episodes.csv
```

Summary:

```text
episode_count = 2
transition_count = 116
student_obs_dim = 72
teacher_obs_dim = 288
teacher_history_length = 4
teacher_action_dim = 3
teacher_stack_stored = false
uses_public_frozen_source_rows = false
```

Stored NPZ arrays:

```text
student_obs_seq       (116, 72) float32
teacher_action_seq    (116, 3)  float32
done_seq              (116,)    bool
episode_start_seq     (116,)    bool
seed_seq              (116,)    int64
episode_id_seq        (116,)    int64
step_seq              (116,)    int64
```

`teacher_obs_stack_seq` is absent.

Episode diagnostics:

| seed | steps | collision | completed | margin | label | initial bucket | final bucket |
| --- | ---: | --- | --- | ---: | --- | --- | --- |
| 18000 | 45 | true | false | -0.032619 | drift_required | medium | low |
| 18001 | 71 | false | true | 1.382851 | unavoidable | low | high |

These are smoke diagnostics only. They are not a performance claim.

## Tests

Focused tests:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_l2_teacher_corpus.py
```

Result:

```text
4 passed
```

The tests verify:

```text
current frame extraction takes the first 72-value frame from the L2 stack
noncanonical student frame dimensions are rejected
seed ranges parse deterministically
exported student arrays do not contain the L2 stack
```

## Decision

```text
l2_teacher_corpus_exporter_pass_admit_m563_l3_bc_optimizer
```

M562 passes because it implements and validates a corpus exporter that produces
L2 teacher targets for canonical 72-value L3 student observations without
public frozen-source rows, student training, checkpoint promotion, or L2 stack
leakage.

## Next

```text
M563: implement offline L3 behavior-cloning optimizer.
```

M563 should train only on M562-style corpora and should preserve checkpoint
metadata declaring `P0_human_view_no_wheel_no_oracle` plus `L3_online_gru`.
