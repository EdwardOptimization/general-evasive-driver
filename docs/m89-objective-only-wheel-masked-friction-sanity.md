# M89 Objective-Only Wheel-Masked Friction Sanity

M88 showed that the wheel-only masked friction auxiliary path works, but PPO
coupling still did not make wheel response behavior-critical. M89 follows the
M80 lesson:

```text
Before adding more PPO continuation,
prove that the objective can move in isolation.
```

## Harness

Added:

```text
src/autodrift/wheel_masked_friction_optimize.py
```

The harness:

- loads a 72-value M62 checkpoint into the 85-value wheel actor through
  `partial_wheel_response_encoder`;
- collects wheel-profile rollout observations;
- applies the `wheel_only` auxiliary mask;
- predicts `mu_bucket` from response GRU hidden state;
- optimizes only response encoder, online GRU, and a temporary classifier;
- does not train PPO reward, actor head, critic, context encoder, or `log_std`;
- writes an `optimized_checkpoint.pt` for downstream gates.

This keeps the test narrow: can the wheel-masked friction objective itself make
wheel response usable?

## Tests

Added:

```text
tests/test_wheel_masked_friction_optimize.py
```

Coverage:

- body/wheel response encoder norm split;
- objective-only optimizer excludes actor head;
- config parser ignores non-`PPOConfig` keys such as `eval_episodes`.

Focused validation:

```text
3 passed
```

## Objective-Only Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 conda run -n autodrift python -m autodrift.wheel_masked_friction_optimize \
  --config configs/ppo_m88_wheel_masked_friction_aux_driver.json \
  --init-checkpoint runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt \
  --episodes 30 \
  --seed 9200 \
  --device cuda \
  --max-samples 1500 \
  --steps 200 \
  --batch-size 256 \
  --learning-rate 0.0003 \
  --run-dir runs/m89_wheel_masked_friction_objective_only_seed9200
```

Objective result:

| split | loss | accuracy | samples |
| --- | ---: | ---: | ---: |
| train_before | 1.110010 | 0.297774 | 1078 |
| test_before | 1.198972 | 0.078199 | 422 |
| train_after | 0.853695 | 0.546382 | 1078 |
| test_after | 0.858630 | 0.668246 | 422 |

Response encoder norms:

```text
before body_norm  = 7.819829
before wheel_norm = 0.000000
after body_norm   = 7.819695
after wheel_norm  = 2.008215
wheel_norm_delta  = 2.008215
```

This is a positive objective-only sanity result.

## Behavior Gate

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 conda run -n autodrift python -m autodrift.benchmark \
  --env-config configs/ppo_m88_wheel_masked_friction_aux_driver.json \
  --episodes 20 \
  --seed 8830 \
  --policies heuristic \
  --checkpoint-policy m89=runs/m89_wheel_masked_friction_objective_only_seed9200/optimized_checkpoint.pt \
  --checkpoint-policy m89_zero_wheel=runs/m89_wheel_masked_friction_objective_only_seed9200/optimized_checkpoint.pt@zero_wheel_response \
  --checkpoint-policy m89_reset=runs/m89_wheel_masked_friction_objective_only_seed9200/optimized_checkpoint.pt@reset_recurrent_state \
  --checkpoint-policy m89_zero_all=runs/m89_wheel_masked_friction_objective_only_seed9200/optimized_checkpoint.pt@zero_all_response \
  --device cpu \
  --run-dir runs/m89_wheel_masked_friction_objective_gate_seed8830
```

Summary:

| policy | success | termination | return mean | clearance mean | clearance min |
| --- | ---: | ---: | ---: | ---: | ---: |
| heuristic | 0.40 | 0.60 | 50.407181 | 0.479831 | -0.231359 |
| m89 | 0.90 | 0.10 | 70.582566 | 2.115762 | -0.130489 |
| m89_reset | 0.80 | 0.20 | 65.272062 | 2.145665 | -0.098783 |
| m89_zero_all | 0.90 | 0.10 | 69.222604 | 2.147918 | -0.093647 |
| m89_zero_wheel | 0.85 | 0.15 | 68.711430 | 2.133370 | -0.126069 |

This is not a full self-ID pass, but it is the first wheel branch result where
objective-only optimization preserves strong aggregate behavior and produces a
small behavior-level zero-wheel drop.

## Relevance Audit

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 conda run -n autodrift python -m autodrift.wheel_response_relevance_audit \
  --checkpoint runs/m89_wheel_masked_friction_objective_only_seed9200/optimized_checkpoint.pt \
  --env-config configs/ppo_m88_wheel_masked_friction_aux_driver.json \
  --episodes 30 \
  --seed 9100 \
  --device cpu \
  --max-samples 1500 \
  --epochs 120 \
  --run-dir runs/m89_wheel_masked_friction_relevance_audit_seed9100
```

Key rows:

| target | body | wheel | body+wheel | body+wheel gain |
| --- | ---: | ---: | ---: | ---: |
| mu_bucket | 0.756646 | 0.343558 | 0.893661 | 0.137014 |
| cg_bucket | 0.237219 | 0.566462 | 0.276074 | 0.038855 |

The important result is `mu_bucket`: body+wheel gain rises to `+0.137014`,
which is stronger than M86 (`+0.102410`) and much stronger than M88
(`+0.006160`).

## Interpretation

M89 is a positive objective sanity result and a partial wheel-signal result.

What it proves:

- the wheel-masked friction objective can move in isolation;
- wheel encoder columns can grow from neutral initialization;
- test-set friction-bucket accuracy improves substantially;
- aggregate driving behavior is retained at `success_rate = 0.90`;
- zero-wheel and reset ablations now show a small directional drop.

What it does not prove:

- wheel response is yet required for the full driver;
- the improvement survives PPO continuation;
- wrong-wheel-history interventions produce a large outcome gap;
- broad vehicle self-identification is solved.

## Decision

Proceed to M90:

```text
M90: guarded PPO continuation from M89 objective-only checkpoint

init from optimized_checkpoint.pt;
keep M62/M89 retention guards;
use low learning rate and baseline action anchor;
gate normal/reset/zero-wheel/zero-all;
rerun wheel relevance audit;
only promote if aggregate margin is retained and zero-wheel gap increases.
```

M89 should be treated as a useful new starting point, not as a promoted driver.
