# M7 First-Stage Results

Last updated: 2026-05-21

## Scope

This note records the first M7 implementation pass. It is an infrastructure and
smoke-validation result, not a completed M7 training result.

Implemented pieces:

- `action_history_mode="full"` for deployable actor inputs that include both
  previous drive/brake and previous steering commands while preserving the
  legacy observation prefix for old checkpoint expansion;
- hidden vehicle-road diagnostics in `info`, including mass, CG, brake, tire,
  and actuator-delay scales;
- M7-A history actor path through stacked observations and full action history;
- M7-B receding-horizon sequence actor path with
  `action_sequence_horizon > 1`, executing only the first action;
- sequence auxiliary target construction from future executed actions inside
  the rollout buffer;
- checkpoint compatibility so older M5 checkpoints can be expanded to the M7
  observation shape and M7-B can add a new sequence head;
- benchmark support for multiple named checkpoint policies through
  `--checkpoint-policy name=path`;
- vehicle-road bucket summaries for held-out analysis.

## Configs

New configuration files:

- `configs/ppo_m7a_history_obstacle.json`;
- `configs/ppo_m7b_sequence_obstacle.json`;
- `configs/m7_obstacle_holdout_eval.json`.

All three use:

- `history_length=4`;
- `action_history_mode="full"`;
- AEB-infeasible obstacle sampling;
- `aes_feasible`, `drift_required`, and `unavoidable` labels;
- broader vehicle-road randomization than M5.

## Smoke Training Commands

M7-A smoke:

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m7a_history_obstacle.json \
  --init-checkpoint runs/ppo_m5_obstacle_seed83/checkpoint.pt \
  --total-steps 128 \
  --rollout-steps 32 \
  --eval-episodes 2 \
  --device cpu \
  --run-dir runs/ppo_m7a_history_smoke
```

Result:

- load mode: `partial_input_expand`;
- eval return mean: `91.179`;
- eval termination rate: `0.000`.

M7-B smoke:

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m7b_sequence_obstacle.json \
  --init-checkpoint runs/ppo_m5_obstacle_seed83/checkpoint.pt \
  --total-steps 128 \
  --rollout-steps 32 \
  --eval-episodes 2 \
  --device cpu \
  --run-dir runs/ppo_m7b_sequence_smoke
```

Result:

- load mode: `new_sequence_head+partial_input_expand`;
- eval return mean: `-25.163`;
- eval termination rate: `1.000`.

Interpretation: the M7-B smoke proves the sequence-head training path and
checkpoint format work, but the 128-step result is a negative performance
result.

## Held-Out Benchmark Smoke

Mixed-label command:

```bash
conda run -n autodrift python -m autodrift.benchmark \
  --episodes 6 \
  --seed 1 \
  --policies aeb aes_heuristic envelope_aes \
  --checkpoint-policy m5=runs/ppo_m5_obstacle_seed83/checkpoint.pt \
  --checkpoint-policy m7a=runs/ppo_m7a_history_smoke/checkpoint.pt \
  --checkpoint-policy m7b=runs/ppo_m7b_sequence_smoke/checkpoint.pt \
  --env-config configs/m7_obstacle_holdout_eval.json \
  --device cpu \
  --run-dir runs/benchmark_m7_operator_smoke_mixed
```

Policy summary:

| policy | episodes | success_rate | collision_rate | obstacle_completion_rate | plan_horizon_mean |
| --- | ---: | ---: | ---: | ---: | ---: |
| `aeb` | 6 | 0.333 | 0.667 | 0.333 | 1 |
| `aes_heuristic` | 6 | 0.167 | 0.833 | 0.167 | 1 |
| `envelope_aes` | 6 | 0.667 | 0.333 | 0.667 | 1 |
| `m5` | 6 | 0.667 | 0.333 | 0.667 | 1 |
| `m7a` | 6 | 0.667 | 0.333 | 0.667 | 1 |
| `m7b` | 6 | 0.667 | 0.333 | 0.667 | 6 |

Obstacle-label result:

- `aes_feasible`: `m5`, `m7a`, and `m7b` all reached `1.000` success in this
  small seed set;
- `drift_required`: `m5`, `m7a`, and `m7b` all reached `1.000` success in this
  small seed set;
- `unavoidable`: all policies reached `0.000` success, as expected for this
  label under the current binary success definition.

Interpretation:

- the benchmark harness can compare AEB, heuristic AES, envelope AES, M5, M7-A,
  and M7-B under the same held-out physical configuration;
- the M7-B sequence preview is recorded (`plan_horizon_mean=6`);
- M7-A and M7-B are still essentially M5 warm-start smoke checkpoints and do
  not yet prove improvement.

## Negative Results And Gaps

- M7-B's direct two-episode eval after 128 training steps terminates every
  episode.
- A four-episode smoke with seed `500` sampled only `unavoidable` cases, and all
  policies failed; this is useful for pipeline testing but not a balanced
  validation result.
- No long M7-A or M7-B training run has been completed yet.
- No `single_frame`, `no_action_history`, `shuffled_history`, or privileged-leak
  ablation has been run yet.
- No latent self-identification probe has been implemented yet.
- M7-B sequence smoothness is recorded, but no safety-preview decision rule has
  been validated.

## Next Steps

1. Run real M7-A training from the M5 checkpoint with the full 1M-step config.
2. Run real M7-B training from the M5 checkpoint with the sequence auxiliary
   loss enabled.
3. Run held-out benchmarks with at least 100 seeds and label-balanced reporting.
4. Add ablation configs for `single_frame`, `no_action_history`, and
   `privileged_leak`.
5. Implement latent probe tooling on frozen rollout data.
