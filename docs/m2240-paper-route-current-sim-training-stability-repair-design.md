# M2240 Paper-Route Current-Sim Training-Stability Repair Design

- status: completed
- decision: `current_sim_training_stability_repair_design_admit_candidate_checkpoint_execution`
- manifest: `experiments/manifests/m2240-paper-route-current-sim-training-stability-repair-design.json`
- parent audit: `docs/m2239-paper-route-current-sim-task-curriculum-readiness-diagnosis-result-audit.md`
- parent diagnosis: `runs/m2238_paper_route_current_sim_task_curriculum_readiness_diagnosis/summary.json`

## Design Rationale

M2238/M2239 classify the current blocker as training plateau or late regression:

```text
late_regression_row_count: 18/30
profile_floor_pass_count short-v0: 0
profile_floor_pass_count medium-v1: 0
fail_to_pass after budget increase: 0/15
```

The current medium-v1 run did not save or evaluate intermediate checkpoints:

```text
checkpoint_interval_steps: 0
final checkpoint only
```

The trainer already supports periodic checkpoint writing through
`checkpoint_interval_steps`, but the matched-budget configs disabled it. The
next repair should therefore test checkpoint-selection and training-stability
before changing actor inputs, controller profiles, or the task distribution.

## Repair Strategy

Run a controlled stability-repair panel with the same profile/seed fairness as
M2234:

```text
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

total_steps: 32768
rollout_steps: 128
num_envs: 4
update_epochs: 2
eval_episodes: 32
vector_env_mode: sync
checkpoint_interval_steps: 4096
```

This is not another blind budget escalation. It keeps total steps fixed at
medium-v1 and adds a pre-registered candidate-checkpoint retention policy.

## Candidate Checkpoint Set

For each profile/seed run, evaluate exactly one candidate per interval:

```text
4096
8192
12288
16384
20480
24576
28672
32768
```

For `32768`, evaluate the final `checkpoint.pt` path rather than a duplicate
periodic copy. Each candidate uses the same public eval protocol as the final
checkpoint:

```text
eval_seed = train_seed + 10000
eval_episodes = 32
same env config
same controller profile mask
deterministic actor policy
```

This candidate selection is a public training-protocol repair, not a private
holdout or paper-level result.

## Selection Rule

Select one checkpoint per profile/seed with a fixed lexicographic rule:

```text
1. readiness_floor_pass is true
2. lower eval_termination_rate
3. higher eval_return_mean
4. lower eval_lateral_rmse_mean
5. earlier checkpoint step
```

The selection is per run only. It does not rank controller families, select a
paper winner, or make a finite-window-vs-GRU conclusion.

## Required Outputs

The M2241 execution should write:

```text
runs/m2241_paper_route_current_sim_training_stability_repair_execution/summary.json
runs/m2241_paper_route_current_sim_training_stability_repair_execution/run_rows.csv
runs/m2241_paper_route_current_sim_training_stability_repair_execution/candidate_eval_rows.csv
runs/m2241_paper_route_current_sim_training_stability_repair_execution/selected_checkpoint_rows.csv
runs/m2241_paper_route_current_sim_training_stability_repair_execution/profile_aggregate.csv
runs/m2241_paper_route_current_sim_training_stability_repair_execution/run_state.json
```

Minimum summary fields:

```text
completed_run_count
failed_run_count
candidate_eval_count
selected_checkpoint_count
all_selected_metrics_finite
profile_floor_pass_count
final_checkpoint_profile_floor_pass_count
selected_checkpoint_profile_floor_pass_count
selected_beats_final_count
guardrail_violation_count
ranking_admissible_count
winner_selected
finite_window_vs_gru_conclusion_made
paper_level_claim_made
level3_self_id_claim_made
```

## Acceptance Logic

M2241 should pass as an execution artifact if:

```text
15/15 training runs complete
all candidate eval metrics are finite
all selected checkpoint metrics are finite
contract violations are 0
guardrail violations are 0
candidate_eval_count is 120
selected_checkpoint_count is 15
```

Result interpretation is separate:

```text
if selected_checkpoint_profile_floor_pass_count >= 1:
  route to result audit and then measured-readiness design

if selected improves final but still profile_floor_pass_count == 0:
  route to reward/curriculum repair design

if selected does not improve final:
  route to task/curriculum or reward repair design, not more budget
```

## Guardrails

M2241 must not:

```text
change actor inputs
change profile definitions
drop difficult seeds
rank profiles
select a winner
use private holdout
claim finite-window-vs-GRU evidence
claim level3 self-identification
claim paper-level result
```

## Follow-Up

Admit:

```text
m2241-paper-route-current-sim-training-stability-repair-execution
```

M2241 may implement and run the controlled stability-repair execution. It must
fail closed if candidate checkpoint paths, eval summaries, finite metrics, or
guardrails are missing.
