# M2305 Paper-Route Current-Sim Scenario Task-Family Guarded-Repair Training Execution Result Audit

- status: completed
- decision: `guarded_repair_training_audit_route_to_selected_checkpoint_measured_execution_design`
- manifest: `experiments/manifests/m2305-paper-route-current-sim-scenario-task-family-guarded-repair-training-execution-result-audit.json`
- parent result: `runs/m2304_paper_route_current_sim_scenario_task_family_guarded_repair_training_execution/summary.json`

## Audit Result

M2304 is a clean guarded-v2 training execution artifact:

```text
result_class: current_sim_training_stability_repair_execution_pass
completed_run_count: 15
failed_run_count: 0
candidate_eval_count: 120
selected_checkpoint_count: 15
all_run_metrics_finite: true
all_candidate_metrics_finite: true
all_selected_metrics_finite: true
guardrail_violation_count: 0
ranking_admissible_count: 0
winner_selected: false
```

It is still not comparison-ready:

```text
selected_checkpoint_profile_floor_pass_count: 0
final_checkpoint_profile_floor_pass_count: 0
selected_readiness_floor_pass_count: 5/15
final_readiness_floor_pass_count: 4/15
selected_beats_final_count: 10/15
```

The selected checkpoint aggregate improved over the final checkpoints, but the
local candidate eval remains weak:

```text
selected_eval_return_mean: 45.66833
selected_eval_termination_rate_mean: 0.55417
final_eval_return_mean: 39.03764
final_eval_termination_rate_mean: 0.61458
```

This does not justify ranking profiles, promoting a checkpoint, or running
another blind training panel.

## Interpretation

M2304 answers only this question:

```text
The guarded-v2 repair matrix is executable and produces complete candidate
checkpoint evidence under the frozen M2303 command.
```

It does not answer the actual scenario/task-quality repair question:

```text
did the M2298 offtrack target slices improve?
did collision guardrail slices stay bounded?
did guarded-v2 turn offtrack failures into collisions?
did any role family become materially more drivable?
```

Those require the same role-family scenario measured-execution shape as M2293,
using the M2304 selected checkpoint rows.

## Route Decision

Route to:

```text
m2306-paper-route-current-sim-scenario-task-family-guarded-repair-selected-checkpoint-measured-execution-design
```

M2306 should design, but not execute, a 1080-episode selected-checkpoint measured
execution over:

```text
scenario config:
  configs/paper_route_current_sim_scenario_task_family_v0.json

selected rows:
  runs/m2304_paper_route_current_sim_scenario_task_family_guarded_repair_training_execution/selected_checkpoint_rows.csv

config root:
  runs/m2304_paper_route_current_sim_scenario_task_family_guarded_repair_training_execution/configs

reference outcome:
  runs/m2293_paper_route_current_sim_scenario_task_family_measured_execution/summary.json
  runs/m2295_paper_route_current_sim_scenario_task_family_failure_slice_diagnosis/summary.json
  runs/m2298_paper_route_current_sim_scenario_task_family_offtrack_primary_collision_guardrail/summary.json
```

The execution design should keep the M2293 panel shape:

```text
scenario specs: 72
selected checkpoints: 15
episodes: 1080
```

## Blocked Routes

Blocked for now:

```text
another training run before measured outcome evidence
ranking profiles by selected return
accepting candidate-selection improvement as repair success
controller-family ranking
winner selection
finite-window-vs-GRU conclusion
paper-level result
level3 self-identification claim
```

## Next

Pre-register:

```text
m2306-paper-route-current-sim-scenario-task-family-guarded-repair-selected-checkpoint-measured-execution-design
```
