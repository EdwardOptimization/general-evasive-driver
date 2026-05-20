# M7 Universal Closed-Loop RL Operator

Last updated: 2026-05-21

## Purpose

The next project stage is to turn the current task-specific RL checkpoints into
a general vehicle operator. The target is not a controller tuned for one car or
one road surface. The target is a closed-loop policy that can stabilize and
avoid obstacles across changing vehicle mass, CG, tire grip, braking authority,
steering response, actuator lag, and road friction.

The operator is drift-capable, not drift-seeking. It should drive normally when
stable avoidance is enough, use high-sideslip or drift behavior when the
scenario demands it, and recover after the maneuver.

The deployment controller should behave like a driver-like trained operator:

```text
sensor and action history
  -> RL operator
  -> steering and throttle/brake commands
  -> vehicle response
  -> updated sensor and action history
```

The actor should not depend on explicit rule branches such as "if slip is high,
then counter-steer." It should learn continuous feedback corrections from the
observed vehicle response and its own recent actions.

## Driver-Like Operator Contract

M7 treats direct closed-loop operation as a hard constraint.

The policy must learn the same control loop that a skilled driver uses:

```text
what I saw and felt
  + what I just did with steering, throttle, and brake
  + how the vehicle responded
  -> what I do next
```

This has several concrete consequences:

- the actor must receive its own recent action history or actuator state;
- the actor must receive enough recent vehicle response to infer whether its
  previous actions helped or hurt;
- the actor must not receive rule-selected modes such as `drift_required`,
  `aes_feasible`, `low_mu_mode`, or `counter_steer_mode`;
- the actor must not receive true hidden simulator parameters such as friction,
  mass, CG, tire stiffness, or brake strength at deployment time;
- the normal control path must not switch to an if-else controller after the RL
  actor has acted.

Rules can define the training world and the evaluation labels. They cannot be
the deployed driving skill.

## Drift-Capable, Not Drift-Seeking

M7 is not a policy that should drift in every emergency. It is a professional
driver-like operator that can choose the right level of tire utilization for the
scenario through learned closed-loop behavior.

Expected behavior by scenario:

- `aes_feasible`: avoid the obstacle with stable steering and braking when
  possible, minimizing unnecessary sideslip, action chatter, and recovery cost;
- `drift_required`: use nonlinear tire behavior, yaw rotation, or high sideslip
  when conventional AES is not enough;
- `unavoidable`: reduce harm, collision severity, and residual speed as much as
  possible instead of chasing a drift reward;
- after obstacle pass: recover heading, speed, and sideslip rather than only
  "surviving" the instant of clearance.

This matters because the target is a general driving operator, not a drift demo.
High sideslip is a tool. It is not the objective.

## Core Principle

The main controller is a neural closed-loop policy, not a rule selector.

Rules are allowed in:

- scenario generation;
- reward and termination definitions;
- evaluation labels and benchmark buckets;
- offline diagnostics;
- safety monitoring and fallback reporting.

Rules should not be the deployed driving logic. A safety monitor can reject or
log obviously unsafe behavior, but it should not become the normal AES/drift
avoidance controller. The policy itself must learn how to recover from the
vehicle's feedback.

## Operator Interface

The operator receives observations that are available from sensing and recent
control history:

- body-frame velocities, yaw rate, sideslip estimate, steering state, and drive
  or brake state;
- path or obstacle-relative features;
- previous steering and throttle/brake commands;
- short history of states, actions, and resulting motion.

The operator outputs continuous low-level commands:

- normalized steering command;
- normalized throttle/brake command.

This keeps the control loop direct:

```text
observation history -> actor -> [steer, drive/brake]
```

There is no required intermediate path planner and no required NMPC layer
between the actor and the vehicle dynamics. Model-based controllers remain
benchmarks, safety filters, or fallback components, not the main research
mechanism.

## Self-Identification Objective

M7 should make the policy identify the hidden vehicle-road condition from
closed-loop feedback.

This does not require the actor to output named physical parameters such as
`mu=0.42` or `mass_scale=1.08`. The useful internal variable can be a learned
latent state that encodes controllability:

- how much lateral force the road and tires can still provide;
- how strong braking is relative to speed and obstacle distance;
- how quickly steering input changes yaw response;
- whether the vehicle is rotating too slowly, rotating usefully, or about to
  spin;
- whether throttle, brake, or steering correction is the right next action.

The important test is behavioral: after a short interaction history, the same
actor should correct its actions differently on a light car, heavy car,
weak-brake car, slow-steering car, high-grip road, low-grip road, and split-mu
road.

Diagnostics may train probes from the actor's latent state to estimate hidden
parameters, but those probes are for analysis only. The actor itself should
operate from deployable observations and memory.

## Training Direction

M7 should replace single-frame decision making with response-based adaptation.

Recommended implementation order:

1. Add history-stacked M5 obstacle training.
2. Make previous actions and actuator states first-class observation channels.
3. Add recurrent actor support, starting with GRU or a compact temporal
   convolution.
4. Add asymmetric PPO: the actor sees deployable observations only, while the
   critic may see privileged training-only parameters.
5. Increase domain randomization for vehicle and actuator properties.
6. Add holdout benchmark suites for unseen vehicle families and friction
   profiles.
7. Add ablations that remove action history, remove recurrence, or leak
   privileged parameters, so the project can measure which mechanism actually
   produces adaptation.

The actor should infer hidden dynamics from feedback instead of receiving true
parameters directly. Privileged parameters are useful for the critic and for
teacher policies, but the deployed actor should not require them.

## Domain Randomization Targets

The current project already randomizes friction, mass scale, CG shift, tire
stiffness scale, actuator lag, speed targets, beta targets, and obstacle
geometry. M7 should extend this into a broader vehicle-family distribution:

- mass and yaw inertia;
- front/rear CG distribution;
- wheelbase and track width;
- maximum brake force;
- front/rear brake balance;
- front/rear tire stiffness and peak friction;
- tire relaxation or lag;
- steering rate limit and steering actuator delay;
- drive force delay and brake pressure delay;
- sensor noise and latency;
- split-mu and time-varying friction;
- road slope or external disturbances.

The goal is to make the policy learn feedback correction, not to memorize a
single nominal model.

## Benchmark Requirements

M7 must be evaluated on held-out combinations that were not used for training:

- light and heavy vehicles;
- front-heavy and rear-heavy vehicles;
- weak-brake and strong-brake vehicles;
- slow-steering and fast-steering vehicles;
- high-grip, low-grip, split-mu, and friction-step roads;
- obstacle cases where AEB is infeasible and conventional AES is marginal.

Report the same metrics as M5/M6, grouped by hidden vehicle and road buckets:

- success rate;
- collision rate;
- obstacle completion rate;
- minimum obstacle clearance;
- lateral RMSE and peak lateral error;
- sideslip error;
- speed;
- termination/spin/off-track rate.

The key claim should be narrow: the project should only claim a general operator
when the same actor succeeds on held-out vehicle and road families.

## Acceptance Criteria

M7 is successful when:

- the actor uses history or recurrence rather than only a single frame;
- previous action or actuator history is part of the actor's deployable input;
- the actor does not receive true friction, mass, CG, tire, or brake parameters
  at deployment time;
- the actor does not receive rule labels or controller-mode labels at deployment
  time;
- the same checkpoint outperforms AEB-only, heuristic AES, and model-based
  envelope baselines on held-out AEB-infeasible obstacle scenarios;
- the policy handles `aes_feasible` scenarios without unnecessary drift and
  handles `drift_required` scenarios when drift-like behavior is useful;
- low-friction and vehicle-variation failures are reported by bucket rather
  than hidden inside an aggregate score;
- ablations show that history, recurrence, or latent adaptation matters for
  held-out vehicle and road generalization;
- safety/fallback logic is clearly separated from the main RL controller.

## Current Status

The current M5 checkpoint is a task-specific prototype, not yet a universal
operator. It demonstrates that direct RL control can outperform AEB, heuristic
AES, and the friction-envelope AES baseline on the current `drift_required`
benchmark. M7-A/M7-B added history and action-history validation but did not
prove closed-loop self-identification. The next implementation step is M8:
temporal-GRU recurrent inference plus stable-AES reward shaping. See
`docs/m8-rl-professional-driver.md`.
