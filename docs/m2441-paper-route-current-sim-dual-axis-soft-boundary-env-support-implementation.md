# M2441 Paper-Route Current-Sim Dual-Axis Soft-Boundary Env Support Implementation

- status: completed
- result_class: `soft_boundary_env_support_implementation_pass`
- manifest: `experiments/manifests/m2441-paper-route-current-sim-dual-axis-soft-boundary-env-support-implementation.json`
- implementation: `src/autodrift/env.py`
- focused tests: `4 passed`
- test file: `tests/test_soft_boundary_env_support.py`
- new measured rollout/reset/repair/training/replay/PPO: `false`
- actual success improvement claim: `false`
- candidate/controller ranking and winner selection: `false`
- paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Implementation Result

M2441 added opt-in soft-boundary support to `DriftEnvConfig`:

```text
soft_offtrack_metric_enabled: bool = false
soft_offtrack_tolerance_m: float = 0.0
```

Default behavior is preserved:

```text
soft_offtrack_metric_enabled == false
and lateral overshoot > 0
=> termination_reason == off_track
```

Enabled behavior:

```text
soft_offtrack_metric_enabled == true
and 0 < lateral overshoot <= soft_offtrack_tolerance_m
=> soft_offtrack_violation == true
=> no off_track termination from boundary alone

soft_offtrack_metric_enabled == true
and lateral overshoot > soft_offtrack_tolerance_m
=> hard_offtrack_failure == true
=> termination_reason == off_track
```

## Added Diagnostics

`info` now includes:

```text
soft_offtrack_metric_enabled
soft_offtrack_tolerance_m
off_track_overshoot
max_off_track_overshoot_env
soft_offtrack_violation
soft_offtrack_step_count
soft_offtrack_duration_s
first_soft_offtrack_step
hard_offtrack_failure
metric_selected_termination_reason
```

These are logging/metric diagnostics. They do not enter actor observation.

## Focused Tests

```text
tests/test_soft_boundary_env_support.py
```

Covered:

```text
default offtrack termination is unchanged;
soft-boundary enabled mode continues inside tolerance;
soft-boundary enabled mode terminates beyond tolerance;
observation_space shape is unchanged;
soft-boundary diagnostics accumulate during step.
```

Focused test result:

```text
4 passed
```

## Contract Boundary

Preserved:

```text
actor observation shape
human-view/no-oracle actor input contract
default offtrack termination behavior
existing action space
existing reward path except that enabled soft-boundary mode does not terminate
inside tolerance
```

Not claimed:

```text
measured validation success
actual success improvement
scenario redesign execution
controller-family ranking
candidate-family ranking
current-sim verdict
paper-level result
self-ID evidence
```

## Next Step

Next milestone:

```text
m2442-paper-route-current-sim-dual-axis-task-boundary-metric-redesign-branch-synthesis
```

M2442 should synthesize the M2437-M2441 task-boundary metric redesign branch
because the local-search guard blocks another ordinary result audit. It must
not run measured validation, repair, training, ranking, or verdict claims.
