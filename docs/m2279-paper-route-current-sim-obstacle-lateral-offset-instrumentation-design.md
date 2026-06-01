# M2279 Paper-Route Current-Sim Obstacle Lateral-Offset Instrumentation Design

- status: completed
- decision: `obstacle_lateral_offset_instrumentation_design_admit_implementation`
- manifest: `experiments/manifests/m2279-paper-route-current-sim-obstacle-lateral-offset-instrumentation-design.json`
- parent audit: `docs/m2278-paper-route-current-sim-scenario-task-family-config-materialization-result-audit.md`
- next route: `m2280-paper-route-current-sim-obstacle-lateral-offset-instrumentation-implementation`

## Purpose

M2279 designs the current-sim instrumentation needed to execute the M2277
scenario task-family pack without silently approximating left/right emergency
obstacles as centerline obstacles.

This milestone is design-only. It does not run reset, rollout, measured
execution, policy actions, training, replay, PPO, private holdout, promotion,
ranking, paper-level claims, finite-window-vs-GRU conclusions, or level3 self-ID
claims.

## Field Semantics

Add a backward-compatible field to `ObstacleTaskConfig`:

```python
lateral_offset_range: tuple[float, float] = (0.0, 0.0)
```

Semantics:

```text
0.0:
  obstacle centered on the reference path, identical to current behavior

positive value:
  obstacle shifted along frame normal-left at reset

negative value:
  obstacle shifted along frame normal-right at reset
```

Validation:

```text
lateral_offset_range must be a two-element numeric range
upper >= lower
values may be negative, zero, or positive
```

No actor observation dimension changes are allowed. The actor already receives
ego-frame obstacle geometry; lateral offset changes scenario geometry, not the
input contract.

## Config Builder

`build_env_config` already handles obstacle keys ending in `_range`. After the
dataclass field exists, existing config parsing should accept:

```json
{
  "obstacle": {
    "lateral_offset_range": [-1.2, -1.2]
  }
}
```

Default configs that omit the field must continue to produce centerline
obstacles.

## Reset Placement

Update `_reset_obstacle` so it samples:

```python
obstacle_distance = uniform(distance_range)
obstacle_lateral_offset = uniform(lateral_offset_range)
obstacle_half_width = uniform(half_width_range)
```

and places the emergency obstacle as:

```python
normal_left = np.array([-frame.tangent[1], frame.tangent[0]])
obstacle_position = (
    position
    + frame.tangent * obstacle_distance
    + normal_left * obstacle_lateral_offset
)
```

This mirrors the existing warmup gate lateral-offset placement and preserves the
centerline default when `lateral_offset_range == (0.0, 0.0)`.

## Info And Observation Effects

Existing info and observation paths should remain structurally unchanged:

```text
_obstacle_path_features:
  already computes lateral offset from obstacle_position

_info["obstacle_lateral_offset"]:
  already reports obstacle_path[1] * track_width

obstacle slots:
  already expose ego-frame x/y obstacle geometry
```

Therefore M2280 should not add any actor-input dimension or new oracle field.
It should only make existing geometry reflect the configured lateral offset.

## Classifier Semantics

`classify_obstacle_scenario` can remain unchanged in M2280. It classifies the
obstacle by speed, friction, longitudinal distance, and half-width. Lateral
offset affects actual geometry and later reset/rollout outcomes, but M2280 is
instrumentation, not a paper-level task validity claim.

Follow-up audits must still check whether generated left/right specs are
meaningful and balanced before ranking or training.

## Materializer Update

M2280 should update
`paper_route_current_sim_scenario_task_family_config_materialization.py` so that
left/right rows emit:

```text
env_config["obstacle"]["lateral_offset_range"] = (offset, offset)
env_config_supported = true
execution_blocked_by_unsupported_capability = false
```

Expected post-implementation materializer result:

```text
unsupported_execution_blocker_count: 0
execution_admissible_without_instrumentation: true
silent_unsupported_approximation_count: 0
```

Future fault rows should remain unsupported nonblocking rows.

## M2280 Test Plan

M2280 may run reset-only unit tests because it is simulator instrumentation.
It must not execute policy actions or measured rollouts.

Required focused tests:

```text
1. build_env_config accepts obstacle.lateral_offset_range.
2. default ObstacleTaskConfig has lateral_offset_range == (0.0, 0.0).
3. default centerline reset behavior remains near zero lateral offset.
4. fixed positive lateral_offset_range produces positive info["obstacle_lateral_offset"].
5. fixed negative lateral_offset_range produces negative info["obstacle_lateral_offset"].
6. observation dimension and actor contract stay unchanged.
7. M2277 materializer rerun emits obstacle.lateral_offset_range in env_config and reduces unsupported_execution_blocker_count to 0.
```

Allowed M2280 reset usage:

```text
env.reset() only in focused instrumentation tests
no policy step loop
no policy action execution
no measured rollout
no training
```

## Blocked Routes

Blocked after M2279:

```text
reset validation of the scenario pack before M2280 implementation
rollout or measured execution
training
controller-family ranking
winner selection
finite-window-vs-GRU verdict
paper-level result
level3 self-identification
high-fidelity validation as a replacement for current-sim instrumentation
```

## Next

Pre-register:

```text
m2280-paper-route-current-sim-obstacle-lateral-offset-instrumentation-implementation
```
