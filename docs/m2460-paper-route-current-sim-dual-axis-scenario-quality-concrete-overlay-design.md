# M2460 Paper-Route Current-Sim Dual-Axis Scenario-Quality Concrete Overlay Design

- status: completed
- decision: `concrete_overlay_design_route_to_materialization_preflight`
- manifest: `experiments/manifests/m2460-paper-route-current-sim-dual-axis-scenario-quality-concrete-overlay-design.json`
- parent audit: `docs/m2459-paper-route-current-sim-dual-axis-scenario-quality-redesign-reset-static-preflight-adapter-result-audit.md`
- parent summary: `runs/m2458_paper_route_current_sim_dual_axis_scenario_quality_redesign_reset_static_preflight_adapter/summary.json`
- reset/rollout/policy action/scenario-redesign execution/repair/training/replay/PPO: `false`
- ranking/winner selection: `false`
- actual-success improvement/paper/FW-vs-GRU/level3 self-ID/scenario-redesign-executed/training-repair/current-sim verdict claims: `false`

## Problem

M2458 proved the M2455 protocol rows are static-valid, but reset validation is
blocked for the six stable/AES support rows:

```text
reset_required_count: 6
concrete_overlay_available_count: 0
reset_blocked_missing_concrete_overlay_count: 6
```

The missing fields are numeric scenario overlays, not policy changes:

```text
obstacle.distance_range
obstacle.lateral_offset_range
obstacle.half_width_range
speed_range
```

## Design Principle

M2460 designs only the numeric overlay contract needed for reset preflight.
Labels such as `aeb_feasible` and `aes_feasible` may be used as environment
sampling filters and artifact metadata, but must remain outside actor input.

Allowed overlay keys:

```text
track_width
soft_offtrack_metric_enabled
soft_offtrack_tolerance_m
speed_range
friction_limited_speed
obstacle.enabled
obstacle.distance_range
obstacle.lateral_offset_range
obstacle.half_width_range
obstacle.allowed_labels
obstacle.require_aeb_infeasible
obstacle.max_threshold_score
obstacle.perception_reveal_distance
obstacle.perception_reveal_step
obstacle.finish_on_pass
obstacle.finish_pass_distance
obstacle.max_sample_attempts
```

Forbidden in M2460/M2461 overlays:

```text
hidden dynamics randomization ranges
mu or tire/brake/actuator oracle actor features
path/TTC/reference features
controller-specific filters
candidate ranking or winner flags
unbounded per-row tuning after reset outcomes are known
```

## Overlay Families

M2461 should materialize two overlay families, each applied to the three
matching reset-blocked work items from M2458.

### R0 Stable Avoidable Overlay

Purpose:

```text
basic stable, road-contained, AEB-feasible obstacle support
```

Overlay:

```json
{
  "track_width": 7.5,
  "speed_range": [8.0, 12.0],
  "friction_limited_speed": false,
  "soft_offtrack_metric_enabled": true,
  "soft_offtrack_tolerance_m": 0.20,
  "obstacle": {
    "enabled": true,
    "distance_range": [34.0, 52.0],
    "lateral_offset_range": [-0.25, 0.25],
    "half_width_range": [0.45, 0.65],
    "allowed_labels": ["aeb_feasible"],
    "require_aeb_infeasible": false,
    "max_sample_attempts": 10000,
    "perception_reveal_step": 0,
    "perception_reveal_distance": 70.0,
    "finish_on_pass": true,
    "finish_pass_distance": 1.0
  }
}
```

Rationale:

```text
early/far obstacle timing and moderate speed support stable completion;
centerline/narrow obstacle sampling supports braking or mild steering;
track width gives road-contained recovery room without removing road bounds;
allowed_labels remains sampling metadata only.
```

### R1 Stable AES Overlay

Purpose:

```text
AEB-infeasible but stable steering avoidance support
```

Overlay:

```json
{
  "track_width": 7.5,
  "speed_range": [10.0, 14.0],
  "friction_limited_speed": false,
  "soft_offtrack_metric_enabled": true,
  "soft_offtrack_tolerance_m": 0.20,
  "obstacle": {
    "enabled": true,
    "distance_range": [20.0, 34.0],
    "lateral_offset_range": [-0.40, 0.40],
    "half_width_range": [0.55, 0.80],
    "allowed_labels": ["aes_feasible"],
    "require_aeb_infeasible": true,
    "max_threshold_score": 0.35,
    "max_sample_attempts": 10000,
    "perception_reveal_step": 0,
    "perception_reveal_distance": 55.0,
    "finish_on_pass": true,
    "finish_pass_distance": 1.0
  }
}
```

Rationale:

```text
mid obstacle timing keeps AEB infeasibility meaningful without forcing drift;
moderate obstacle width and balanced lateral offsets support stable steering;
max_threshold_score bounds sampling difficulty without becoming actor input;
soft-boundary metrics remain diagnostic until fresh execution proves completion.
```

## Guardrail Treatment

M2461 must not attach performance overlays to these groups yet:

```text
geometry_timing_guardrail
handling_limit_guardrail
hidden_dynamics_guardrail
mitigation_guardrail
```

They remain static-only guardrails in this branch. Later branches may design
handling-limit, hidden-dynamics, or mitigation overlays, but not as part of the
stable/AES reset unblocker.

## M2461 Output Contract

M2461 should write:

```text
summary.json
concrete_overlay_rows.csv
candidate_rows_with_overlays.csv
adapter_summary.json
adapter_preflight_work_items.csv
adapter_static_check_rows.csv
adapter_reset_check_rows.csv
guardrail_rows.csv
claim_boundary.csv
decision_rows.csv
```

Required `concrete_overlay_rows.csv` fields:

```text
overlay_id
preflight_id
source_candidate_id
candidate_group
overlay_family
env_config_overlay_json
allowed_labels_metadata_only
labels_enter_actor_input
actor_input_contract_changed
scenario_redesign_executed
policy_action_executed
repair_execution_started
training_started
ranking_admissible
winner_selected
```

Pass criteria for M2461:

```text
six reset-blocked stable/AES work items receive concrete overlays;
all overlay keys are in the allowed set;
adapter static checks pass with zero guardrail violations;
adapter concrete_overlay_available_count is 6;
reset execution remains disabled until a later audit admits it;
no policy action, rollout, repair, training, ranking, winner, or verdict claim.
```

## Decision

Accepted next route:

```text
m2461-paper-route-current-sim-dual-axis-scenario-quality-concrete-overlay-materialization-preflight
```

M2461 should materialize the concrete overlay rows and run the M2458 adapter in
preflight mode over the overlay-augmented candidate table. It must not execute
reset, rollout, policy actions, scenario redesign, repair, training, ranking,
winner selection, or verdict claims.
