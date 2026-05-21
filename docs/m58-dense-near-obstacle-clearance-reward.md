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

## Full Result

Full training completed:

- command log:
  `runs/research/m58-dense-near-obstacle-clearance-reward_20260521T083531Z/command.log`;
- final eval return mean: `74.113`;
- final eval termination rate: `0.100`;
- checkpoint run:
  `runs/ppo_m58_dense_clearance_margin_reward_seed2658`.

Checkpoint sweeps:

- `runs/m58_m38_margin_benchmark_seed4300`;
- `runs/m58_broad_margin_benchmark_seed3000`;
- `runs/m58_fresh_margin_benchmark_seed5200`.

Strict gate:

- corpus: `runs/m58_margin_critical_corpus`;
- gate: `runs/m58_margin_retention_gate_strict`;
- status: `needs_iteration`;
- passed candidates: none.

Gate summary:

| Candidate | Passed | Success delta | Binary regressions | Near-margin regressions | Margin delta mean |
| --- | --- | ---: | ---: | ---: | ---: |
| m58_004 | false | 0.00000 | 0 | 0 | -0.002749 |
| m58_008 | false | -0.01250 | 2 | 0 | -0.005254 |
| m58_012 | false | -0.00625 | 1 | 1 | -0.004573 |
| m58_016 | false | 0.00000 | 0 | 1 | -0.002816 |
| m58_020 | false | 0.00000 | 0 | 0 | -0.003863 |
| m58_024 | false | -0.01875 | 3 | 1 | -0.007706 |
| m58_028 | false | -0.01875 | 3 | 1 | -0.008128 |
| m58_032 | false | -0.01875 | 3 | 0 | -0.005629 |

Dense near-obstacle reward is a negative result in this form. It eliminates
near-margin regressions for some early checkpoints, but the mean margin drops
more than M56/M57, and later checkpoints reintroduce binary regressions.

## Conclusion

M58 is not promotable. Current best remains `m37_102`; the closest
non-promoted candidate remains `m56_028`.

## Next Step

M59 should stop scaling reward terms and instead test a trust-region selection
path: checkpoint or weight interpolation between M37_102 and the closest
non-promoted candidates, especially M56_028. The goal is to determine whether
a very small update can satisfy the strict margin gate without training drift.
