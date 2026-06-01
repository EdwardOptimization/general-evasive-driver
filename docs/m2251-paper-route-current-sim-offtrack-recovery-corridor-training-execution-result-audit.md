# M2251 Paper-Route Current-Sim Offtrack/Recovery/Corridor Training Execution Result Audit

- status: completed
- decision: `current_sim_offtrack_recovery_corridor_training_audit_route_to_selected_checkpoint_outcome_localization_design`
- manifest: `experiments/manifests/m2251-paper-route-current-sim-offtrack-recovery-corridor-training-execution-result-audit.json`
- parent result: `runs/m2250_paper_route_current_sim_offtrack_recovery_corridor_training_execution/summary.json`

## Audit Result

M2250 is a complete repaired training artifact:

```text
result_class: current_sim_training_stability_repair_execution_pass
completed_run_count: 15
failed_run_count: 0
candidate_eval_count: 120
expected_candidate_count: 120
selected_checkpoint_count: 15
all_run_metrics_finite: true
all_candidate_metrics_finite: true
all_selected_metrics_finite: true
guardrail_violation_count: 0
```

The execution used the intended fixed panel:

```text
profile_set_matched: true
seed_set_matched: true
source_contract_violation_count: 0
source_budget_violation_count: 0
```

The guardrails held:

```text
private_holdout_used: false
controller_family_ranking_claim_made: false
winner_selected: false
finite_window_vs_gru_conclusion_made: false
paper_level_claim_made: false
level3_self_id_claim_made: false
```

## Training Signal

Candidate checkpoint selection remains useful:

```text
selected_beats_final_count: 15/15
```

M2250 improves selected aggregate return relative to the earlier M2241
candidate-retention panel across all five profiles:

| profile | M2241 selected return | M2250 selected return |
| --- | ---: | ---: |
| L0_current_masked | `49.55190` | `65.04845` |
| L1_one_step | `49.01157` | `64.18060` |
| L2_window_25 | `52.04593` | `66.95109` |
| L2_window_50 | `52.62991` | `66.95093` |
| L3_online_gru | `45.94770` | `57.93655` |

However, route-level readiness is still blocked:

```text
final_checkpoint_profile_floor_pass_count: 0
selected_checkpoint_profile_floor_pass_count: 0
selected local readiness rows: 4/15
```

Selected aggregate termination is mixed relative to M2241:

| profile | M2241 selected termination | M2250 selected termination |
| --- | ---: | ---: |
| L0_current_masked | `0.40625` | `0.42708` |
| L1_one_step | `0.42708` | `0.40625` |
| L2_window_25 | `0.40625` | `0.41667` |
| L2_window_50 | `0.39583` | `0.41667` |
| L3_online_gru | `0.47917` | `0.53125` |

## Classification

Primary classification:

```text
return_signal_improved_but_outcome_mode_unverified
```

Supported:

- The M2248 reward extension did not break training infrastructure.
- The repaired panel produces stronger selected-checkpoint return than M2241.
- Checkpoint retention should remain part of the current-sim training recipe.

Not supported:

- M2250 is comparison-ready.
- Return improvement proves offtrack repair.
- Any profile ranking, finite-window-vs-GRU verdict, paper-level result, or
  level3 self-identification claim.

## Route Decision

Route to selected-checkpoint outcome localization design:

```text
m2252-paper-route-current-sim-offtrack-recovery-corridor-selected-checkpoint-outcome-localization-design
```

Reason:

```text
M2250 changed training signal and improved selected returns, but readiness
remains below floor and termination movement is mixed. The next evidence gap is
episode-level outcome mode: whether the repaired selected checkpoints reduce
offtrack, trade failures into collision, or remain broadly unsupported.
```

The next localization should evaluate exactly the M2250 `15` selected
checkpoints over the same `32` public episodes per selected row. It should
compare failure-mode counts against M2244 only as repair-route evidence:

```text
M2244 baseline selected panel:
  success: 277/480
  offtrack: 110/480
  collision: 93/480
```

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
another repaired training run before outcome localization
```

## Next

Pre-register:

```text
m2252-paper-route-current-sim-offtrack-recovery-corridor-selected-checkpoint-outcome-localization-design
```
