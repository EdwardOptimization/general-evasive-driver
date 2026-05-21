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
