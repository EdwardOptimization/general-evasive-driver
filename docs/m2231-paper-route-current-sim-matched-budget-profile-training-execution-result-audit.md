# M2231 Paper-Route Current-Sim Matched-Budget Profile Training Execution Result Audit

- status: completed
- decision: `current_sim_matched_budget_training_complete_but_below_floor_route_to_medium_budget_design`
- manifest: `experiments/manifests/m2231-paper-route-current-sim-matched-budget-profile-training-execution-result-audit.json`
- parent result: `runs/m2230_paper_route_current_sim_matched_budget_profile_training_execution/summary.json`
- parent aggregate: `runs/m2230_paper_route_current_sim_matched_budget_profile_training_execution/profile_aggregate.csv`

## Audit Result

M2230 is a clean execution result:

- result_class: `current_sim_matched_budget_profile_training_execution_pass`
- completed_run_count: `15`
- failed_run_count: `0`
- expected_run_count: `15`
- all_selected_metrics_finite: `true`
- budget_signature_count: `1`
- budget_matched: `true`
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

M2230 is not a comparison-ready training result:

- quality_floor_profile_pass_count: `0`
- all five profiles have fewer than `2/3` seeds passing the pre-registered
  readiness floor.
- downstream measured execution remains blocked.
- controller-family ranking remains blocked.
- finite-window-vs-GRU conclusion remains blocked.
- self-identification claims remain blocked.

## Classification

This is not an implementation failure and not a contract failure. It is a
training-readiness floor failure:

```text
the fixed short-v0 budget produces complete finite checkpoints,
but the checkpoints are too weak or too seed-fragile for downstream comparison.
```

The most likely immediate cause is insufficient public training budget and/or
short-v0 training recipe weakness, not evidence that any controller family has
won or lost. Several profiles have one seed above the readiness floor, so the
right next step is a matched-budget medium-v1 training design, not ranking or
task-quality changes.

## Route Decision

Admit a medium-budget design milestone:

```text
m2232-paper-route-current-sim-matched-budget-medium-training-design
```

M2232 should keep the same core comparison discipline:

- same five trainable profiles;
- same seed IDs, to isolate training-budget effects;
- no profile-specific hyperparameter tuning;
- no actor input changes;
- no private holdout;
- no winner selection;
- no paper-level claim.

Design target:

```text
total_steps_per_seed = 32768
rollout_steps = 128
num_envs = 4
update_epochs = 2
minibatch_size = 256
learning_rate = 0.0001
clip_coef = 0.1
max_grad_norm = 0.25
eval_episodes = 32
```

The readiness floor should remain:

```text
at least 2/3 seeds per profile with eval_termination_rate <= 0.4
and eval_return_mean >= 50.0
```

This preserves the same admission standard while testing whether the short-v0
panel was undertrained.

## Blocked Claims

M2231 does not admit:

```text
controller-family ranking
winner selection
finite-window-vs-GRU conclusion
paper-level result
level3 self-identification
measured execution from M2230 checkpoints
private holdout
```

## Next

Pre-register:

```text
m2232-paper-route-current-sim-matched-budget-medium-training-design
```
