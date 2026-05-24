# M563 L3 Behavior-Cloning Optimizer

## Purpose

M563 implements an offline behavior-cloning optimizer that transfers L2 teacher
actions into an L3 online-GRU student.

This milestone is deliberately narrow:

```text
optimize teacher-action MSE
preserve P0 72-value student inputs
preserve L3 online-GRU metadata
do not run PPO
do not promote a checkpoint
```

Closed-loop route performance is deferred to M564.

## Implementation

M563 adds:

```text
src/autodrift/l3_behavior_cloning.py
tests/test_l3_behavior_cloning.py
```

The optimizer loads M562-style corpora:

```text
student_obs_seq       (N, 72)
teacher_action_seq    (N, 3)
done_seq              (N,)
episode_start_seq     (N,)
episode_id_seq        (N,)
step_seq              (N,)
```

It rejects `teacher_obs_stack_seq` if present. Training uses
`episode_start_seq` to reset the online-GRU hidden state at episode boundaries.

The saved checkpoint metadata declares:

```text
input_contract = P0_human_view_no_wheel_no_oracle
history_baseline.level = L3_online_gru
actor_encoder = human_view_online_gru
actor_history_length = 1
env_history_length = 1
ppo_used = false
promoted = false
```

## Validation Corpus

M563 first exported an independent validation corpus from the L2 teacher:

```text
PYTHONPATH=src python -m autodrift.l2_teacher_corpus \
  --teacher-checkpoint runs/m542_matched_l2_variance_seed3540/checkpoint.pt \
  --teacher-env-config configs/ppo_m541_matched_l2_variance_4096.json \
  --seeds 18128:18129 \
  --device cpu \
  --run-dir runs/m563_l2_teacher_corpus_validation_smoke
```

Result:

```text
validation transitions = 126
student_obs_dim = 72
teacher_obs_dim = 288
teacher_stack_stored = false
```

## BC Smoke

Command:

```text
PYTHONPATH=src python -m autodrift.l3_behavior_cloning \
  --train-corpus runs/m562_l2_teacher_corpus_exporter_smoke/l2_teacher_corpus.npz \
  --val-corpus runs/m563_l2_teacher_corpus_validation_smoke/l2_teacher_corpus.npz \
  --student-env-config configs/ppo_m541_matched_l3_variance_4096.json \
  --epochs 25 \
  --learning-rate 0.001 \
  --hidden-size 64 \
  --seed 5630 \
  --device cpu \
  --run-dir runs/m563_l3_behavior_cloning_smoke
```

Artifacts:

```text
runs/m563_l3_behavior_cloning_smoke/checkpoint.pt
runs/m563_l3_behavior_cloning_smoke/train_metrics.csv
runs/m563_l3_behavior_cloning_smoke/summary.json
```

MSE result:

| metric | initial | final | delta |
| --- | ---: | ---: | ---: |
| train action MSE | 0.083840 | 0.0000705 | -0.083770 |
| validation action MSE | 0.076715 | 0.000131 | -0.076584 |

Checkpoint metadata verification:

```text
obs_dim = 72
actor_encoder = human_view_online_gru
actor_history_length = 1
is_online_recurrent = true
history_baseline.level = L3_online_gru
input_contract = P0_human_view_no_wheel_no_oracle
ppo_used = false
promoted = false
```

## Tests

Focused tests:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_l3_behavior_cloning.py \
  tests/test_l2_teacher_corpus.py
```

Result:

```text
7 passed
```

The tests verify:

```text
BC corpus loading rejects teacher_obs_stack_seq
episode_start_seq defines recurrent hidden reset slices
offline BC improves train and validation MSE on a tiny corpus
saved checkpoint remains canonical P0 L3 online-GRU
```

## Interpretation

M563 proves only that the offline L3 BC path is technically valid and can reduce
teacher-action MSE without input leakage.

It does not prove closed-loop driving performance. A low action MSE checkpoint
can still fail route-screen due to exposure bias, small corpus size, or
teacher-forced histories.

## Decision

```text
l3_bc_optimizer_pass_admit_m564_route_screen_smoke
```

M563 passes because it implements the offline optimizer, improves train and
validation MSE, preserves the P0 L3 checkpoint contract, and avoids PPO,
promotion, public frozen-source rows, and L2 stack leakage.

## Next

```text
M564: evaluate the M563 BC smoke checkpoint with route-screen v2 seed 17560.
```

M564 should remain a route-screen diagnostic. A pass would admit public
diagnostics; a failure should be classified as exposure bias, corpus scale
insufficiency, or BC objective mismatch before trying PPO continuation.
