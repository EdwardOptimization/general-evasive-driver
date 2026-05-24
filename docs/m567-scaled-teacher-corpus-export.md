# M567 Scaled Teacher Corpus Export

## Purpose

M567 executes the scaled corpus-export step from the M566 design.

This milestone exports data only. It does not train or promote a checkpoint.

## Commands

Train corpus:

```text
PYTHONPATH=src python -m autodrift.l2_teacher_corpus \
  --teacher-checkpoint runs/m542_matched_l2_variance_seed3540/checkpoint.pt \
  --teacher-env-config configs/ppo_m541_matched_l2_variance_4096.json \
  --seeds 18200:18327 \
  --device cpu \
  --run-dir runs/m567_scaled_l2_teacher_corpus_train
```

Validation corpus:

```text
PYTHONPATH=src python -m autodrift.l2_teacher_corpus \
  --teacher-checkpoint runs/m542_matched_l2_variance_seed3540/checkpoint.pt \
  --teacher-env-config configs/ppo_m541_matched_l2_variance_4096.json \
  --seeds 18328:18391 \
  --device cpu \
  --run-dir runs/m567_scaled_l2_teacher_corpus_validation
```

## Artifacts

```text
runs/m567_scaled_l2_teacher_corpus_train/l2_teacher_corpus.npz
runs/m567_scaled_l2_teacher_corpus_train/summary.json
runs/m567_scaled_l2_teacher_corpus_train/episodes.csv

runs/m567_scaled_l2_teacher_corpus_validation/l2_teacher_corpus.npz
runs/m567_scaled_l2_teacher_corpus_validation/summary.json
runs/m567_scaled_l2_teacher_corpus_validation/episodes.csv
```

## Array Checks

Train corpus:

```text
episode_count = 128
transition_count = 8024
student_obs_seq       (8024, 72) float32
teacher_action_seq    (8024, 3)  float32
done_seq              (8024,)    bool
episode_start_seq     (8024,)    bool
seed_seq              (8024,)    int64
episode_id_seq        (8024,)    int64
step_seq              (8024,)    int64
teacher_obs_stack_seq absent
```

Validation corpus:

```text
episode_count = 64
transition_count = 3900
student_obs_seq       (3900, 72) float32
teacher_action_seq    (3900, 3)  float32
done_seq              (3900,)    bool
episode_start_seq     (3900,)    bool
seed_seq              (3900,)    int64
episode_id_seq        (3900,)    int64
step_seq              (3900,)    int64
teacher_obs_stack_seq absent
```

Both corpora report:

```text
student_obs_dim = 72
teacher_obs_dim = 288
teacher_history_length = 4
teacher_stack_stored = false
uses_public_frozen_source_rows = false
```

## Terminal Diagnostics

Train:

```text
episodes = 128
collisions = 37
obstacle_completed = 91
terminal_margin_mean = 1.090507
```

Validation:

```text
episodes = 64
collisions = 24
obstacle_completed = 40
terminal_margin_mean = 1.086313
```

These are teacher rollout diagnostics, not student performance.

## Decision

```text
scaled_teacher_corpus_export_pass_admit_m568_scaled_bc_training
```

M567 passes because it exports larger non-public train and validation corpora
with canonical 72-value student observations, absent L2 stack arrays, done/start
masks, terminal diagnostics, and no public frozen-source rows.

## Next

```text
M568: train the scaled L3 BC seed family.
```

M568 should train BC seeds `5660`, `5661`, and `5662` from these corpora and
should not run route-screen or PPO.
