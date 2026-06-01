# M2303 Paper-Route Current-Sim Scenario Task-Family Guarded-Repair Training Execution Design

- status: completed
- decision: `guarded_repair_training_execution_design_admit_cuda_execution`
- manifest: `experiments/manifests/m2303-paper-route-current-sim-scenario-task-family-guarded-repair-training-execution-design.json`
- parent summary: `runs/m2302_paper_route_current_sim_scenario_task_family_guarded_repair_configs/summary.json`
- parent matrix: `runs/m2302_paper_route_current_sim_scenario_task_family_guarded_repair_configs/training_matrix.csv`
- device check: `torch.cuda.is_available() == true`
- device: `NVIDIA GeForce RTX 5080`
- training executed in M2303: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- paper-level claim made: `false`
- finite-window vs GRU conclusion made: `false`
- level3 self-ID claim made: `false`

## Design Decision

M2303 admits a bounded CUDA training execution:

```text
m2304-paper-route-current-sim-scenario-task-family-guarded-repair-training-execution
```

M2304 should use the existing candidate-checkpoint runner:

```text
autodrift.paper_route_current_sim_training_stability_repair_execution
```

## Frozen Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.paper_route_current_sim_training_stability_repair_execution \
  --training-matrix runs/m2302_paper_route_current_sim_scenario_task_family_guarded_repair_configs/training_matrix.csv \
  --output-dir runs/m2304_paper_route_current_sim_scenario_task_family_guarded_repair_training_execution \
  --execution-root runs/m2304_paper_route_current_sim_scenario_task_family_guarded_repair_training_execution \
  --device cuda \
  --task-id m2304-paper-route-current-sim-scenario-task-family-guarded-repair-training-execution \
  --fail-fast \
  --next-blocker m2305-paper-route-current-sim-scenario-task-family-guarded-repair-training-execution-result-audit
```

## Expected Counts

```text
expected_run_count: 15
expected_candidate_count: 120
expected_selected_checkpoint_count: 15
profiles: 5
seeds: 3
candidate steps: 4096, 8192, 12288, 16384, 20480, 24576, 28672, 32768
```

The execution is still not ranking. Candidate selection is diagnostic and
prepares a later guarded measured-execution panel.

## Guardrails

M2304 must keep:

```text
training_matrix:
  runs/m2302_paper_route_current_sim_scenario_task_family_guarded_repair_configs/training_matrix.csv

actor contract:
  P0_human_view_no_wheel_no_oracle

claim boundary:
  ranking_admissible_count: 0
  winner_selected: false
  paper_level_claim_made: false
  finite_window_vs_gru_conclusion_made: false
  level3_self_id_claim_made: false
```

M2304 may train and evaluate candidate checkpoints through the frozen runner.
It may not promote a checkpoint or rank controller families.

## Output Artifacts

M2304 should write:

```text
runs/m2304_paper_route_current_sim_scenario_task_family_guarded_repair_training_execution/summary.json
runs/m2304_paper_route_current_sim_scenario_task_family_guarded_repair_training_execution/command_matrix.csv
runs/m2304_paper_route_current_sim_scenario_task_family_guarded_repair_training_execution/run_rows.csv
runs/m2304_paper_route_current_sim_scenario_task_family_guarded_repair_training_execution/candidate_eval_rows.csv
runs/m2304_paper_route_current_sim_scenario_task_family_guarded_repair_training_execution/selected_checkpoint_rows.csv
runs/m2304_paper_route_current_sim_scenario_task_family_guarded_repair_training_execution/profile_aggregate.csv
runs/m2304_paper_route_current_sim_scenario_task_family_guarded_repair_training_execution/run_state.json
```

## Claim Boundary

M2303 is execution design only. M2304, even if it passes, will be training
execution evidence only. The next result audit must decide whether the produced
selected checkpoints are worth a guarded 1080-episode measured-execution panel.

M2303 cannot claim:

- any repair improves behavior;
- controller-family ranking;
- winner selection;
- paper-level benchmark result;
- finite-window vs GRU conclusion;
- level3 self-identification.

## Follow-Up

Pre-registered:

```text
experiments/manifests/m2304-paper-route-current-sim-scenario-task-family-guarded-repair-training-execution.json
```
