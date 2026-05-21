# M56: Terminal Clearance-Margin Reward

## Motivation

M55 found an early checkpoint with zero binary regressions, but every
checkpoint still failed strict margin retention because mean clearance margin
was lower than M37 and at least one near-margin regression remained. This means
the conservative data mixture can preserve outcomes, but the training objective
does not directly reward near-boundary clearance.

M56 adds a config-gated terminal clearance-margin reward for training only.
Actor observations remain unchanged.

## Implementation

M56 extends `ObstacleTaskConfig` with:

- `clearance_margin_reward_scale`, default `0.0`;
- `clearance_margin_reward_clip`, default `0.25`.

When enabled, the environment adds this reward only on terminal obstacle
success or collision:

```text
reward += scale * clip(min_clearance_margin / clip, -1, 1)
```

The term is written to `info["reward_terms"]` as:

- `clearance_margin_reward`;
- `clearance_margin_reward_normalized`.

This does not add margin, labels, hidden vehicle parameters, or other oracle
fields to the actor input.

## Tests And Smoke

Targeted tests:

```bash
conda run -n autodrift pytest -q tests/test_env.py tests/test_config.py
```

Result: `26 passed`.

Training smoke:

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m56_clearance_margin_reward_driver.json \
  --total-steps 1024 \
  --rollout-steps 128 \
  --seed 2456 \
  --device cuda \
  --init-checkpoint runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt \
  --run-dir runs/ppo_m56_clearance_margin_reward_smoke_seed2456
```

Result:

- init load mode: `strict`;
- curriculum stage: `base`;
- smoke checkpoint written;
- final eval return mean: `80.410`;
- final eval termination rate: `0.100`.

## Full Experiment

M56 full training should reuse the M55 conservative schedule:

- start from `m37_102`;
- `learning_rate = 1e-5`;
- `training_seed_mix_probability = 0.15`;
- no low-mu-only curriculum stage;
- `32768` total steps;
- checkpoints every `4096` steps;
- terminal clearance-margin reward scale `2.0`, clip `0.25`.

Promotion gate remains unchanged: zero binary regressions, zero near-margin
regressions, and non-negative mean margin delta versus M37_102.
