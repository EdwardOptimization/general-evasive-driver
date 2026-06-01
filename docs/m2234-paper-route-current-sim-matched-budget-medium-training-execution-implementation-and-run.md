# M2234 Paper-Route Current-Sim Matched-Budget Medium Training Execution Implementation and Run

- status: completed
- decision: `current_sim_matched_budget_medium_training_execution_complete_route_to_result_audit`
- manifest: `experiments/manifests/m2234-paper-route-current-sim-matched-budget-medium-training-execution-implementation-and-run.json`
- run artifact: `runs/m2234_paper_route_current_sim_matched_budget_medium_training_execution/summary.json`
- implementation update: `src/autodrift/paper_route_current_sim_matched_budget_profile_training_execution.py`
- focused tests: `3 passed`

## Result

M2234 adapts the focused runner to accept an expected total-step budget and
executes the medium-v1 matched-budget profile/seed panel.

Key summary fields:

- result_class: `current_sim_matched_budget_profile_training_execution_pass`
- expected_total_steps: `32768`
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
- finite_window_vs_gru_conclusion_made: `false`
- paper_level_claim_made: `false`
- level3_self_id_claim_made: `false`
- runtime_seconds: `210.46644273702987`

M2234 necessarily starts training/PPO/environment rollout/policy action inside
train_ppo:

- training_started: `true`
- ppo_started: `true`
- environment_rollout_started: `true`
- policy_action_executed: `true`
- measured_rollout_started: `false`

## Profile Aggregate

The medium-v1 panel completes cleanly, but it still does not pass the
pre-registered readiness floor:

| profile | completed | passing seeds | readiness floor | eval return mean | eval termination mean |
| --- | ---: | ---: | --- | ---: | ---: |
| `L0_current_masked` | 3 | 1 | `false` | `49.347420291670154` | `0.40625` |
| `L1_one_step` | 3 | 1 | `false` | `48.73910562570327` | `0.4270833333333333` |
| `L2_window_25` | 3 | 1 | `false` | `49.40571122152958` | `0.46875` |
| `L2_window_50` | 3 | 1 | `false` | `49.956578630434215` | `0.4583333333333333` |
| `L3_online_gru` | 3 | 0 | `false` | `34.462087462071864` | `0.6458333333333334` |

quality_floor_profile_pass_count: `0`

This is not a controller-family ranking. The medium-v1 result improves some
aggregate means relative to short-v0, but the pre-registered readiness floor is
still not met by any profile. Downstream measured execution remains blocked.

## Artifacts

```text
runs/m2234_paper_route_current_sim_matched_budget_medium_training_execution/summary.json
runs/m2234_paper_route_current_sim_matched_budget_medium_training_execution/run_rows.csv
runs/m2234_paper_route_current_sim_matched_budget_medium_training_execution/profile_aggregate.csv
runs/m2234_paper_route_current_sim_matched_budget_medium_training_execution/command_matrix.csv
runs/m2234_paper_route_current_sim_matched_budget_medium_training_execution/run_state.json
```

Checkpoint root:

```text
runs/m2234_paper_route_current_sim_matched_budget_medium_training_execution/checkpoints/
```

## Interpretation Boundary

Allowed claim:

```text
M2234 cleanly executed the fixed medium-v1 matched-budget training panel and
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

Because medium-v1 also has `quality_floor_profile_pass_count=0`, the next audit
should decide whether to pivot to task/curriculum diagnosis, relax nothing and
run a synthesis, or design a more targeted training repair. It should not keep
blindly increasing budget without a reasoned route decision.

## Next

Pre-register:

```text
m2235-paper-route-current-sim-matched-budget-medium-training-execution-result-audit
```
