# m2234-paper-route-current-sim-matched-budget-medium-training-execution-implementation-and-run Research Review

## Summary

- Generated at UTC: 20260601T134848Z
- Type: infrastructure
- Gate tier: generalization
- Promotion decision: pending
- Decision reason: M2234 pending 32768-step focused runner adaptation and 15 medium-v1 profile/seed training jobs no ranking claims

## Hypothesis

The M2233 medium-v1 matched-budget profile configs can be executed as 15 fixed train_ppo jobs with clean contract checks and finite post-training metrics, testing whether short-v0 was undertrained.

## Lineage

- parent_checkpoint: none
- parent_dataset: runs/m2233_paper_route_current_sim_matched_budget_medium_training_configs/training_matrix.csv, configs/paper_route_profiles/m2233_matched_budget_medium_v1, docs/m2233-paper-route-current-sim-matched-budget-medium-training-config-materialization.md
- parent_config: experiments/manifests/m2233-paper-route-current-sim-matched-budget-medium-training-config-materialization.json
- parent_objective: adapt runner for medium-v1 expected budget and run exactly 15 matched-budget profile training jobs
- derived_from: m2233-paper-route-current-sim-matched-budget-medium-training-config-materialization
- blocked_by: M2233 materialized medium-v1 configs and command matrix without training
- supersedes: manual train_ppo execution for medium-v1 profile comparison
- invalidates: None

## Success Criteria

- runs/m2234_paper_route_current_sim_matched_budget_medium_training_execution/summary.json exists
- run_rows.csv exists
- profile_aggregate.csv exists
- command_matrix.csv exists
- expected_run_count is 15
- completed_run_count is 15
- failed_run_count is 0
- budget_signature_count is 1
- contract_violation_count is 0
- all_selected_metrics_finite is true
- private_holdout_used is false
- profile_specific_tuning is false
- winner_selected is false
- no promotion, ranking, paper-level finite-window-vs-GRU or level3 self-ID claim is made

## Failure Criteria

- any train_ppo subprocess fails
- any expected checkpoint or eval summary is missing
- budget/profile/seed/contract drift is detected
- metrics are non-finite
- failed profile/seed rows are omitted
- results are framed as architecture ranking or self-identification evidence before audit

## Evidence Gates

- M2234 may adapt the focused execution adapter to accept expected total_steps 32768 and run exactly the 15 M2233 profile/seed configs
- M2234 must preserve frozen profiles, seeds, budgets, and actor input contract
- M2234 must fail closed on missing configs, contract violations, nonzero train_ppo return codes, missing checkpoints, missing eval summaries, or non-finite selected metrics
- M2234 must write run rows, profile aggregates, summary, command matrix, and run_state
- M2234 must not rank controller families, select a winner, promote a checkpoint, claim paper-level evidence, claim finite-window-vs-GRU evidence, or claim level3 self-identification

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not change profile-specific budgets
- do not change seed policy
- do not add hidden or oracle actor inputs
- do not use private holdout
- do not run measured execution
- do not run replay gates
- do not promote any checkpoint
- do not rank controller families
- do not select a winner
- do not claim paper-level evidence
- do not claim finite-window vs GRU conclusion
- do not claim level3 self-identification

## Failure Taxonomy

- lineage_invalid
- contract_violation
- training_instability
- metric_artifact

## Scoreboard

- milestone: m2234-paper-route-current-sim-matched-budget-medium-training-execution-implementation-and-run
- type: infrastructure
- checkpoint: runs/m2234_paper_route_current_sim_matched_budget_medium_training_execution/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: pending
- reason: M2234 pending 32768-step focused runner adaptation and 15 medium-v1 profile/seed training jobs no ranking claims

## Next Blocker

m2234-paper-route-current-sim-matched-budget-medium-training-execution-implementation-and-run
