# M2295 Paper-Route Current-Sim Scenario Task-Family Failure-Slice Diagnosis Implementation

- status: completed
- result_class: `current_sim_scenario_task_family_failure_slice_diagnosis_pass`
- manifest: `experiments/manifests/m2295-paper-route-current-sim-scenario-task-family-failure-slice-diagnosis-implementation.json`
- summary: `runs/m2295_paper_route_current_sim_scenario_task_family_failure_slice_diagnosis/summary.json`
- runner: `src/autodrift/paper_route_current_sim_scenario_task_family_failure_slice_diagnosis.py`
- tests: `tests/test_paper_route_current_sim_scenario_task_family_failure_slice_diagnosis.py`
- environment reset/rollout/policy action: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- paper-level claim made: `false`
- finite-window vs GRU conclusion made: `false`
- level3 self-ID claim made: `false`

## Command

```bash
PYTHONPATH=src python -m autodrift.paper_route_current_sim_scenario_task_family_failure_slice_diagnosis \
  --summary runs/m2293_paper_route_current_sim_scenario_task_family_measured_execution/summary.json \
  --episode-rows runs/m2293_paper_route_current_sim_scenario_task_family_measured_execution/episode_rows.csv \
  --output-dir runs/m2295_paper_route_current_sim_scenario_task_family_failure_slice_diagnosis \
  --next-blocker m2296-paper-route-current-sim-scenario-task-family-failure-slice-diagnosis-result-audit
```

## Count Reproduction

M2295 reproduces the M2293 global counts using the same mutually exclusive
classification priority:

```text
success -> collision -> offtrack -> max_step -> other
```

Count checks:

```text
input_episode_count: 1080
summary_episode_count: 1080
episode_count_match: true
success_count_match: true
offtrack_count_match: true
collision_count_match: true
max_step_count_match: true
guardrail_violation_count: 0
```

Global outcome:

```text
success_count: 69
success_rate: 0.06388888888888888
offtrack_count: 785
offtrack_rate: 0.7268518518518519
collision_count: 209
collision_rate: 0.1935185185185185
dominant_failure_mode: offtrack_dominated_failure
dominant_slice_count: 56
```

## Dominant Slices

Top diagnostic slices:

```text
termination_reason=off_track:
  episode_count: 786
  offtrack_count: 785
  collision_count: 1
  dominant_failure_mode: offtrack_dominated_failure
  dominant_failure_count: 785

outcome_bucket=off_track_noncollision_noncompletion:
  episode_count: 785
  offtrack_count: 785
  dominant_failure_mode: offtrack_dominated_failure

obstacle_lateral_offset_bucket=centerline:
  episode_count: 510
  offtrack_count: 383
  collision_count: 84
  dominant_failure_mode: offtrack_dominated_failure

sampled_obstacle_label=drift_required:
  episode_count: 405
  offtrack_count: 323
  collision_count: 73
  dominant_failure_mode: offtrack_dominated_failure

obstacle_longitudinal_timing_bucket=early_far:
  episode_count: 360
  offtrack_count: 310
  collision_count: 18
  dominant_failure_mode: offtrack_dominated_failure
```

Collision remains an important guardrail:

```text
outcome_bucket=collision_failure:
  episode_count: 209
  collision_count: 209
  dominant_failure_mode: collision_dominated_failure

termination_reason=obstacle_collision:
  episode_count: 208
  collision_count: 208
  dominant_failure_mode: collision_dominated_failure
```

## Primary Route

M2295 route recommendation:

```text
offtrack_primary_collision_guardrail_failure_slice_result_audit
```

Reason:

```text
global offtrack dominates while collision slices remain a guardrail
```

This is not a repair decision. M2296 must audit the diagnosis and decide whether
the next route should be offtrack containment, collision/mitigation guardrail
repair, scenario-task reshaping, or another synthesis/pivot.

## Artifacts

```text
runs/m2295_paper_route_current_sim_scenario_task_family_failure_slice_diagnosis/summary.json
runs/m2295_paper_route_current_sim_scenario_task_family_failure_slice_diagnosis/global_slice.csv
runs/m2295_paper_route_current_sim_scenario_task_family_failure_slice_diagnosis/all_slices.csv
runs/m2295_paper_route_current_sim_scenario_task_family_failure_slice_diagnosis/dominant_slices.csv
runs/m2295_paper_route_current_sim_scenario_task_family_failure_slice_diagnosis/route_recommendation.csv
runs/m2295_paper_route_current_sim_scenario_task_family_failure_slice_diagnosis/claim_boundary.csv
runs/m2295_paper_route_current_sim_scenario_task_family_failure_slice_diagnosis/slice_by_role_family.csv
runs/m2295_paper_route_current_sim_scenario_task_family_failure_slice_diagnosis/slice_by_scenario_family_id.csv
runs/m2295_paper_route_current_sim_scenario_task_family_failure_slice_diagnosis/slice_by_sampled_obstacle_label.csv
runs/m2295_paper_route_current_sim_scenario_task_family_failure_slice_diagnosis/slice_by_obstacle_longitudinal_timing_bucket.csv
runs/m2295_paper_route_current_sim_scenario_task_family_failure_slice_diagnosis/slice_by_obstacle_lateral_offset_bucket.csv
runs/m2295_paper_route_current_sim_scenario_task_family_failure_slice_diagnosis/slice_by_hidden_dynamics_bucket.csv
runs/m2295_paper_route_current_sim_scenario_task_family_failure_slice_diagnosis/slice_by_profile_name.csv
runs/m2295_paper_route_current_sim_scenario_task_family_failure_slice_diagnosis/slice_by_profile_seed.csv
runs/m2295_paper_route_current_sim_scenario_task_family_failure_slice_diagnosis/slice_by_outcome_bucket.csv
runs/m2295_paper_route_current_sim_scenario_task_family_failure_slice_diagnosis/slice_by_termination_reason.csv
```

## Claim Boundary

M2295 may claim only that an artifact-only failure-slice diagnosis was produced
over M2293 rows and that its counts reproduce M2293.

M2295 cannot claim:

- controller-family ranking;
- winner selection;
- paper-level benchmark result;
- finite-window vs GRU conclusion;
- level3 self-identification.

## Next

Pre-registered follow-up:

```text
m2296-paper-route-current-sim-scenario-task-family-failure-slice-diagnosis-result-audit
```
