# M595 BC Capability Corpus Runner Implementation

## Purpose

M595 implements the closed-loop BC5660 capability corpus and same-corpus
matched-current pair runner designed in M594.

This milestone is infrastructure plus smoke export only:

```text
no repair training
no PPO
no route evaluation
no checkpoint promotion
```

## Implementation

M595 adds:

```text
src/autodrift/bc_capability_corpus.py
tests/test_bc_capability_corpus.py
```

The corpus runner exports:

```text
capability_corpus.npz
pairs.csv
target_summary.csv
pair_summary.csv
summary.json
```

The NPZ schema is:

```text
student_obs_seq          (N, 72)
anchor_action_seq        (N, 3)
capability_target_seq    (N, 3)
done_seq                 (N,)
episode_start_seq        (N,)
seed_seq                 (N,)
episode_id_seq           (N,)
step_seq                 (N,)
base_hidden_seq          (N, H)   # diagnostic only
base_next_hidden_seq     (N, H)   # diagnostic / training target path only
```

Capability labels are:

```text
future_braking_deceleration
future_yaw_response
future_lateral_accel_response
```

They are stored as training/evaluation targets only and are not appended to the
actor observation.

## Focused Tests

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_bc_capability_corpus.py \
  tests/test_bc_capability_repair.py
```

Result:

```text
7 passed
```

The tests verify:

- corpus arrays have the expected shapes;
- invalid actor observation shapes are rejected;
- matched-current pair rows reference valid corpus row indices;
- pair rows preserve seed/step provenance and target-z thresholds.

## Real Runner Smoke

Single-seed export smoke:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.bc_capability_corpus \
  --base-checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --env-config configs/ppo_m541_matched_l3_variance_4096.json \
  --seeds 25950 \
  --horizon-steps 2 \
  --sample-stride 4 \
  --max-samples 8 \
  --nearest-k 4 \
  --min-target-z-delta 0.5 \
  --max-pairs-per-target 4 \
  --max-visible-quantile 1.0 \
  --device cpu \
  --run-dir runs/m595_bc_capability_corpus_runner_smoke
```

Result:

```text
row_count = 8
pair_count = 0
labels_enter_actor_input = false
contains_privileged_actor_inputs = false
```

The zero pair count is expected because this smoke uses one episode and the
pair miner excludes same-episode pairs.

Multi-seed pair smoke:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.bc_capability_corpus \
  --base-checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --env-config configs/ppo_m541_matched_l3_variance_4096.json \
  --seeds 25950,25951,25952 \
  --horizon-steps 2 \
  --sample-stride 4 \
  --max-samples 24 \
  --nearest-k 8 \
  --min-target-z-delta 0.5 \
  --max-pairs-per-target 6 \
  --max-visible-quantile 1.0 \
  --device cpu \
  --run-dir runs/m595_bc_capability_corpus_pair_smoke
```

Result:

```text
row_count = 24
student_obs_dim = 72
action_dim = 3
target_dim = 3
hidden_dim = 64
pair_count = 18
labels_enter_actor_input = false
contains_privileged_actor_inputs = false
```

Pair summary:

| target | pair count | mean target z delta | max target z delta |
| --- | ---: | ---: | ---: |
| future_braking_deceleration | 6 | 2.965795 | 3.101528 |
| future_yaw_response | 6 | 4.125291 | 4.131886 |
| future_lateral_accel_response | 6 | 3.586460 | 4.010313 |

## Interpretation

M595 validates the data path needed for real capability repair:

```text
P0 observation + base action anchor + future-response label + same-corpus pair
rows can be generated from a closed-loop BC5660 rollout.
```

This does not yet prove hidden repair works. It only proves the runner can
produce aligned training artifacts without actor-input leakage.

## Next

M596 should export a slightly larger train/validation capability corpus and
pair set before any repair optimizer is run.

## Decision

```text
bc_capability_corpus_runner_implementation_admit_export_smoke
```

M595 passes because it implements the corpus/pair runner, passes focused tests,
and completes a real multi-seed export smoke with same-corpus pair rows.
