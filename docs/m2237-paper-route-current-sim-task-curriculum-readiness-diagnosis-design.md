# M2237 Paper-Route Current-Sim Task/Curriculum Readiness Diagnosis Design

- status: completed
- decision: `current_sim_task_curriculum_readiness_diagnosis_design_admit_artifact_only_implementation`
- manifest: `experiments/manifests/m2237-paper-route-current-sim-task-curriculum-readiness-diagnosis-design.json`
- parent synthesis: `docs/m2236-paper-route-current-sim-matched-budget-training-branch-synthesis.md`

## Purpose

M2236 closed the blind budget-escalation branch. Short-v0 and medium-v1 both
completed cleanly, but both had `quality_floor_profile_pass_count=0`.

M2237 designs an artifact-only diagnosis to localize why matched-budget training
remains below the readiness floor before any new training, rollout, measured
execution, replay, private holdout, ranking, or self-ID claim.

## Input Artifacts

Short-v0:

```text
runs/m2230_paper_route_current_sim_matched_budget_profile_training_execution/summary.json
runs/m2230_paper_route_current_sim_matched_budget_profile_training_execution/run_rows.csv
runs/m2230_paper_route_current_sim_matched_budget_profile_training_execution/profile_aggregate.csv
runs/m2230_paper_route_current_sim_matched_budget_profile_training_execution/profiles/*/seed_*/train_metrics.csv
```

Medium-v1:

```text
runs/m2234_paper_route_current_sim_matched_budget_medium_training_execution/summary.json
runs/m2234_paper_route_current_sim_matched_budget_medium_training_execution/run_rows.csv
runs/m2234_paper_route_current_sim_matched_budget_medium_training_execution/profile_aggregate.csv
runs/m2234_paper_route_current_sim_matched_budget_medium_training_execution/profiles/*/seed_*/train_metrics.csv
```

No episode rerun is allowed. The diagnosis must operate only on existing
training/eval summaries and train-metrics CSV files.

## Diagnostic Axes

### 1. Readiness-floor gap

For every profile/seed/budget row compute:

```text
return_gap = 50.0 - eval_return_mean
termination_gap = eval_termination_rate - 0.4
floor_fail_reason:
  pass
  return_only
  termination_only
  both
```

This distinguishes "near pass" from "far below floor". If many rows are close
to one threshold, the next route may be floor calibration or focused reward
repair. If rows fail both thresholds, the issue is broader task/training
readiness.

### 2. Seed fragility

Group by seed across profiles and budgets:

```text
passing_seed_count_by_seed
mean_return_by_seed
mean_termination_by_seed
budget_delta_by_seed
```

If one seed consistently passes while others fail, the problem is likely task
seed heterogeneity or scenario distribution. That should route to task/curriculum
diagnosis rather than architecture ranking.

### 3. Budget response

Join short-v0 and medium-v1 rows by `profile_name, seed_id` and compute:

```text
delta_return = medium_return - short_return
delta_termination = medium_termination - short_termination
floor_transition = fail_to_pass / pass_to_fail / unchanged_fail / unchanged_pass
```

This tests whether more training produces systematic improvement or simply
moves noisy seeds. It must not rank profiles.

### 4. Training plateau and late regression

From each `train_metrics.csv` compute:

```text
best_rollout_return_mean
final_rollout_return_mean
best_termination_rate
final_termination_rate
last_quarter_return_mean
last_quarter_termination_rate_mean
best_update_step
final_minus_best_return
final_minus_best_termination
```

If best rollout return is much better than final, the next route should consider
checkpoint selection/early stopping rather than more budget. If last-quarter
termination remains high, the next route should consider task/curriculum or
reward/termination design.

### 5. Profile-independent task difficulty signal

Aggregate without ranking:

```text
global_floor_pass_rate
global_return_gap_mean
global_termination_gap_mean
near_floor_count
far_below_floor_count
```

This asks whether the panel itself is too hard or poorly calibrated for the
current training recipe.

## Output Artifacts

M2238 should produce:

```text
runs/m2238_paper_route_current_sim_task_curriculum_readiness_diagnosis/summary.json
runs/m2238_paper_route_current_sim_task_curriculum_readiness_diagnosis/row_diagnosis.csv
runs/m2238_paper_route_current_sim_task_curriculum_readiness_diagnosis/seed_diagnosis.csv
runs/m2238_paper_route_current_sim_task_curriculum_readiness_diagnosis/budget_delta.csv
runs/m2238_paper_route_current_sim_task_curriculum_readiness_diagnosis/training_plateau.csv
runs/m2238_paper_route_current_sim_task_curriculum_readiness_diagnosis/run_state.json
```

## Route Rules

M2238 should classify the next route without ranking profiles:

```text
task_seed_heterogeneity
training_plateau_or_late_regression
readiness_floor_calibration
reward_or_termination_repair
task_curriculum_repair
insufficient_existing_artifacts
```

Initial routing policy:

- if the same seeds pass/fail across profiles, route to task-seed/curriculum
  diagnosis;
- if medium improves most rows but still misses by small margins, route to
  floor/reward calibration audit;
- if best train checkpoints are much better than final, route to checkpoint
  selection/early stopping design;
- if medium does not improve L3 while finite-window/current profiles improve,
  record it only as a diagnosis input, not architecture ranking;
- if artifacts are insufficient, stop and write an artifact-gap report before
  running new rollouts.

## Claim Boundary

Allowed:

```text
artifact-only readiness diagnosis design
```

Blocked:

```text
new training
new rollout
measured execution
profile ranking
winner selection
finite-window-vs-GRU conclusion
paper-level result
level3 self-identification
private holdout
```

## Next

Pre-register:

```text
m2238-paper-route-current-sim-task-curriculum-readiness-diagnosis-implementation
```
