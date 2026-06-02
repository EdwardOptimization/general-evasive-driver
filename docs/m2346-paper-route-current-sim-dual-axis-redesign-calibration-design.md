# M2346 Paper-Route Current-Sim Dual-Axis Redesign Calibration Design

- status: completed
- result_class: `dual_axis_redesign_calibration_design_admit_artifact_only_materializer`
- manifest: `experiments/manifests/m2346-paper-route-current-sim-dual-axis-redesign-calibration-design.json`
- parent synthesis: `docs/m2345-paper-route-current-sim-scenario-support-redesign-branch-synthesis.md`
- parent artifacts: `runs/m2343_paper_route_current_sim_scenario_support_redesign_consolidation`
- admitted follow-up: `artifact-only materializer`
- reset/rollout/policy action in M2346: `false`
- measured execution in M2346: `false`
- training/replay/PPO in M2346: `false`
- support-policy ranking claim made: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- paper-level claim made: `false`
- finite-window vs GRU conclusion made: `false`
- level3 self-ID claim made: `false`

## Purpose

M2345 stops the direct single-axis redesign route because M2343 exposes an
exact split:

```text
geometry_timing_rebalance_candidate: 13
hidden_dynamics_range_rebalance_candidate: 13
secondary coverage-materialization rows: 9
```

M2346 designs a bounded calibration plan for a future artifact-only materializer.
It does not edit the active scenario pack, run rollouts, train policies, rank
support policies, or claim that the scenario redesign has been executed.

## Inputs For M2347

The materializer should read:

```text
runs/m2343_paper_route_current_sim_scenario_support_redesign_consolidation/consolidated_redesign_rows.csv
runs/m2343_paper_route_current_sim_scenario_support_redesign_consolidation/secondary_coverage_materialization_rows.csv
runs/m2343_paper_route_current_sim_scenario_support_redesign_consolidation/redesign_route_summary.csv
docs/m2346-paper-route-current-sim-dual-axis-redesign-calibration-design.md
```

Reference config, read-only:

```text
configs/paper_route_current_sim_scenario_task_family_v0.json
```

The implementation must treat these as artifact inputs. It must not reset the
environment, execute policy actions, run replay, or overwrite the active config.

## Calibration Principles

The materializer should preserve the actor contract:

```text
actor_contract_id == P0_human_view_no_wheel_no_oracle
```

No candidate may introduce hidden parameters, feasibility labels, TTC, reference
trajectory, path error, heading error, slip, tire force, friction margin, success
labels, or controller mode into actor input.

The calibration is a candidate-set design, not a ranking. A row may produce
multiple candidate patches, but M2347 should only materialize them and record
their intent. Later measured validation can decide whether any candidate is
usable.

## Axis G: Geometry And Timing

Rows routed to `geometry_timing_rebalance_candidate` should receive bounded
geometry/timing candidates. The allowed transformations are:

```text
timing_step_earlier:
  late_close -> mid
  mid -> early_far only when the row is collision-dominated and centerline

speed_step_down:
  reduce initial_speed_mps by one existing-pack speed step, never below the
  nearest lower speed already represented in the role family

lateral_offset_step_toward_centerline:
  left_offset/right_offset -> reduced-offset candidate or centerline-neighbor
  metadata candidate, preserving the original direction in provenance

track_width_step_up:
  for offtrack-dominated rows, propose the next existing broader track-width
  bucket when the role family already contains it; otherwise record as
  unavailable rather than inventing an unbounded width

radius_step_up:
  optional only when track_radius_m has a known adjacent easier bucket in the
  source config; otherwise record as unavailable
```

Recommended mapping:

```text
collision_timing_pressure:
  primary candidate: timing_step_earlier
  secondary candidate: speed_step_down

offtrack_geometry_pressure:
  primary candidate: lateral_offset_step_toward_centerline
  secondary candidate: track_width_step_up

late_close + lateral offset:
  emit both a timing candidate and a lateral candidate, but do not combine them
  unless the row is also GH-eligible.
```

## Axis H: Hidden-Dynamics Range

Rows routed to `hidden_dynamics_range_rebalance_candidate` should receive
bounded hidden-range candidates. The materializer should work at bucket/metadata
level unless the source config exposes an explicit adjacent range. The allowed
transformations are:

```text
low_mu_step_toward_nominal:
  low_mu -> one less severe low-friction bucket or nominal-neighbor candidate

weak_brake_step_toward_nominal:
  weak_brake -> one less severe brake-scale bucket or nominal-neighbor candidate

slow_steer_actuator_step_toward_nominal:
  slow_steer_actuator -> one less severe actuator-lag bucket or nominal-neighbor
  candidate

tire_stiffness_step_toward_nominal:
  tire_stiffness_shift -> one less severe tire-stiffness bucket or
  nominal-neighbor candidate

same_scene_hidden_balance:
  for R5 hidden-dynamics robustness rows, preserve same_scene_group_id and
  propose a balanced hidden-bucket panel rather than changing geometry first
```

The H axis must not erase hidden-dynamics stress entirely. It should propose
one-step range calibration so later validation can ask whether the task family
is too extreme, not whether the project can avoid hard hidden dynamics.

## Axis GH: Minimal Combined Candidates

Combined candidates are allowed only when a row carries both geometry/timing and
hidden-dynamics stress signals:

```text
eligible if:
  recommended_redesign_route is geometry_timing_rebalance_candidate
  and hidden_dynamics_bucket is low_mu, weak_brake, slow_steer_actuator, or
      tire_stiffness_shift
  and redesign_theme is collision_timing_pressure or offtrack_geometry_pressure

or:
  recommended_redesign_route is hidden_dynamics_range_rebalance_candidate
  and obstacle_longitudinal_timing_bucket is late_close
  and dominant_failure_mode is collision_dominated_failure
```

For GH candidates:

```text
apply at most one G transform and one H transform;
prefer the primary transform from each axis;
set combined_candidate_reason explicitly;
do not mark the original row solved;
do not make ranking or controller-comparison claims.
```

## Secondary Coverage Rows

The 9 `support_policy_coverage_materialization_candidate` rows remain tracked
but inactive:

```text
copy to secondary_coverage_rows.csv;
set active_for_calibration = false;
set blocked_by = dual_axis_redesign_calibration_not_materialized;
do not materialize support-policy coverage candidates in M2347.
```

This keeps the source-mapping result intact without mixing support-policy
coverage materialization into scenario redesign calibration.

## M2347 Output Schema

The materializer should write:

```text
runs/m2347_paper_route_current_sim_dual_axis_redesign_calibration_materialization/summary.json
runs/m2347_paper_route_current_sim_dual_axis_redesign_calibration_materialization/calibration_candidate_rows.csv
runs/m2347_paper_route_current_sim_dual_axis_redesign_calibration_materialization/geometry_timing_candidate_rows.csv
runs/m2347_paper_route_current_sim_dual_axis_redesign_calibration_materialization/hidden_range_candidate_rows.csv
runs/m2347_paper_route_current_sim_dual_axis_redesign_calibration_materialization/combined_axis_candidate_rows.csv
runs/m2347_paper_route_current_sim_dual_axis_redesign_calibration_materialization/secondary_coverage_rows.csv
runs/m2347_paper_route_current_sim_dual_axis_redesign_calibration_materialization/calibration_config_candidates.json
runs/m2347_paper_route_current_sim_dual_axis_redesign_calibration_materialization/claim_boundary.csv
```

Candidate row columns:

```text
scenario_spec_id
candidate_id
candidate_axis
source_recommended_route
role_family
scenario_family_id
same_scene_group_id
hidden_dynamics_bucket_before
hidden_dynamics_bucket_after
timing_bucket_before
timing_bucket_after
lateral_bucket_before
lateral_bucket_after
initial_speed_mps_before
initial_speed_mps_after
track_width_m_before
track_width_m_after
track_radius_m_before
track_radius_m_after
transform_name
transform_reason
combined_candidate_reason
active_for_materialization
diagnostic_only
ranking_admissible
winner_selected
paper_level_claim_made
level3_self_id_claim_made
```

Required summary fields:

```text
input_redesign_row_count
geometry_timing_input_row_count
hidden_range_input_row_count
secondary_coverage_input_row_count
geometry_timing_candidate_count
hidden_range_candidate_count
combined_axis_candidate_count
secondary_coverage_tracked_count
rows_without_candidate_count
guardrail_violation_count
environment_reset_started
environment_rollout_started
measured_rollout_started
training_started
replay_started
ppo_used
support_policy_ranking_claim_made
controller_family_ranking_claim_made
winner_selected
paper_level_claim_made
finite_window_vs_gru_conclusion_made
level3_self_id_claim_made
scenario_redesign_executed_claim_made
```

## Acceptance Criteria For M2347

M2347 should pass if:

```text
input_redesign_row_count == 26
geometry_timing_input_row_count == 13
hidden_range_input_row_count == 13
secondary_coverage_input_row_count == 9
secondary_coverage_tracked_count == 9
rows_without_candidate_count == 0
guardrail_violation_count == 0
all required artifacts exist
```

The materializer must fail closed if:

```text
required columns are missing;
axis counts differ from 13/13;
secondary coverage rows are activated;
candidate transforms introduce actor-contract shortcuts;
any reset, rollout, measured execution, replay, PPO, ranking, or promotion starts;
or the output claims scenario redesign has been executed.
```

## Claim Boundary

Allowed claim:

```text
M2346 designs a bounded dual-axis artifact materialization route for the
26-row current-sim scenario/support redesign blocker.
```

Blocked claims:

```text
scenario redesign executed;
support-policy ranking;
controller-family comparison readiness;
residual support solved;
paper-level evidence;
finite-window vs GRU conclusion;
level3 self-identification evidence.
```

## Follow-Up

Next milestone:

```text
m2347-paper-route-current-sim-dual-axis-redesign-calibration-materialization-implementation
```

M2347 should implement the artifact-only materializer and focused tests. It
should not run validation rollouts or edit the active benchmark config.
