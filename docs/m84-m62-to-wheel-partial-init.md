# M84 M62-to-Wheel Partial Initialization

M83 showed that training the 85-value wheel-response actor from scratch is too
weak to judge the input branch. The M84 hypothesis is narrower:

```text
Start from retained M62 behavior first.
Then expose the policy to the extra wheel-response channels.
```

This follows the persisted 5.5pro MHTML review guidance: wheel/tire response is
a plausible missing sensory channel for professional-driver-like online
self-identification, but it should be added without destroying the current best
driver behavior.

## Code Change

`load_init_checkpoint_state(...)` now supports a controlled partial load from a
72-value `human_view_online_gru` actor into an 85-value
`wheel_human_view_online_gru` actor:

- copy `response_encoder.0.weight[:, 0:12]` from the human-view checkpoint;
- set the new wheel-response columns `[:, 12:25]` to zero;
- copy response bias, context encoder, GRU, fusion, actor, critic, `log_std`,
  and matching auxiliary heads;
- keep response-prediction head partial resizing behavior unchanged.

The intended load mode is:

```text
partial_wheel_response_encoder
```

This makes the initialized wheel actor behavior-preserving when the 85-value
observation is:

```text
[human_response_12, wheel_response_13, human_context_60]
```

because the wheel columns are neutral at initialization.

## Focused Test

Added:

```text
tests/test_checkpoints.py::test_wheel_human_view_init_preserves_human_view_behavior
```

The test verifies:

- the first 12 response columns match the source human-view encoder;
- the new wheel-response columns are exactly zero;
- context encoder weights match;
- action, log probability, value, and next recurrent hidden state match the
  source 72-value actor even when the wheel-response values are nonzero.

Focused validation:

```bash
python -m json.tool configs/ppo_m84_wheel_response_warmstart_driver.json
python -m compileall -q src tests
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src conda run -n autodrift pytest -q \
  tests/test_checkpoints.py::test_wheel_human_view_init_preserves_human_view_behavior
```

Result:

```text
1 passed
```

## Warm-Start Smoke

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m84_wheel_response_warmstart_driver.json \
  --total-steps 4096 \
  --rollout-steps 64 \
  --num-envs 4 \
  --vector-env-mode sync \
  --seed 3884 \
  --device cuda \
  --init-checkpoint runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt \
  --run-dir runs/ppo_m84_wheel_warmstart_smoke_seed3884 \
  --eval-episodes 4
```

The real M62 checkpoint loads through the new path:

```text
loaded_init_checkpoint=.../alpha_0_25.pt load_mode=partial_wheel_response_encoder
```

Smoke result:

```text
return_mean = 78.21965725064047
steps_mean = 77.75
termination_rate = 0.0
lateral_rmse_mean = 0.8642115332149448
beta_abs_error_mean = 0.1461498611303628
```

This is a large improvement over the M83 from-scratch smoke, which had
`termination_rate = 0.9`.

## Ablation Gate

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 conda run -n autodrift python -m autodrift.benchmark \
  --env-config configs/ppo_m84_wheel_response_warmstart_driver.json \
  --episodes 20 \
  --seed 8830 \
  --policies heuristic \
  --checkpoint-policy m84=runs/ppo_m84_wheel_warmstart_smoke_seed3884/checkpoint.pt \
  --checkpoint-policy m84_zero_wheel=runs/ppo_m84_wheel_warmstart_smoke_seed3884/checkpoint.pt@zero_wheel_response \
  --checkpoint-policy m84_reset=runs/ppo_m84_wheel_warmstart_smoke_seed3884/checkpoint.pt@reset_recurrent_state \
  --checkpoint-policy m84_zero_all=runs/ppo_m84_wheel_warmstart_smoke_seed3884/checkpoint.pt@zero_all_response \
  --device cpu \
  --run-dir runs/m84_wheel_warmstart_gate_seed8830
```

Summary:

| policy | success | termination | return mean | clearance mean | clearance min |
| --- | ---: | ---: | ---: | ---: | ---: |
| heuristic | 0.40 | 0.60 | 50.407181 | 0.479831 | -0.231359 |
| m84 | 0.90 | 0.10 | 44.442587 | 2.107145 | -0.068371 |
| m84_reset | 0.85 | 0.15 | 41.015447 | 2.101834 | -0.067297 |
| m84_zero_all | 0.90 | 0.10 | 45.931012 | 2.053412 | -0.121621 |
| m84_zero_wheel | 0.90 | 0.10 | 44.441725 | 2.108047 | -0.069960 |

## Interpretation

M84 is a positive infrastructure and retention result, not a wheel
self-identification pass.

What it proves:

- the 85-value wheel actor can be initialized from M62 without breaking the
  retained behavior;
- the new checkpoint path is behavior-preserving by construction and by test;
- the warm-started wheel actor is much stronger than the M83 from-scratch actor.

What it does not prove:

- wheel-response features are behavior-critical;
- recurrent hidden state is using wheel response for online identification;
- zeroing wheel response hurts the policy.

The `m84_zero_wheel` result is nearly identical to normal M84 because the new
wheel columns are initialized neutral and the 4096-step continuation is too
short to force wheel use.

## Next Step

M85 should make wheel response part of a training signal while retaining M62
behavior:

```text
M85: warm-started wheel-response auxiliary continuation

start from M84 partial init;
predict the full 25-value response stream or a wheel/body response envelope;
keep baseline/action or margin-retention guards;
gate normal vs zero-wheel/reset/zero-all after continuation.
```

The pass condition is not just aggregate success. M85 only matters if it keeps
M84/M62-class margin while making `zero_wheel_response` or wrong wheel-history
interventions measurably worse.
