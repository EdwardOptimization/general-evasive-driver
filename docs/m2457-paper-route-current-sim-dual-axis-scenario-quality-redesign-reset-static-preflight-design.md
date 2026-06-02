# M2457 Paper-Route Current-Sim Dual-Axis Scenario-Quality Redesign Reset/Static Preflight Design

- status: completed
- decision: `reset_static_preflight_design_route_to_adapter_implementation`
- manifest: `experiments/manifests/m2457-paper-route-current-sim-dual-axis-scenario-quality-redesign-reset-static-preflight-design.json`
- parent audit: `docs/m2456-paper-route-current-sim-dual-axis-scenario-quality-redesign-protocol-materialization-result-audit.md`
- parent materialization: `runs/m2455_paper_route_current_sim_dual_axis_scenario_quality_redesign_protocol_materialization_preflight/summary.json`
- reset/rollout/policy action/scenario-redesign execution/repair/training/replay/PPO: `false`
- ranking/winner selection: `false`
- actual-success improvement/paper/FW-vs-GRU/level3 self-ID/scenario-redesign-executed/training-repair/current-sim verdict claims: `false`

## Design Summary

M2457 turns the M2455 protocol artifacts into a reset/static preflight design.
It does not execute the design.

The important boundary is that M2455 rows are protocol rows, not executable env
specs. They contain role, label bucket, hidden-dynamics bucket, timing bucket,
offset bucket, geometry lever class, and claim-boundary flags, but they do not
yet contain complete numeric scenario overlays such as obstacle distance range,
lateral offset range, half-width range, speed range, track width, or allowed
label filter.

Therefore the next implementation must be fail-closed:

```text
all M2455 rows can enter static schema/guardrail validation;
only rows with a concrete resolved env overlay can enter reset validation;
rows without numeric env overlays must be marked reset_blocked_missing_concrete_overlay;
no row may be promoted to measured rollout directly.
```

## Work-Item Schema

M2458 should materialize a `preflight_work_items.csv` table. Required fields:

```text
preflight_id
source_candidate_id
source_panel_id
candidate_group
role_scope
sampled_obstacle_label_scope
split
preflight_lane
intended_evidence_role
geometry_lever_class
boundary_protocol_class
static_check_required
reset_check_required
concrete_overlay_required
concrete_overlay_available
concrete_overlay_source
env_config_overlay_json
blocked_reason
labels_enter_actor_input
actor_input_contract_changed
scenario_redesign_executed
policy_action_executed
repair_execution_started
training_started
ranking_admissible
winner_selected
```

`preflight_lane` may be:

```text
static_only:
  schema, lineage, split, role, claim-boundary, and guardrail checks only.

static_then_reset:
  static checks plus environment construction and reset; no policy action.

reset_blocked:
  static checks are allowed, but reset is blocked because a concrete overlay is
  missing or unsafe.
```

The adapter must not infer hidden/oracle actor features from metadata. Fields
such as `sampled_obstacle_label_scope`, `hidden_dynamics_bucket`, and role
family are metadata only.

## Role Mapping

The role mapping is deterministic and non-ranking:

```text
stable_feasibility_support:
  role_scope: R0_stable_avoidable
  evidence role: stable road-contained obstacle-avoidance support
  reset lane: static_then_reset only after numeric obstacle geometry exists

stable_aes_support:
  role_scope: R1_aeb_infeasible_stable_aes
  evidence role: AEB-infeasible but stable AES support
  reset lane: static_then_reset only after numeric obstacle geometry exists

geometry_timing_guardrail:
  role_scope: geometry_timing_guardrail
  evidence role: timing and lateral-offset distribution guardrail
  reset lane: static_only unless a concrete overlay is explicitly attached

handling_limit_guardrail:
  role_scope: R2/R3/R5 handling-limit guardrail
  evidence role: preserve drift-required and recovery stress cases
  reset lane: static_only unless a later repair-plan route attaches overlays

hidden_dynamics_guardrail:
  role_scope: hidden-dynamics stress guardrail
  evidence role: preserve low_mu/weak_brake/slow_steer/tire-shift metadata
  reset lane: static_only unless a concrete hidden-condition env spec exists

mitigation_guardrail:
  role_scope: R4_unavoidable_mitigation
  evidence role: isolate unavoidable mitigation from success support
  reset lane: static_only unless a mitigation-specific eval spec is attached
```

The adapter may report group counts, but must not rank these roles or select a
winner.

## Allowed Config Overlay Keys

Only these non-actor config families may appear in a concrete reset overlay:

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

These keys control environment sampling and validation only. They do not enter
the actor observation. M2458 must reject any overlay that changes the actor input
shape or adds hidden/oracle actor fields.

## Static Checks

M2458 static validation should run for every work item:

```text
source files readable;
candidate_id unique;
candidate_group maps to a role_protocol row;
candidate split is public_debug or public_gate;
all required groups are nonempty;
all guardrail_rows.violation are false;
claim_boundary rows preserve blocked verdict claims;
labels_enter_actor_input is false;
actor_input_contract_changed is false;
scenario_redesign_executed is false;
policy_action_executed is false;
repair_execution_started is false;
training_started is false;
ranking_admissible is false;
winner_selected is false;
bounded geometry levers are true where applicable;
no private holdout, controller ranking, checkpoint ranking, or candidate-family ranking is introduced.
```

Static validation failure is a scenario-quality protocol failure, not a driver
performance result.

## Reset Checks

Reset validation is allowed only for `static_then_reset` items with
`concrete_overlay_available == true`.

Reset validation may:

```text
construct DriftEnvConfig from the resolved overlay;
instantiate the environment;
call reset with deterministic seeds;
verify observation shape remains unchanged;
verify obstacle sampling succeeds under configured filters;
record reset metadata and row-level failure text.
```

Reset validation must not:

```text
call policy inference;
step the environment with policy or heuristic actions;
execute measured rollout;
train, repair, replay, or run PPO;
rank candidates or select winners;
claim actual success, paper evidence, self-ID, FW-vs-GRU, training repair, or current-sim verdict.
```

Rows lacking concrete numeric overlays should be recorded as:

```text
preflight_lane: reset_blocked
blocked_reason: reset_blocked_missing_concrete_overlay
```

This is an expected fail-closed result, not a negative result about the driver.

## Output Contract For M2458

M2458 should write:

```text
summary.json
preflight_work_items.csv
static_check_rows.csv
reset_check_rows.csv
overlay_requirement_rows.csv
guardrail_rows.csv
claim_boundary.csv
decision_rows.csv
```

Required summary fields:

```text
source_candidate_row_count
preflight_work_item_count
static_check_pass_count
static_check_fail_count
reset_required_count
concrete_overlay_available_count
reset_attempted_count
reset_success_count
reset_blocked_missing_concrete_overlay_count
labels_enter_actor_input_count
actor_input_contract_changed_count
scenario_redesign_executed
policy_action_executed
repair_execution_started
training_started
ranking_admissible_count
winner_selected_count
guardrail_violation_count
result_class
next_blocker
```

The expected result class should distinguish static-only readiness from reset
readiness:

```text
scenario_quality_redesign_reset_static_preflight_adapter_static_pass_reset_blocked
scenario_quality_redesign_reset_static_preflight_adapter_reset_pass
scenario_quality_redesign_reset_static_preflight_adapter_fail
```

## Admission Criteria For Later Measured Rollout

Measured rollout remains blocked until a later audit verifies:

```text
static checks pass;
all reset-required work items either reset successfully or are explicitly out of scope;
actor observation shape is unchanged;
labels and hidden metadata remain actor-input blocked;
guardrail rows are nonviolating;
the measured workload denominator is explicit and non-ranking;
public_debug and public_gate splits are preserved;
no candidate family, controller family, profile, pack, or checkpoint winner is selected.
```

## Decision

Accepted next route:

```text
m2458-paper-route-current-sim-dual-axis-scenario-quality-redesign-reset-static-preflight-adapter-implementation
```

M2458 should implement the adapter and run it as preflight infrastructure only.
It may perform static checks and reset checks for concrete overlays, but it must
not execute rollout, policy actions, scenario redesign, repair, training,
ranking, winner selection, or verdict claims.
