# M2304 Paper-Route Current-Sim Scenario Task-Family Guarded-Repair Training Execution

- status: completed
- decision: `current_sim_scenario_task_family_guarded_repair_training_execution_pass_route_to_result_audit`
- manifest: `experiments/manifests/m2304-paper-route-current-sim-scenario-task-family-guarded-repair-training-execution.json`
- parent matrix: `runs/m2302_paper_route_current_sim_scenario_task_family_guarded_repair_configs/training_matrix.csv`
- result artifact: `runs/m2304_paper_route_current_sim_scenario_task_family_guarded_repair_training_execution/summary.json`
- device: `cuda`
- runtime_seconds: `644.463307607919`

## Execution Result

M2304 completed the frozen guarded-v2 repair training execution:

```text
result_class: current_sim_training_stability_repair_execution_pass
completed_run_count: 15
failed_run_count: 0
candidate_eval_count: 120
selected_checkpoint_count: 15
expected_candidate_count: 120
```

The execution guardrails held:

```text
validation_pass: true
all_run_metrics_finite: true
all_candidate_metrics_finite: true
all_selected_metrics_finite: true
profile_set_matched: true
seed_set_matched: true
source_contract_violation_count: 0
source_budget_violation_count: 0
guardrail_violation_count: 0
training_started: true
ppo_started: true
policy_action_executed: true
environment_rollout_started: true
```

No ranking or paper claim is admitted:

```text
ranking_admissible_count: 0
winner_selected: false
controller_family_ranking_claim_made: false
finite_window_vs_gru_conclusion_made: false
paper_level_claim_made: false
level3_self_id_claim_made: false
```

## Profile Aggregates

M2304 does not pass the pre-registered `2/3` seed readiness floor for any
profile:

```text
final_checkpoint_profile_floor_pass_count: 0
selected_checkpoint_profile_floor_pass_count: 0
selected_readiness_floor_pass_count: 5/15
final_readiness_floor_pass_count: 4/15
selected_beats_final_count: 10/15
```

Selected checkpoint aggregates:

| profile | selected passing seeds | selected return mean | selected termination mean | selected beats final |
| --- | ---: | ---: | ---: | ---: |
| L0_current_masked | `1/3` | `50.06262` | `0.55208` | `2/3` |
| L1_one_step | `1/3` | `46.33150` | `0.55208` | `2/3` |
| L2_window_25 | `1/3` | `43.55920` | `0.52083` | `2/3` |
| L2_window_50 | `1/3` | `44.56003` | `0.52083` | `1/3` |
| L3_online_gru | `1/3` | `42.82827` | `0.62500` | `3/3` |

Across all selected rows:

```text
selected_eval_return_mean: 45.66833
selected_eval_termination_rate_mean: 0.55417
final_eval_return_mean: 39.03764
final_eval_termination_rate_mean: 0.61458
```

Candidate selection improved many final checkpoints, but the aggregate remains
below readiness floor. This is training-execution evidence only, not
comparison-ready outcome evidence.

## Classification

Primary classification:

```text
guarded_repair_training_execution_clean_but_below_profile_readiness_floor
```

Supported:

- The M2302 guarded-v2 config matrix is executable on CUDA.
- The candidate-checkpoint panel is complete: `120` candidate rows and `15`
  selected rows.
- Candidate selection often improves final checkpoints: `10/15` selected rows
  beat their final checkpoint.
- Claim guardrails held: no ranking, no winner, no paper claim, no finite-window
  vs GRU conclusion, and no level3 self-ID claim.

Not supported:

- Any profile is comparison-ready.
- Guarded-v2 repair is behaviorally successful.
- Offtrack count decreased without raising collision count.
- Any profile should be promoted or ranked.
- Any paper-level, finite-window-vs-GRU, or level3 self-identification claim.

## Route Decision

Route to:

```text
m2305-paper-route-current-sim-scenario-task-family-guarded-repair-training-execution-result-audit
```

M2305 must audit whether the clean execution and selected checkpoint rows are
worth a guarded measured-execution localization panel, or whether the branch
should synthesize/pivot because readiness floors stayed at zero.

## Blocked Claims

Still blocked:

```text
controller-family ranking
winner selection
measured execution as comparison evidence
finite-window-vs-GRU conclusion
paper-level result
level3 self-identification
private holdout
another blind budget escalation
```

## Next

Pre-register:

```text
m2305-paper-route-current-sim-scenario-task-family-guarded-repair-training-execution-result-audit
```
