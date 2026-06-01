# M2306 Paper-Route Current-Sim Scenario Task-Family Guarded-Repair Selected-Checkpoint Measured Execution Design

- status: completed
- decision: `guarded_repair_selected_checkpoint_measured_execution_design_admit_execution`
- manifest: `experiments/manifests/m2306-paper-route-current-sim-scenario-task-family-guarded-repair-selected-checkpoint-measured-execution-design.json`
- parent audit: `docs/m2305-paper-route-current-sim-scenario-task-family-guarded-repair-training-execution-result-audit.md`
- selected checkpoint source: `runs/m2304_paper_route_current_sim_scenario_task_family_guarded_repair_training_execution/selected_checkpoint_rows.csv`
- config root: `runs/m2304_paper_route_current_sim_scenario_task_family_guarded_repair_training_execution/configs`
- measured execution in M2306: `false`
- policy actions executed in M2306: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- finite-window vs GRU conclusion made: `false`
- level3 self-ID claim made: `false`

## Design Rationale

M2305 establishes that M2304 is a clean guarded-v2 training execution, but it
does not establish repair success:

```text
completed_run_count: 15
candidate_eval_count: 120
selected_checkpoint_count: 15
selected_beats_final_count: 10/15
selected_checkpoint_profile_floor_pass_count: 0
selected_readiness_floor_pass_count: 5/15
```

The repair target from M2298 is not selected return. It is the scenario-family
outcome distribution:

```text
offtrack-primary target slices
collision guardrail slices
role-family failure modes
```

Therefore the next evidence gap is measured outcome mode over the same reset-
valid scenario task-family panel as M2293.

## Preflight

The required sources are present:

```text
selected rows: 15 plus header
profile config files: 15
scenario config: configs/paper_route_current_sim_scenario_task_family_v0.json
runner: src/autodrift/paper_route_current_sim_scenario_task_family_measured_execution.py
```

M2306 does not parse, reset, or execute the panel. It only freezes the command
and claim boundary for M2307.

## Execution Scope

M2307 should evaluate exactly the `15` M2304 selected checkpoint rows:

```text
scenario config:
  configs/paper_route_current_sim_scenario_task_family_v0.json

selected rows:
  runs/m2304_paper_route_current_sim_scenario_task_family_guarded_repair_training_execution/selected_checkpoint_rows.csv

config root:
  runs/m2304_paper_route_current_sim_scenario_task_family_guarded_repair_training_execution/configs

profiles:
  L0_current_masked
  L1_one_step
  L2_window_25
  L2_window_50
  L3_online_gru

seeds:
  222601
  222602
  222603

scenario specs:
  72

expected episode rows:
  72 * 15 = 1080
```

Use the M2293 deterministic measured-execution seed rule:

```text
eval_seed = eval_seed_base + selected_checkpoint_index * 1000 + scenario_spec_index
eval_seed_base = 230700
```

This keeps M2307 comparable to M2293 as repair-route evidence, not as
controller-family ranking.

## Frozen Command

M2307 should run:

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

## Required Outputs

M2307 should write:

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

## Pass Gates

M2307 passes only if:

```text
summary.json exists
episode_count == 1080
scenario_spec_count == 72
selected_checkpoint_count == 15
failure_count == 0
metadata_missing_count == 0
metric_completeness_failure_count == 0
guardrail_violation_count == 0
controller_family_ranking_claim_made == false
winner_selected == false
paper_level_claim_made == false
finite_window_vs_gru_conclusion_made == false
level3_self_id_claim_made == false
```

Pass or fail, M2307 must route to M2308 result audit before interpretation.

## Audit Metrics

M2308 must compare M2307 against the M2293 reference panel and the M2298
offtrack/collision guardrail spec:

```text
M2293 global outcome:
  success/offtrack/collision = 69/785/209
  max_step_noncompletion_count = 7
  other_failure_count = 10

M2298 repair gate spec:
  offtrack_target_slice_count = 20
  collision_guardrail_slice_count = 11
```

M2307 is useful only if it supports target-slice improvement without collision
guardrail regression. Global return or selected checkpoint readiness is
explicitly insufficient.

## Guardrails

M2306 and M2307 must not:

```text
train
alter checkpoints
alter actor inputs
alter scenario specs
drop selected checkpoints
drop seeds
use private holdout
promote any checkpoint
rank profiles
select a winner
claim finite-window-vs-GRU
claim level3 self-identification
claim paper-level result
```

## Next

Pre-register:

```text
m2307-paper-route-current-sim-scenario-task-family-guarded-repair-measured-execution
```
