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

## Full Result

Full training completed:

- command log:
  `runs/research/m56-terminal-clearance-margin-reward_20260521T081954Z/command.log`;
- final eval return mean: `80.382`;
- final eval termination rate: `0.100`;
- checkpoint run:
  `runs/ppo_m56_clearance_margin_reward_seed2456`.

Checkpoint sweeps:

- `runs/m56_m38_margin_benchmark_seed4300`;
- `runs/m56_broad_margin_benchmark_seed3000`;
- `runs/m56_fresh_margin_benchmark_seed5200`.

Strict gate:

- corpus: `runs/m56_margin_critical_corpus`;
- gate: `runs/m56_margin_retention_gate_strict`;
- status: `needs_iteration`;
- passed candidates: none.

Gate summary:

| Candidate | Passed | Success delta | Binary regressions | Near-margin regressions | Margin delta mean |
| --- | --- | ---: | ---: | ---: | ---: |
| m56_004 | false | 0.00000 | 0 | 1 | -0.000445 |
| m56_008 | false | -0.00625 | 1 | 4 | -0.001418 |
| m56_012 | false | -0.01250 | 2 | 7 | -0.000429 |
| m56_016 | false | -0.00625 | 1 | 6 | -0.001967 |
| m56_020 | false | 0.00000 | 0 | 1 | -0.002899 |
| m56_024 | false | -0.01250 | 2 | 0 | -0.003555 |
| m56_028 | false | 0.00000 | 0 | 0 | -0.001527 |
| m56_032 | false | -0.00625 | 1 | 4 | -0.000600 |

M56 improves over M55 in one important way: `m56_028` has zero binary
regressions and zero near-margin regressions. It still fails because combined
mean margin is slightly negative. The terminal reward therefore moves in the
right direction, but the scale `2.0` is not enough to produce positive mean
margin under the strict gate.

## Next Step

M57 should rerun the same schedule with stronger terminal clearance-margin
reward scale `4.0` while leaving the gate unchanged. If stronger sparse reward
still fails mean margin retention, the next objective change should be a denser
near-obstacle clearance signal rather than further data-mixture tuning.
