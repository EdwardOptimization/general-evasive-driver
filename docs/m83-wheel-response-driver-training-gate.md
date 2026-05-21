# M83 Wheel Response Driver Training Gate

M81 added the first deployable wheel/tire response input branch:

- 85-value `wheel_human_view_online_gru` actor input;
- 25-value response stream: body response, actuator state, previous commands,
  and front/rear wheel response;
- 60-value scene context stream with strict zero obstacle relative velocity;
- `zero_wheel_response` ablation support.

The M83 question is whether this new input branch can train into a useful
driver at meaningful smoke scale, and whether the resulting policy shows any
wheel/history dependence. This gate follows the 5.5pro MHTML review direction
preserved in `docs/external-review-5-5pro-mhtml.md`: wheel response is a
missing sensory channel for professional-driver-like self-identification, but
it must improve behavior under counterfactual ablations rather than merely
increase observation dimension.

## Training Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m81_wheel_response_gru_driver.json \
  --total-steps 32768 \
  --seed 3783 \
  --device cuda \
  --run-dir runs/ppo_m83_wheel_response_driver_seed3783 \
  --eval-episodes 10
```

Hardware check before training reported:

```text
NVIDIA GeForce RTX 5080, 16303 MiB
torch.cuda.is_available() True
```

The trainer ran on CUDA with 16 environments:

```text
training_device=cuda num_envs=16 curriculum_stage=base
step=20480 update=5 stage=base rollout_return_mean=24.92 reward_mean=0.464 episode_count=69
step=32768 update=8 stage=base rollout_return_mean=26.22 reward_mean=0.497 episode_count=75
saved=runs/ppo_m83_wheel_response_driver_seed3783/checkpoint.pt
```

Final built-in eval:

```text
return_mean = 27.55341663462969
steps_mean = 53.5
termination_rate = 0.9
lateral_rmse_mean = 0.8453905811077608
beta_abs_error_mean = 0.1333279218324991
```

## Ablation Gate

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 conda run -n autodrift python -m autodrift.benchmark \
  --env-config configs/ppo_m81_wheel_response_gru_driver.json \
  --episodes 20 \
  --seed 8830 \
  --policies heuristic \
  --checkpoint-policy m83=runs/ppo_m83_wheel_response_driver_seed3783/checkpoint.pt \
  --checkpoint-policy m83_zero_wheel=runs/ppo_m83_wheel_response_driver_seed3783/checkpoint.pt@zero_wheel_response \
  --checkpoint-policy m83_reset=runs/ppo_m83_wheel_response_driver_seed3783/checkpoint.pt@reset_recurrent_state \
  --checkpoint-policy m83_zero_all=runs/ppo_m83_wheel_response_driver_seed3783/checkpoint.pt@zero_all_response \
  --device cpu \
  --run-dir runs/m83_wheel_response_gate_seed8830
```

Summary:

| policy | success | termination | return mean | clearance mean | clearance min |
| --- | ---: | ---: | ---: | ---: | ---: |
| heuristic | 0.4 | 0.6 | 50.407181 | 0.479831 | -0.231359 |
| m83 | 0.1 | 0.9 | 30.452461 | 0.285214 | -0.242660 |
| m83_reset | 0.1 | 0.9 | 30.436058 | 0.258982 | -0.220446 |
| m83_zero_all | 0.1 | 0.9 | 29.598439 | 0.152147 | -0.237749 |
| m83_zero_wheel | 0.1 | 0.9 | 29.859377 | 0.224937 | -0.216904 |

## Interpretation

M83 is a negative result.

The 32k-step from-scratch wheel-response actor is not a candidate:

- it underperforms the heuristic baseline on the same 20-episode gate;
- aggregate success is only `0.1`;
- termination remains `0.9`;
- `zero_wheel_response`, `zero_all_response`, and `reset_recurrent_state`
  produce only weak differences because the base policy itself is poor.

There is a small clearance-margin drop under `zero_all_response` and
`zero_wheel_response`, but this is not useful self-identification evidence when
the normal M83 checkpoint already fails most episodes.

## Decision

Do not continue long from-scratch wheel-response training as the next step.
The 85-value actor has a harder optimization surface than the retained 72-value
M62 policy and currently loses the known driving behavior before wheel-response
history can become useful.

The next branch should preserve M62 behavior first:

```text
M84: M62 -> wheel-response partial initialization

copy M62 response encoder columns 0-11 into the wheel actor;
zero or neutralize the new wheel-response columns initially;
copy context encoder, GRU, fusion, actor, critic, and log_std where shapes match;
run a short wheel-response continuation and the same zero-wheel/history gate.
```

This tests the input branch under a better starting point: if wheel feedback is
useful, it should improve or at least preserve M62-class driving before it is
asked to demonstrate stronger self-identification.
