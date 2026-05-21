# M58: Dense Near-Obstacle Clearance Reward

## Motivation

M56 and M57 show that sparse terminal clearance-margin reward is not enough:
it can reduce binary and near-margin regressions, but it does not reliably
produce non-negative mean margin under the strict gate. M58 adds a denser
near-obstacle clearance reward for better credit assignment.

## Implementation

M58 extends `ObstacleTaskConfig` with:

- `dense_clearance_margin_reward_scale`, default `0.0`;
- `dense_clearance_margin_reward_clip`, default `0.25`;
- `dense_clearance_margin_reward_window`, default `8.0`.

When enabled, the reward applies only while the obstacle longitudinal distance
is inside the encounter window:

```text
-finish_pass_distance <= obstacle_longitudinal_distance <= dense_window
```

The reward is:

```text
scale * clip(min_clearance_margin / clip, -1, 1)
```

Actor observations are unchanged.

## Tests And Smoke

Targeted tests:

```bash
conda run -n autodrift pytest -q tests/test_env.py tests/test_config.py
```

Result: `27 passed`.

Training smoke:

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m58_dense_clearance_margin_reward_driver.json \
  --total-steps 1024 \
  --rollout-steps 128 \
  --seed 2658 \
  --device cuda \
  --init-checkpoint runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt \
  --run-dir runs/ppo_m58_dense_clearance_margin_reward_smoke_seed2658
```

Result:

- init load mode: `strict`;
- curriculum stage: `base`;
- smoke checkpoint written;
- final eval return mean: `73.938`;
- final eval termination rate: `0.100`.

## Full Experiment

M58 should reuse the conservative schedule:

- start from `m37_102`;
- terminal clearance margin reward scale `2.0`;
- dense near-obstacle margin reward scale `0.04`;
- dense reward clip `0.25`;
- dense reward window `8.0` meters;
- hard seed mix `0.15`;
- checkpoints every `4096` steps over `32768` total steps.

Promotion gate remains unchanged.
