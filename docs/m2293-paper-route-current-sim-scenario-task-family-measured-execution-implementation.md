# M2293 Paper-Route Current-Sim Scenario Task-Family Measured Execution Implementation

- status: completed
- result_class: `current_sim_scenario_task_family_measured_execution_pass`
- manifest: `experiments/manifests/m2293-paper-route-current-sim-scenario-task-family-measured-execution-implementation.json`
- summary: `runs/m2293_paper_route_current_sim_scenario_task_family_measured_execution/summary.json`
- runner: `src/autodrift/paper_route_current_sim_scenario_task_family_measured_execution.py`
- tests: `tests/test_paper_route_current_sim_scenario_task_family_measured_execution.py`
- training/replay/PPO: `false`
- profile config or scenario spec tuning: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- paper-level claim made: `false`
- finite-window vs GRU conclusion made: `false`
- level3 self-ID claim made: `false`

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.paper_route_current_sim_scenario_task_family_measured_execution \
  --config configs/paper_route_current_sim_scenario_task_family_v0.json \
  --selected-rows runs/m2262_paper_route_current_sim_midcourse_corridor_containment_training_execution/selected_checkpoint_rows.csv \
  --config-root runs/m2262_paper_route_current_sim_midcourse_corridor_containment_training_execution/configs \
  --output-dir runs/m2293_paper_route_current_sim_scenario_task_family_measured_execution \
  --eval-seed-base 229300 \
  --target-scenario-spec-count 72 \
  --target-selected-checkpoint-count 15 \
  --target-episode-count 1080 \
  --device cpu \
  --next-blocker m2294-paper-route-current-sim-scenario-task-family-measured-execution-result-audit
```

## Execution Completeness

```text
episode_count: 1080 / 1080
scenario_spec_count: 72 / 72
selected_checkpoint_count: 15 / 15
failure_count: 0
validation_failure_count: 0
metadata_missing_count: 0
metric_completeness_failure_count: 0
guardrail_violation_count: 0
label_mismatch_count: 0
```

Role-family coverage is balanced:

```text
R0_stable_avoidable: 180
R1_aeb_infeasible_stable_aes: 180
R2_handling_limit_drift_capable_avoidance: 180
R3_recovery_after_limit: 180
R4_unavoidable_mitigation: 180
R5_hidden_dynamics_robustness: 180
```

Profile coverage is also balanced:

```text
L0_current_masked: 216
L1_one_step: 216
L2_window_25: 216
L2_window_50: 216
L3_online_gru: 216
```

## Outcome Snapshot

Global diagnostic outcome:

```text
success_count: 69
success_rate: 0.06388888888888888
collision_count: 209
collision_rate: 0.1935185185185185
offtrack_count: 785
offtrack_rate: 0.7268518518518519
max_step_noncompletion_count: 7
max_step_noncompletion_rate: 0.006481481481481481
other_failure_count: 10
other_failure_rate: 0.009259259259259259
mean_min_clearance_margin: 6.802372067958403
min_min_clearance_margin: -0.3498040457660503
dominant_failure_mode: offtrack_dominated_failure
```

Role-family outcome is diagnostic only:

```text
R0 success_rate: 0.05555555555555555, dominant_failure_mode: offtrack_dominated_failure
R1 success_rate: 0.3277777777777778, dominant_failure_mode: offtrack_dominated_failure
R2 success_rate: 0.0, dominant_failure_mode: offtrack_dominated_failure
R3 success_rate: 0.0, dominant_failure_mode: offtrack_dominated_failure
R4 success_rate: 0.0, dominant_failure_mode: collision_dominated_failure
R5 success_rate: 0.0, dominant_failure_mode: offtrack_dominated_failure
```

The profile aggregates are written for M2294 audit only. They are not ranking
evidence and do not select a winner.

## Artifacts

```text
runs/m2293_paper_route_current_sim_scenario_task_family_measured_execution/summary.json
runs/m2293_paper_route_current_sim_scenario_task_family_measured_execution/episode_rows.csv
runs/m2293_paper_route_current_sim_scenario_task_family_measured_execution/failure_rows.csv
runs/m2293_paper_route_current_sim_scenario_task_family_measured_execution/validation_failure_rows.csv
runs/m2293_paper_route_current_sim_scenario_task_family_measured_execution/metadata_missing_rows.csv
runs/m2293_paper_route_current_sim_scenario_task_family_measured_execution/metric_completeness_failures.csv
runs/m2293_paper_route_current_sim_scenario_task_family_measured_execution/claim_boundary.csv
runs/m2293_paper_route_current_sim_scenario_task_family_measured_execution/aggregate_by_role_family.csv
runs/m2293_paper_route_current_sim_scenario_task_family_measured_execution/aggregate_by_scenario_family.csv
runs/m2293_paper_route_current_sim_scenario_task_family_measured_execution/aggregate_by_profile_seed.csv
runs/m2293_paper_route_current_sim_scenario_task_family_measured_execution/aggregate_by_profile.csv
runs/m2293_paper_route_current_sim_scenario_task_family_measured_execution/aggregate_by_obstacle_label.csv
runs/m2293_paper_route_current_sim_scenario_task_family_measured_execution/aggregate_by_timing_bucket.csv
runs/m2293_paper_route_current_sim_scenario_task_family_measured_execution/aggregate_by_lateral_bucket.csv
runs/m2293_paper_route_current_sim_scenario_task_family_measured_execution/aggregate_by_hidden_dynamics_bucket.csv
```

## Claim Boundary

M2293 may claim only that the reset-valid scenario task-family pack is runnable
as a measured execution panel with complete metadata and no guardrail violation.

M2293 does not claim:

- controller-family ranking;
- winner selection;
- paper-level benchmark result;
- finite-window vs GRU conclusion;
- level3 self-identification.

## Next

Pre-registered follow-up:

```text
m2294-paper-route-current-sim-scenario-task-family-measured-execution-result-audit
```

M2294 must audit the offtrack/collision dominated outcome distribution as the
scenario task-quality branch cadence synthesis before any repair, comparison, or
paper-route interpretation.
