# M2250 Paper-Route Current-Sim Offtrack/Recovery/Corridor Training Execution

- status: completed
- decision: `current_sim_offtrack_recovery_corridor_training_execution_pass_route_to_result_audit`
- manifest: `experiments/manifests/m2250-paper-route-current-sim-offtrack-recovery-corridor-training-execution.json`
- parent matrix: `runs/m2248_paper_route_current_sim_offtrack_recovery_corridor_reward_extension_materialization/training_matrix.csv`
- result artifact: `runs/m2250_paper_route_current_sim_offtrack_recovery_corridor_training_execution/summary.json`

## Execution Result

M2250 completed the fixed repaired training panel:

```text
result_class: current_sim_training_stability_repair_execution_pass
completed_run_count: 15
failed_run_count: 0
candidate_eval_count: 120
selected_checkpoint_count: 15
expected_candidate_count: 120
runtime_seconds: 315.7409776400309
```

The execution guardrails held:

```text
all_run_metrics_finite: true
all_candidate_metrics_finite: true
all_selected_metrics_finite: true
profile_set_matched: true
seed_set_matched: true
source_contract_violation_count: 0
source_budget_violation_count: 0
guardrail_violation_count: 0
validation_pass: true
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

M2250 still does not pass the pre-registered `2/3` seed readiness floor for any
profile:

```text
final_checkpoint_profile_floor_pass_count: 0
selected_checkpoint_profile_floor_pass_count: 0
```

Selected checkpoint aggregates:

| profile | selected passing seeds | selected return mean | selected termination mean | selected beats final |
| --- | ---: | ---: | ---: | ---: |
| L0_current_masked | `1/3` | `65.04845` | `0.42708` | `3/3` |
| L1_one_step | `1/3` | `64.18060` | `0.40625` | `3/3` |
| L2_window_25 | `1/3` | `66.95109` | `0.41667` | `3/3` |
| L2_window_50 | `1/3` | `66.95093` | `0.41667` | `3/3` |
| L3_online_gru | `0/3` | `57.93655` | `0.53125` | `3/3` |

The repaired reward panel improves selected checkpoints relative to final
checkpoints in every run:

```text
selected_beats_final_count: 15/15
```

Rows that pass the selected readiness floor locally:

| profile/seed | selected step | selected return | selected termination |
| --- | ---: | ---: | ---: |
| L0_current_masked / 222603 | `28672` | `101.99225` | `0.06250` |
| L1_one_step / 222603 | `24576` | `101.98480` | `0.06250` |
| L2_window_25 / 222601 | `16384` | `97.70658` | `0.12500` |
| L2_window_50 / 222601 | `16384` | `97.70719` | `0.12500` |

## Comparison To M2241

M2250 is a repair-execution result, not a controller-family comparison. It can
only be compared to M2241 as route evidence for the same training harness.

Selected aggregate return improves for all five profiles relative to M2241:

| profile | M2241 selected return | M2250 selected return |
| --- | ---: | ---: |
| L0_current_masked | `49.55190` | `65.04845` |
| L1_one_step | `49.01157` | `64.18060` |
| L2_window_25 | `52.04593` | `66.95109` |
| L2_window_50 | `52.62991` | `66.95093` |
| L3_online_gru | `45.94770` | `57.93655` |

Termination is mixed and remains below the route readiness floor:

| profile | M2241 selected termination | M2250 selected termination |
| --- | ---: | ---: |
| L0_current_masked | `0.40625` | `0.42708` |
| L1_one_step | `0.42708` | `0.40625` |
| L2_window_25 | `0.40625` | `0.41667` |
| L2_window_50 | `0.39583` | `0.41667` |
| L3_online_gru | `0.47917` | `0.53125` |

This means the reward extension likely changed training signal in a useful way,
but M2250 alone cannot prove that offtrack was repaired rather than traded for
collision or another termination mode.

## Classification

Primary classification:

```text
offtrack_recovery_corridor_training_execution_complete_but_readiness_still_below_floor
```

Supported:

- The repaired config matrix is executable and guardrail clean.
- Candidate-checkpoint retention remains valuable; selected beats final in
  `15/15` rows.
- Aggregate returns improve relative to the earlier M2241 selected-checkpoint
  panel.

Not supported:

- The repaired panel is comparison-ready.
- A profile can be ranked or selected as a winner.
- The reward repair has reduced offtrack without raising collision risk.
- Any paper-level, finite-window-vs-GRU, or level3 self-identification claim.

## Route Decision

Route to:

```text
m2251-paper-route-current-sim-offtrack-recovery-corridor-training-execution-result-audit
```

M2251 should audit M2250 before any additional training. The audit must decide
whether the next step is selected-checkpoint outcome localization over the
M2250 selected checkpoints, another bounded reward/curriculum repair, or branch
synthesis.

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
m2251-paper-route-current-sim-offtrack-recovery-corridor-training-execution-result-audit
```
