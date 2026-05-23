# M493 Natural Belief Decision-Window Redesign

## Purpose

M493 closes the M486-M492 artificial tail-forcing branch and redirects the
research path toward a natural belief decision-window task.

No training, PPO, actor-input change, checkpoint update, proof expansion, or
checkpoint promotion is performed.

## Why Close The Tail-Forcing Branch

The recent branch established useful mechanism evidence:

```text
M487 natural wrong_tail_once:      11 proof rows, 0 event rows
M488 mechanism audit:             wrong-tail trajectory mean only 0.068261
M490 hidden-hold diagnostic:      90 proof rows, 4 event rows
M492 observer action replay:      21 proof rows, 1 event row
```

Interpretation:

```text
wrong initial hidden state is not ignored;
the actor corrects it quickly from current response;
forcing wrong hidden for multiple steps can break behavior;
forcing the wrong physical action prefix alone mostly does not.
```

That is evidence about the recurrent mechanism, but it is not deployable
self-identification proof. Continuing to add stronger artificial hidden/action
forcing on the same M486 surface would mostly test intervention strength, not
natural closed-loop belief use.

## New Research Question

The next task family should ask:

```text
Can natural command-response history affect the emergency decision before
current-response observations have enough time to correct a wrong belief?
```

This is different from M487-M492. Instead of injecting wrong hidden state at a
tail point, the environment should create natural episodes where:

```text
1. hidden dynamics are randomized before the emergency;
2. the policy receives a short warm-up / response-evidence phase;
3. obstacle geometry becomes decision-critical late;
4. the first few actions after reveal have high terminal leverage;
5. matched-current rows can compare histories that look similar now but imply
   different vehicle capability.
```

## Design Principles

Keep the P0 actor contract:

```text
ego/IMU-like response
actuator states
previous physical commands
ego-frame road/free-space/obstacle geometry
online recurrent hidden from past command-response history
```

Do not add:

```text
mu
tire/slip/friction oracle features
AEB/AES/drift-required labels
TTC
required clearance
reference trajectory
controller mode
```

The task may randomize hidden dynamics and obstacle geometry, but the actor
must still only receive deployable P0 observations.

## Proposed M494 Config Family

M494 should implement and sampling-validate two candidate configs before any
proof mining.

### 1. Short-Reveal Decision Window

Goal: obstacle appears late enough that the first few post-reveal actions matter
more than later correction.

Starting from M484 late high-energy, make it slightly more decision-critical:

```text
track_width: 7.4 to 7.8
speed_range: [13.8, 18.0]
obstacle.distance_range: [4.5, 20.0]
obstacle.perception_reveal_distance: 6.0 to 7.0
obstacle.half_width_range: [0.70, 1.45]
obstacle.max_threshold_score: 0.45 to 0.60
friction_step.step_range: [4, 28]
obstacle.min_time_after_friction_step: 0.25 to 0.50
```

### 2. Warm-Up Capability Evidence

Goal: ensure the actor has time to feel hidden dynamics before obstacle reveal,
but not enough time after reveal to fully re-identify.

Starting from M484 near-threshold, preserve sampling robustness but add a
clearer response-evidence window:

```text
track_width: 7.6 to 8.0
speed_range: [12.8, 17.6]
obstacle.distance_range: [7.0, 24.0]
obstacle.perception_reveal_distance: 7.0 to 9.0
obstacle.half_width_range: [0.60, 1.35]
obstacle.max_threshold_score: 0.30 to 0.50
friction_step.step_range: [4, 30]
obstacle.min_time_after_friction_step: 0.35 to 0.70
```

Both configs should keep:

```text
obstacle_relative_velocity_mode: zero
allowed_labels: aes_feasible, drift_required, unavoidable
require_aeb_infeasible: true
randomized mu/mass/cg/tire/brake/actuator ranges
```

## M494 Sampling Validation

M494 is config validation only. It should not mine proof rows until sampling is
stable.

Use seed blocks:

```text
11800
11900
12000
```

For each config:

```text
128 reset attempts per seed block
384/384 reset successes required
at least 2 obstacle labels
single-label share <= 0.80
hidden-at-reset or late-reveal count reported
friction-step-before-reveal count reported if available
```

Then run tiny behavior smokes:

```text
M399 normal
M399 reset-hidden
M399 zero-current
heuristic
random
```

The smokes are not proof gates. They only check that the config is runnable,
nontrivial, and not saturated.

## M495 If M494 Passes

If at least one config passes sampling and smoke validation, M495 should run
natural matched-current mining:

```text
matched current ego/scene at the decision window
different pre-reveal command-response histories
no hidden/action forcing
wrong-history and reset/zero-current only as diagnostics
outcome gate measured within short post-reveal horizon
```

Acceptance criteria should prioritize:

```text
source-diverse rows
normal natural rollout near-boundary
wrong-history/reset/zero-current degradation without manual hidden hold
event rows over margin-only rows
```

## Decision

```text
admit_m494_natural_belief_decision_config_implementation
```

M494 should implement the two config candidates and run sampling plus behavior
smokes. No proof mining or training until config robustness is known.
