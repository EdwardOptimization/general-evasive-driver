# M24 Human-View Driver Contract

Last updated: 2026-05-21

## Motivation

M23 showed that hard-only replay overfits a small mined response corpus. Before
running another fine-tune, the actor input contract needed a stronger cleanup:
the old 15-value obstacle frame still contained path-tracking features and
precomputed obstacle quantities that are not how a human driver perceives the
scene.

M24 replaces that frame with a human-view GRU contract. The driver now observes
ego vehicle response, actuator feedback, previous physical commands, ego-frame
road boundaries, and ego-frame obstacle slots.

## Implemented Contract

The canonical actor frame is now 72 values:

- 9 ego-response values;
- 3 previous physical command values;
- 32 road-boundary values for eight left and eight right lookahead points;
- 28 obstacle-slot values for four ego-frame object slots.

The current simulator action is now three-dimensional:

```text
[steering_command, throttle_command, brake_command]
```

The PPO head still emits normalized tanh actions in `[-1, 1]`. The environment
maps throttle and brake to physical pedal positions in `[0, 1]` and exposes
those physical previous commands in the next observation.

## Removed From Actor Observation

M24 removes these old actor inputs:

- path lateral error;
- path heading error;
- path curvature;
- along-path speed;
- required lateral obstacle clearance;
- time to obstacle.

The environment can still use those values for reward, termination, logging,
and oracle baselines. They are not part of the deployable RL actor frame.

## Actor Architecture

The next trainable actor should use:

```text
actor_encoder = "human_view_online_gru"
history_length = 1
action_history_mode = "full"
```

The response stream is indices `0-11`: ego response plus previous physical
commands. The context stream is indices `12-71`: road and obstacle perception.
History and self-identification must live in the GRU hidden state.

## Validation

M24 infrastructure validation is interface-level:

- environment reset/step returns finite 72-value observations;
- action space accepts 3-value normalized commands;
- dynamics maps throttle/brake to separate physical pedal states;
- observation ablations zero the new response/action indices;
- human-view online GRU checkpoints require the 72-value frame strictly.

The next research run should train from scratch under this contract. Old M21 and
M23 checkpoints are historical evidence, not compatible initializations.
