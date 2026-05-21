# M26 Human-View GRU Results

Last updated: 2026-05-21

## Purpose

M26 is the first full training run under the M24 human-view input/output
contract. It trains from scratch with `human_view_online_gru`; old M21/M23
checkpoints are not compatible with the 72-value frame.

## Training

Command:

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m24_human_view_gru_driver.json \
  --seed 2024 \
  --device cuda \
  --run-dir runs/ppo_m26_human_view_gru_seed2024
```

Result:

- run dir: `runs/ppo_m26_human_view_gru_seed2024`;
- checkpoint: `runs/ppo_m26_human_view_gru_seed2024/checkpoint.pt`;
- periodic checkpoints: 102400, 200704, 303104, 401408, 503808, 602112,
  700416, 802816, and 900000;
- final eval return mean: 66.240;
- final eval steps mean: 59.100;
- final eval termination rate: 0.200;
- final eval lateral RMSE mean: 0.777;
- final eval beta absolute error mean: 0.132.

## Checkpoint Sweep

Run dir: `runs/m26_human_view_checkpoint_sweep_seed3000`.

| Policy | Success | Termination | Return |
| --- | ---: | ---: | ---: |
| `envelope_aes` | 0.675 | 0.325 | 56.594 |
| M26_102 | 0.725 | 0.275 | 64.016 |
| M26_200 | 0.725 | 0.275 | 62.948 |
| M26_303 | 0.725 | 0.275 | 63.115 |
| M26_401 | 0.775 | 0.225 | 66.175 |
| M26_503 | 0.775 | 0.225 | 66.079 |
| M26_602 | 0.800 | 0.200 | 67.765 |
| M26_700 | 0.775 | 0.225 | 66.751 |
| M26_802 | 0.775 | 0.225 | 68.118 |
| M26_900 | 0.775 | 0.225 | 67.552 |
| M26_final | 0.775 | 0.225 | 67.552 |

The current best human-view checkpoint by success is:

```text
runs/ppo_m26_human_view_gru_seed2024/checkpoints/checkpoint_step_602112.pt
```

## Ablation

Run dir: `runs/m26_602_human_view_ablation_seed3000`.

| Policy | Success | Termination | Return |
| --- | ---: | ---: | ---: |
| `envelope_aes` | 0.675 | 0.325 | 56.594 |
| M26_602 | 0.800 | 0.200 | 67.765 |
| M26_602 reset hidden | 0.800 | 0.200 | 66.288 |
| M26_602 zero current response | 0.775 | 0.225 | 66.545 |
| M26_602 zero all response | 0.775 | 0.225 | 66.545 |

This is positive for aggregate driving but weak for self-identification. Hidden
reset does not reduce success, and response masking only reduces success by
0.025.

Important interpretation boundary: hidden reset measures whether long-horizon
GRU memory is necessary for a specific gate. It does not measure all adaptation.
With the human-view frame, the current observation already contains ego response
signals and previous physical commands. A policy can therefore perform
one-step, nearly Markovian adaptation from current `last_action -> ax/ay/yaw`
feedback even when the recurrent hidden state is reset.

If a gate has fixed dynamics, or if the current observation is rich enough to
make the control problem close to Markov, reset and normal inference are
expected to be similar. That is not a proof that the controller cannot adapt;
it only means the gate does not require multi-step hidden-state
self-identification.

## Old Hard Seeds

Run dir: `runs/m26_602_human_view_m22_hard_seed_benchmark_seed3000`.

The old M22 hard seed corpus is not hard under the human-view contract:
`envelope_aes`, M26_602, reset, and response-masked policies all reach success
1.000 on those seven seeds. M22 should be treated as historical evidence for
the old 15-value frame, not a valid hard gate for M24/M26.

## Conclusion

M26 is a useful positive step: the human-view actor beats the model-based
envelope AES baseline on the 40-episode same-seed obstacle benchmark
(`0.800` vs `0.675` success at M26_602).

It is not an ideal-driver result. The ablations do not yet prove closed-loop
self-identification, and the old hard-response corpus no longer stresses the
new contract. The next milestone should build a new human-view hard
response-dependence gate around M26_602.

The next gate must separate three claims:

- can the policy drive well;
- can the policy adapt to different friction, vehicle, tire, brake, and
  actuator responses;
- does that adaptation require accumulated recurrent hidden state.

A stronger proof should use matched-current-observation cases: give normal GRU
policies a probing window under different hidden dynamics, then compare normal,
reset, zero-response, and hidden-swap variants at the same visible road and
obstacle state. Only a normal-vs-reset or hidden-swap difference on such cases
can support a strong self-identification claim.
