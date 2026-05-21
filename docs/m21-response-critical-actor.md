# M21 Response-Critical Actor Plan

Last updated: 2026-05-21

## Motivation

M20 improves aggregate obstacle performance, but it does not pass the
self-identification gate. The best checkpoint, `m20_700`, reaches success
`0.475` on the near-threshold obstacle corpus and improves M13 friction
perturbed success to `0.425`, but zeroing deployable response channels leaves
success unchanged. That means the current actor can still rely too much on
geometry and recurrent state shortcuts.

The next experiment should change the actor structure or loss so measured
vehicle response is control-critical. This should be done under the same clean
project rule: no old checkpoint compatibility, no privileged inputs, and no
oracle fields.

## Clean Contract

M21 must keep the current deployable actor I/O:

- observation frame: 15 values from `docs/observation-contract.md`;
- recurrent hidden state carried online by the actor;
- action: `[steering_command, drive_brake_command]`;
- no `mu`, vehicle parameter scales, `speed_ref`, `beta_target`, explicit
  `beta`, obstacle label, feasibility label, or friction-step timing;
- no shape adaptation from older checkpoints.

## Candidate Design

Use a response-critical online actor rather than the current single mixed
frame encoder:

- response stream: `vx`, `vy`, yaw rate, steering actuator state, drive/brake
  actuator state, and previous action;
- context stream: lateral error, heading error, curvature, along-path speed,
  and obstacle geometry;
- recurrent state update driven primarily by the response stream;
- actor head conditioned on both context embedding and response hidden state;
- optional interaction features such as elementwise products or a FiLM-style
  modulation from response hidden state to context features.

The intended failure mode is explicit: if response channels are zeroed, the
actor should lose the hidden-condition estimate and perform worse on paired
friction and actuator-response gates.

## Validation Gate

M21 should not be considered progress unless it beats the M20 result on both
performance and diagnostic dependence:

- same-corpus obstacle benchmark success above `m20_700` (`0.475`);
- M13 friction perturbed success at least `0.425`;
- actuator-response perturbed success at least `0.400`;
- hidden-reset and response-masked policies must be measurably worse than
  normal recurrent inference on at least one paired gate;
- no privileged or removed actor inputs in config or checkpoint metadata.

## First Implementation Step

Add a new strict `actor_encoder` variant for the response-critical online actor
and a smoke config that trains from scratch under the M20 environment contract.
Do not load M20 weights unless the architecture is exactly compatible; a clean
architecture change should start as a new run.

Implementation status:

- `actor_encoder="response_critical_online_gru"` is available;
- checkpoint loading is strict and recognizes the response/context encoder
  weights only when they match the canonical 7-response + 8-context frame;
- recurrent PPO sequence training supports the new online actor;
- `reset_recurrent_state` and response-channel ablations use the same
  evaluation harness as M18-M20.

Config:

```text
configs/ppo_m21_response_critical_actor.json
```

Queued command:

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m21_response_critical_actor.json \
  --seed 1031 \
  --device cuda \
  --run-dir runs/ppo_m21_response_critical_actor_seed1031
```

The new actor starts from scratch. It does not shape-adapt M18, M19, or M20
weights.

## Smoke Result

Command:

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m21_response_critical_actor.json \
  --total-steps 20480 \
  --seed 1031 \
  --device cuda \
  --run-dir runs/ppo_m21_response_critical_smoke_seed1031
```

Result:

- run dir: `runs/ppo_m21_response_critical_smoke_seed1031`;
- saved checkpoint: `runs/ppo_m21_response_critical_smoke_seed1031/checkpoint.pt`;
- eval return mean: 56.456;
- eval steps mean: 63.700;
- eval termination rate: 0.500;
- eval lateral RMSE mean: 0.554;
- eval beta absolute error mean: 0.175.

The smoke result only proves the architecture trains and evaluates under the
clean contract. It is not a driver-quality result. The full run must still pass
the M21 validation gate above.

## Full Result

Training completed through the research harness:

```text
runs/ppo_m21_response_critical_actor_seed1031/checkpoint.pt
```

Built-in final evaluation:

- return mean: 77.974;
- steps mean: 73.700;
- termination rate: 0.100;
- lateral RMSE mean: 0.867;
- beta absolute error mean: 0.179.

Periodic checkpoints were saved at steps 102400, 200704, 303104, 401408,
503808, 602112, 700416, 802816, and 900000.

Actuator-response checkpoint sweep:

| policy | nominal success | perturbed success | drop |
| --- | ---: | ---: | ---: |
| m20_700 | 0.475 | 0.400 | 0.075 |
| m21_102 | 0.400 | 0.325 | 0.075 |
| m21_200 | 0.425 | 0.375 | 0.050 |
| m21_303 | 0.400 | 0.400 | 0.000 |
| m21_401 | 0.475 | 0.425 | 0.050 |
| m21_503 | 0.500 | 0.450 | 0.050 |
| m21_602 | 0.475 | 0.450 | 0.025 |
| m21_700 | 0.450 | 0.450 | 0.000 |
| m21_802 | 0.450 | 0.450 | 0.000 |
| m21_900 | 0.425 | 0.450 | -0.025 |

Top-candidate actuator-response gate:

| policy | nominal success | perturbed success | drop |
| --- | ---: | ---: | ---: |
| m20_700 | 0.475 | 0.400 | 0.075 |
| m21_503 | 0.500 | 0.450 | 0.050 |
| m21_503_reset | 0.350 | 0.450 | -0.100 |
| m21_503_zero_current | 0.500 | 0.425 | 0.075 |
| m21_602 | 0.475 | 0.450 | 0.025 |
| m21_602_reset | 0.375 | 0.450 | -0.075 |
| m21_602_zero_current | 0.500 | 0.450 | 0.050 |
| m21_900 | 0.425 | 0.450 | -0.025 |
| m21_900_reset | 0.275 | 0.450 | -0.175 |
| m21_900_zero_current | 0.400 | 0.450 | -0.050 |

Top-candidate M13 friction gate:

| policy | nominal success | perturbed success | drop |
| --- | ---: | ---: | ---: |
| m20_700 | 0.875 | 0.425 | 0.450 |
| m21_503 | 0.900 | 0.450 | 0.450 |
| m21_503_reset | 0.900 | 0.400 | 0.500 |
| m21_503_zero_current | 0.900 | 0.450 | 0.450 |
| m21_602 | 0.900 | 0.450 | 0.450 |
| m21_602_reset | 0.900 | 0.300 | 0.600 |
| m21_602_zero_current | 0.900 | 0.450 | 0.450 |
| m21_900 | 0.875 | 0.400 | 0.475 |
| m21_900_reset | 0.875 | 0.250 | 0.625 |
| m21_900_zero_current | 0.875 | 0.425 | 0.450 |

Same-corpus obstacle benchmark:

| policy | success | termination | high sideslip |
| --- | ---: | ---: | ---: |
| envelope_aes | 0.250 | 0.750 | 0.000 |
| m20_700 | 0.475 | 0.525 | 0.000 |
| m21_503 | 0.500 | 0.500 | 0.005 |
| m21_503_reset | 0.450 | 0.550 | 0.021 |
| m21_503_zero_current | 0.500 | 0.500 | 0.002 |
| m21_602 | 0.475 | 0.525 | 0.009 |
| m21_602_reset | 0.400 | 0.600 | 0.024 |
| m21_602_zero_current | 0.500 | 0.500 | 0.007 |
| m21_900 | 0.425 | 0.575 | 0.022 |
| m21_900_reset | 0.325 | 0.675 | 0.061 |
| m21_900_zero_current | 0.475 | 0.525 | 0.025 |

Conclusion: M21 is a real aggregate-performance improvement but still not a
complete self-identification solution. The best checkpoint is `m21_503`: it
beats `m20_700` on same-corpus success (`0.500` vs `0.475`), actuator-response
perturbed success (`0.450` vs `0.400`), and M13 friction perturbed success
(`0.450` vs `0.425`). Hidden-state reset now hurts several checkpoints,
especially M21_602 and M21_900 on the friction gate. However, response masking
still does not reliably reduce success. The next milestone should make the
gate itself harder by mining or constructing paired cases where identical
geometry and different hidden response require different corrective actions.
