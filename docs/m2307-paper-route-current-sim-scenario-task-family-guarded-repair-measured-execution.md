# M2307 Paper-Route Current-Sim Scenario Task-Family Guarded-Repair Measured Execution

- status: completed
- result_class: `current_sim_scenario_task_family_measured_execution_pass`
- manifest: `experiments/manifests/m2307-paper-route-current-sim-scenario-task-family-guarded-repair-measured-execution.json`
- summary: `runs/m2307_paper_route_current_sim_scenario_task_family_guarded_repair_measured_execution/summary.json`
- runner: `src/autodrift/paper_route_current_sim_scenario_task_family_measured_execution.py`
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
  --selected-rows runs/m2304_paper_route_current_sim_scenario_task_family_guarded_repair_training_execution/selected_checkpoint_rows.csv \
  --config-root runs/m2304_paper_route_current_sim_scenario_task_family_guarded_repair_training_execution/configs \
  --output-dir runs/m2307_paper_route_current_sim_scenario_task_family_guarded_repair_measured_execution \
  --eval-seed-base 230700 \
  --target-scenario-spec-count 72 \
  --target-selected-checkpoint-count 15 \
  --target-episode-count 1080 \
  --device cpu \
  --next-blocker m2308-paper-route-current-sim-scenario-task-family-guarded-repair-measured-execution-result-audit
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
success_count: 68
success_rate: 0.06296296296296296
collision_count: 218
collision_rate: 0.20185185185185187
offtrack_count: 786
offtrack_rate: 0.7277777777777777
max_step_noncompletion_count: 4
max_step_noncompletion_rate: 0.003703703703703704
other_failure_count: 4
other_failure_rate: 0.003703703703703704
mean_min_clearance_margin: 6.461206859204371
min_min_clearance_margin: -0.34658935202461905
dominant_failure_mode: offtrack_dominated_failure
```

Reference M2293 global outcome:

```text
success/offtrack/collision: 69 / 785 / 209
max_step_noncompletion_count: 7
other_failure_count: 10
mean_min_clearance_margin: 6.802372067958403
```

M2307 global deltas versus M2293:

```text
success_delta: -1
offtrack_delta: +1
collision_delta: +9
max_step_noncompletion_delta: -3
other_failure_delta: -6
mean_min_clearance_margin_delta: -0.341165208754032
```

These deltas are diagnostic only. They do not rank profiles and do not prove
repair success or failure until M2308 audits the M2298 target/guardrail slices.

## Role-Family Snapshot

```text
R0 success/collision/offtrack: 7 / 1 / 172
R1 success/collision/offtrack: 61 / 5 / 114
R2 success/collision/offtrack: 0 / 27 / 150
R3 success/collision/offtrack: 0 / 21 / 157
R4 success/collision/offtrack: 0 / 133 / 47
R5 success/collision/offtrack: 0 / 31 / 146
```

The profile aggregates are written for M2308 audit only. They are not ranking
evidence and do not select a winner.

## Artifacts

```text
runs/m2307_paper_route_current_sim_scenario_task_family_guarded_repair_measured_execution/summary.json
runs/m2307_paper_route_current_sim_scenario_task_family_guarded_repair_measured_execution/episode_rows.csv
runs/m2307_paper_route_current_sim_scenario_task_family_guarded_repair_measured_execution/failure_rows.csv
runs/m2307_paper_route_current_sim_scenario_task_family_guarded_repair_measured_execution/validation_failure_rows.csv
runs/m2307_paper_route_current_sim_scenario_task_family_guarded_repair_measured_execution/metadata_missing_rows.csv
runs/m2307_paper_route_current_sim_scenario_task_family_guarded_repair_measured_execution/metric_completeness_failures.csv
runs/m2307_paper_route_current_sim_scenario_task_family_guarded_repair_measured_execution/claim_boundary.csv
runs/m2307_paper_route_current_sim_scenario_task_family_guarded_repair_measured_execution/aggregate_by_role_family.csv
runs/m2307_paper_route_current_sim_scenario_task_family_guarded_repair_measured_execution/aggregate_by_scenario_family.csv
runs/m2307_paper_route_current_sim_scenario_task_family_guarded_repair_measured_execution/aggregate_by_profile_seed.csv
runs/m2307_paper_route_current_sim_scenario_task_family_guarded_repair_measured_execution/aggregate_by_profile.csv
runs/m2307_paper_route_current_sim_scenario_task_family_guarded_repair_measured_execution/aggregate_by_obstacle_label.csv
runs/m2307_paper_route_current_sim_scenario_task_family_guarded_repair_measured_execution/aggregate_by_timing_bucket.csv
runs/m2307_paper_route_current_sim_scenario_task_family_guarded_repair_measured_execution/aggregate_by_lateral_bucket.csv
runs/m2307_paper_route_current_sim_scenario_task_family_guarded_repair_measured_execution/aggregate_by_hidden_dynamics_bucket.csv
```

## Claim Boundary

M2307 may claim only that the guarded-v2 selected-checkpoint panel is runnable
as a measured execution panel with complete metadata and no guardrail violation.

M2307 does not claim:

- controller-family ranking;
- winner selection;
- paper-level benchmark result;
- finite-window vs GRU conclusion;
- level3 self-identification.

## Next

Pre-register:

```text
m2308-paper-route-current-sim-scenario-task-family-guarded-repair-measured-execution-result-audit
```

M2308 must audit the M2298 offtrack target and collision guardrail slices before
any repair, comparison, or paper-route interpretation.
