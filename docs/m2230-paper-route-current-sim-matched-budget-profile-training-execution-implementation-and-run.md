# M2230 Paper-Route Current-Sim Matched-Budget Profile Training Execution Implementation and Run

- status: completed
- decision: `current_sim_matched_budget_profile_training_execution_complete_route_to_result_audit`
- manifest: `experiments/manifests/m2230-paper-route-current-sim-matched-budget-profile-training-execution-implementation-and-run.json`
- run artifact: `runs/m2230_paper_route_current_sim_matched_budget_profile_training_execution/summary.json`
- implementation: `src/autodrift/paper_route_current_sim_matched_budget_profile_training_execution.py`
- focused tests: `2 passed`

## Result

M2230 implements the focused runner and executes the frozen M2227
matched-budget profile/seed panel.

Key summary fields:

- result_class: `current_sim_matched_budget_profile_training_execution_pass`
- expected_run_count: `15`
- planned_run_count: `15`
- completed_run_count: `15`
- failed_run_count: `0`
- profile_count: `5`
- seed_count: `3`
- checkpoint count: `15`
- all_selected_metrics_finite: `true`
- budget_signature_count: `1`
- budget_matched: `true`
- profile_set_matched: `true`
- seed_set_matched: `true`
- missing_config_count: `0`
- contract_violation_count: `0`
- config_budget_violation_count: `0`
- guardrail_violation_count: `0`
- private_holdout_used: `false`
- profile_specific_tuning: `false`
- winner_selected: `false`
- ranking_admissible_count: `0`
- controller_family_ranking_claim_made: `false`
- finite_window_vs_gru_conclusion_made: `false`
- paper_level_claim_made: `false`
- level3_self_id_claim_made: `false`
- runtime_seconds: `78.78890041913837`

M2230 necessarily starts training, PPO, environment rollout, and policy action
execution inside train_ppo:

- training_started: `true`
- ppo_started: `true`
- environment_rollout_started: `true`
- policy_action_executed: `true`
- measured_rollout_started: `false`

## Profile Aggregate

The pre-registered readiness floor is:

```text
at least 2/3 seeds per profile with eval_termination_rate <= 0.4
and eval_return_mean >= 50.0
```

M2230 completion is clean, but readiness is weak:

| profile | completed | passing seeds | readiness floor | eval return mean | eval termination mean |
| --- | ---: | ---: | --- | ---: | ---: |
| `L0_current_masked` | 3 | 1 | `false` | `40.82208296806885` | `0.6354166666666666` |
| `L1_one_step` | 3 | 1 | `false` | `41.01134007799829` | `0.65625` |
| `L2_window_25` | 3 | 1 | `false` | `48.598540168844494` | `0.4791666666666667` |
| `L2_window_50` | 3 | 1 | `false` | `48.59846665023459` | `0.4791666666666667` |
| `L3_online_gru` | 3 | 0 | `false` | `39.637494059841835` | `0.6666666666666666` |

quality_floor_profile_pass_count: `0`

This is not a controller-family ranking. It is a training-completion and
readiness-floor report. The result says the matched-budget short-v0 training
panel completed, but none of the profiles is ready for downstream measured
execution or finite-window-vs-GRU comparison under the pre-registered floor.

## Artifacts

```text
runs/m2230_paper_route_current_sim_matched_budget_profile_training_execution/summary.json
runs/m2230_paper_route_current_sim_matched_budget_profile_training_execution/run_rows.csv
runs/m2230_paper_route_current_sim_matched_budget_profile_training_execution/profile_aggregate.csv
runs/m2230_paper_route_current_sim_matched_budget_profile_training_execution/command_matrix.csv
runs/m2230_paper_route_current_sim_matched_budget_profile_training_execution/run_state.json
```

Checkpoint root:

```text
runs/m2230_paper_route_current_sim_matched_budget_profile_training_execution/checkpoints/
```

## Interpretation Boundary

Allowed claim:

```text
M2230 cleanly executed the fixed matched-budget short-v0 training panel and
produced complete finite public training/eval artifacts.
```

Blocked claims:

```text
controller-family ranking
winner selection
finite-window-vs-GRU conclusion
paper-level result
level3 self-identification
downstream measured-execution readiness
```

The immediate blocker is now result interpretation and routing. Because
`quality_floor_profile_pass_count=0`, M2231 must audit whether the right next
step is training recipe/curriculum repair, longer matched-budget training,
task-quality adjustment, or a bounded negative-result branch synthesis.

## Next

Pre-register:

```text
m2231-paper-route-current-sim-matched-budget-profile-training-execution-result-audit
```

M2231 should audit M2230 without rerunning training and without ranking
profiles.
