# M1949 Executable V2 Task-Quality Offtrack Support Repair Anchor Fallback Geometry Calibration Design

- status: completed
- decision: `task_quality_anchor_fallback_geometry_calibration_design_admit_implementation`
- branch: `paper_route_task_quality_offtrack_support_repair`
- parent audit: `docs/m1948-executable-v2-task-quality-offtrack-support-repair-source-mining-result-audit.md`
- reset/rollout/measured execution in M1949: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Purpose

M1948 localized the M1947 failure to stable-AEB anchor fallback geometry. The
fallback geometry produced `aes_feasible` source labels, while the anchor rows
require `aeb_feasible`. M1949 designs a bounded no-rollout calibration step for
that fallback. It does not rerun M1947 source mining and does not relax the
stable-AEB label gate.

The calibration target is narrow:

```text
tier_c_boundary_near_miss / stable_aeb / aeb_feasible
```

The output should be a calibrated fallback artifact that later source-mining
can consume.

## Inputs

M1950 should read:

```text
configs/executable_v2_task_quality_offtrack_support_repair_candidates_v0.json
runs/m1947_executable_v2_task_quality_offtrack_support_repair_source_mining/repair_blocked_rows.csv
runs/m1947_executable_v2_task_quality_offtrack_support_repair_source_mining/source_kind_aggregate.csv
```

It may also read M1947 `repair_source_rows.csv` for diagnostics, but it must
not depend on environment reset, environment rollout, policy action execution,
or measured rollout.

## Calibration Scope

Rows eligible for calibration:

```text
repair_source_kind == anchor_neighborhood
source_role_semantics == stable_aeb
sampled_obstacle_label == aeb_feasible
source_support_failure_reason == label_role_mismatch
dominant_label == aes_feasible
```

M1947 has `64` such rows split across two surface variants:

```text
post_friction_step
steady_surface
```

The calibration may choose one fallback per surface variant, because the
source-mining adapter already treats `post_friction_step` and `steady_surface`
differently.

## Candidate Search

M1950 should use the existing no-rollout source classifier primitives:

```text
required_label_for_role
evaluate_candidate_cell
scan_candidate_profile
classify_obstacle_scenario
```

Candidate dimensions:

```text
speed_ref: preserve template speed_ref, normally 18.0
mu: preserve template mu, normally 0.40
base_obstacle_distance: bounded grid, e.g. 36.0 to 80.0
base_obstacle_half_width: bounded grid, e.g. 0.30 to 1.00
base_track_width: preserve M1946 default unless a row explicitly supplies it
surface_variant: post_friction_step or steady_surface
```

For each candidate fallback, apply the original M1945 repair deltas and the
M1946 anchor scan window:

```text
obstacle_distance_center =
  base_obstacle_distance + obstacle_distance_delta

obstacle_half_width_center =
  max(0.10, base_obstacle_half_width + obstacle_half_width_delta)

anchor scan:
  obstacle_distance_center +/- 4.0, count 9
  obstacle_half_width_center +/- 0.15, count 7
```

The calibration should score each fallback by:

```text
supported_anchor_count
accepted_cell_count_total
surface_balance
center_label_correct_count
distance_from_old_default
```

The primary feasibility rule is label correctness, not proximity to the old
default. Do not accept a geometry whose center or support rows remain
dominated by `aes_feasible` for stable-AEB anchors.

## Outputs

M1950 should write:

```text
runs/m1950_executable_v2_task_quality_offtrack_support_repair_anchor_fallback_geometry_calibration/summary.json
runs/m1950_executable_v2_task_quality_offtrack_support_repair_anchor_fallback_geometry_calibration/anchor_fallback_candidates.csv
runs/m1950_executable_v2_task_quality_offtrack_support_repair_anchor_fallback_geometry_calibration/anchor_calibration_source_rows.csv
runs/m1950_executable_v2_task_quality_offtrack_support_repair_anchor_fallback_geometry_calibration/anchor_calibration_accepted_cells.csv
runs/m1950_executable_v2_task_quality_offtrack_support_repair_anchor_fallback_geometry_calibration/anchor_calibration_blocked_rows.csv
runs/m1950_executable_v2_task_quality_offtrack_support_repair_anchor_fallback_geometry_calibration/selected_anchor_fallback_geometry.json
runs/m1950_executable_v2_task_quality_offtrack_support_repair_anchor_fallback_geometry_calibration/claim_boundary.csv
```

`selected_anchor_fallback_geometry.json` should contain explicit keys for the
two calibrated surfaces:

```text
tier_c_boundary_near_miss::stable_aeb::aeb_feasible::post_friction_step
tier_c_boundary_near_miss::stable_aeb::aeb_feasible::steady_surface
```

Each selected entry should include:

```text
speed_ref
mu
obstacle_distance
obstacle_half_width
base_track_width
surface_variant
source_role_semantics
required_label
center_label
supported_anchor_count
accepted_cell_count_total
```

## Pass Gates

M1950 calibration passes only if:

```text
result_class == task_quality_anchor_fallback_geometry_calibration_pass
input_anchor_template_count == 64
blocked_anchor_row_count == 64
selected_surface_count == 2
selected_surfaces include post_friction_step and steady_surface
selected_required_label == aeb_feasible for every selected fallback
selected_center_label == aeb_feasible for every selected fallback
selected_supported_anchor_count_total >= 32
selected_supported_anchor_count_by_surface >= 16 for each surface
selected_accepted_cell_count_total > 0
labels_enter_actor_input_count == 0
profile_specific_tuning_count == 0
guardrail_violation_count == 0

environment_reset_started == false
environment_rollout_started == false
policy_action_executed == false
measured_rollout_started == false
training_started == false
replay_started == false
ppo_used == false
promoted == false
private_holdout_used == false
actor_input_contract_changed == false
controller_family_ranking_claim_made == false
paper_level_claim_made == false
level3_self_id_claim_made == false
```

If the selected supported-anchor count is below these floors, M1950 should fail
closed and route to synthesis or broader scenario redesign, not weaken the
stable-AEB label contract.

## Follow-Up If Calibration Passes

If M1950 passes, the next milestone should apply the calibrated fallback
artifact to the M1947 source-mining adapter and rerun the no-rollout
source-mining step. That later rerun should keep the original source-kind gates:

```text
anchor_neighborhood_supported_source_count >= 16
success_stabilizer_supported_source_count >= 16
offtrack_boundary_relief_supported_source_count >= 8
mitigation_isolation_check_source_count == 16
```

The rerun should remain non-ranking and non-paper evidence until reset and
measured execution have been separately validated.

## Unsupported Claims

M1949 does not support:

- offtrack support repair success;
- reset validity;
- measured execution readiness;
- controller-family ranking;
- finite-window vs GRU conclusion;
- paper-level benchmark result;
- level3 self-identification.

## Next

Next milestone:

```text
m1950-executable-v2-task-quality-offtrack-support-repair-anchor-fallback-geometry-calibration-implementation
```

M1950 should implement and run the calibration only. It should not reset
environments, run measured episodes, train, replay, use PPO, or promote any
checkpoint.
