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
