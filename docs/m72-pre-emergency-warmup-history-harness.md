# M72 Pre-Emergency Warm-Up History Harness

M71 showed that passive matched snapshots still do not produce causal
wrong-history outcome gaps. M72 starts the next proof surface: let the recurrent
driver collect action-response evidence before the obstacle becomes visible.

## Goal

Create a gate where the policy has a warm-up phase with randomized hidden
dynamics, then enters an emergency avoidance phase. The deployable actor must
still see only human-view inputs.

Target comparison:

```text
normal warm-up history
wrong matched warm-up history
reset history
zero action history
zero response history
```

Pass evidence should be outcome-level:

```text
normal history success or clearance margin
  >
wrong/reset/zero-history success or clearance margin
```

under strict visible-state matching.

## M72-A: Obstacle Perception Reveal Infrastructure

Added obstacle perception reveal controls to `ObstacleTaskConfig`:

```text
perception_reveal_step
perception_reveal_distance
```

Behavior:

- the obstacle still exists physically from reset;
- collision, clearance, scenario labels, and logging remain available;
- actor obstacle slots stay zero until the reveal conditions pass;
- observation dimension and slot layout remain unchanged.

This supports a controlled warm-up phase without changing the actor contract.
The driver can experience vehicle response first, then see the obstacle later.

## Tests

Focused tests cover:

```text
obstacle slots are hidden before reveal
step and distance reveal conditions work
config loader accepts reveal fields
existing obstacle observation behavior remains visible by default
```

Validation command:

```text
conda run -n autodrift pytest -q tests/test_env.py tests/test_config.py
```

Result:

```text
33 passed
```

## Next Step

Build the actual M72 gate:

```text
collect warm-up snapshots with obstacle hidden
reveal obstacle at matched emergency geometry
swap normal and wrong matched warm-up recurrent histories
replay normal/reset/zero/wrong-history variants
accept only outcome-sensitive cases
```

The M72 gate should reuse M71's outcome-sensitive acceptance logic where
possible, but its snapshot source should be warm-up history rather than passive
same-obstacle rollouts.
