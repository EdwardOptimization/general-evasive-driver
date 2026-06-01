# m2253-paper-route-current-sim-offtrack-recovery-corridor-selected-checkpoint-outcome-localization-implementation Research Review

## Summary

- Generated at UTC: 20260601T165130Z
- Type: infrastructure
- Gate tier: process
- Promotion decision: current_sim_offtrack_recovery_corridor_selected_checkpoint_outcome_localization_pass_route_to_branch_synthesis
- Decision reason: M2253 pass 480 rows success/offtrack/collision 269/118/93 offtrack still dominant no ranking claims

## Hypothesis

Episode-level outcome localization over M2250 selected checkpoints can identify whether the reward repair changed the offtrack-dominated failure mode.

## Lineage

- parent_checkpoint: runs/m2250_paper_route_current_sim_offtrack_recovery_corridor_training_execution/selected_checkpoint_rows.csv
- parent_dataset: docs/m2252-paper-route-current-sim-offtrack-recovery-corridor-selected-checkpoint-outcome-localization-design.md, runs/m2250_paper_route_current_sim_offtrack_recovery_corridor_training_execution/selected_checkpoint_rows.csv, runs/m2250_paper_route_current_sim_offtrack_recovery_corridor_training_execution/profile_aggregate.csv, runs/m2244_paper_route_current_sim_selected_checkpoint_outcome_localization/summary.json
- parent_config: experiments/manifests/m2252-paper-route-current-sim-offtrack-recovery-corridor-selected-checkpoint-outcome-localization-design.json
- parent_objective: run episode-level outcome localization over M2250 selected checkpoints
- derived_from: m2252-paper-route-current-sim-offtrack-recovery-corridor-selected-checkpoint-outcome-localization-design
- blocked_by: M2252 admits M2250 selected-checkpoint outcome localization execution
- supersedes: another repaired training run before outcome localization, return-only repair interpretation, ranking repaired selected checkpoints
- invalidates: None

## Success Criteria

- runs/m2253_paper_route_current_sim_offtrack_recovery_corridor_selected_checkpoint_outcome_localization/summary.json exists
- episode_row_count is 480
- selected_checkpoint_count is 15
- profile_seed groups each have 32 episodes
- outcome and termination aggregates exist
- repair_route_candidates.csv exists
- guardrail_violation_count is 0
- ranking_admissible_count is 0
- winner_selected is false
- paper_level_claim_made is false
- finite_window_vs_gru_conclusion_made is false
- level3_self_id_claim_made is false

## Failure Criteria

- selected checkpoint rows are missing
- episode rows are incomplete
- outcome_bucket or termination_reason fields are missing
- repair route candidates are ambiguous
- M2253 trains promotes uses private holdout ranks profiles or selects a winner

## Evidence Gates

- M2253 must evaluate exactly the 15 M2250 selected checkpoints
- M2253 must emit 480 episode rows with outcome_bucket and termination_reason
- M2253 must aggregate by profile profile+seed outcome bucket and termination reason
- M2253 must classify repair-route candidates without ranking profiles
- M2253 must not train replay PPO promote use private holdout or claim paper/self-ID evidence

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not alter checkpoints
- do not change actor input contract
- do not drop selected checkpoints
- do not drop seeds
- do not use private holdout
- do not promote any checkpoint
- do not rank controller families
- do not select a winner
- do not claim paper-level evidence
- do not claim finite-window vs GRU conclusion
- do not claim level3 self-identification

## Failure Taxonomy

- scenario_sampling_failure
- metric_artifact
- training_instability
- seed_fragility
- behavior_regression

## Scoreboard

- milestone: m2253-paper-route-current-sim-offtrack-recovery-corridor-selected-checkpoint-outcome-localization-implementation
- type: infrastructure
- checkpoint: runs/m2253_paper_route_current_sim_offtrack_recovery_corridor_selected_checkpoint_outcome_localization/summary.json
- success_rate: 0.5604166666666667
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: current_sim_offtrack_recovery_corridor_selected_checkpoint_outcome_localization_pass_route_to_branch_synthesis
- reason: M2253 pass 480 rows success/offtrack/collision 269/118/93 offtrack still dominant no ranking claims

## Next Blocker

m2253-paper-route-current-sim-offtrack-recovery-corridor-selected-checkpoint-outcome-localization-implementation
