# m2243-paper-route-current-sim-selected-checkpoint-outcome-localization-design Research Review

## Summary

- Generated at UTC: 20260601T150928Z
- Type: gate
- Gate tier: process
- Promotion decision: current_sim_selected_checkpoint_outcome_localization_design_admit_execution
- Decision reason: M2243 freezes selected-checkpoint outcome localization 480 episodes fields groups repair route logic no ranking claims

## Hypothesis

An episode-level outcome localization design over M2241 selected checkpoints can identify the repair target more reliably than immediate reward/task training.

## Lineage

- parent_checkpoint: runs/m2241_paper_route_current_sim_training_stability_repair_execution/selected_checkpoint_rows.csv
- parent_dataset: docs/m2242-paper-route-current-sim-training-stability-repair-result-audit.md, runs/m2241_paper_route_current_sim_training_stability_repair_execution/summary.json, runs/m2241_paper_route_current_sim_training_stability_repair_execution/selected_checkpoint_rows.csv, runs/m2241_paper_route_current_sim_training_stability_repair_execution/profile_aggregate.csv
- parent_config: experiments/manifests/m2242-paper-route-current-sim-training-stability-repair-result-audit.json
- parent_objective: design selected-checkpoint episode-level outcome localization before reward/task/curriculum repair
- derived_from: m2242-paper-route-current-sim-training-stability-repair-result-audit
- blocked_by: M2241 selected checkpoints improve final in 12/15 rows but selected_checkpoint_profile_floor_pass_count remains 0
- supersedes: another checkpoint-selection-only run, direct reward/curriculum training without outcome localization, ranking selected checkpoints below readiness floor
- invalidates: None

## Success Criteria

- docs/m2243-paper-route-current-sim-selected-checkpoint-outcome-localization-design.md exists
- selected checkpoint input source is specified
- episode-level outcome fields are specified
- grouping axes and minimum support rules are specified
- execution guardrails are specified
- no reset rollout measured execution training replay PPO private holdout ranking paper-level finite-window-vs-GRU or level3 claim is made

## Failure Criteria

- selected checkpoint inputs are ambiguous
- outcome fields are insufficient to guide repair
- M2243 starts rollout, training, replay, PPO, measured execution, or private holdout
- M2243 ranks profiles or selects a winner

## Evidence Gates

- M2243 must design outcome localization over M2241 selected checkpoints without running rollout
- M2243 must specify episode-level outcome fields and grouping axes before execution
- M2243 must keep ranking, winner selection, paper, finite-window-vs-GRU, and self-ID claims blocked
- M2243 must not train or change actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run environment reset
- do not run environment rollout
- do not execute policy actions
- do not run measured execution
- do not run replay
- do not run PPO
- do not use private holdout
- do not promote any checkpoint
- do not rank controller families
- do not select a winner
- do not change actor input contract
- do not claim paper-level evidence
- do not claim finite-window vs GRU conclusion
- do not claim level3 self-identification

## Failure Taxonomy

- scenario_sampling_failure
- training_instability
- seed_fragility
- metric_artifact

## Scoreboard

- milestone: m2243-paper-route-current-sim-selected-checkpoint-outcome-localization-design
- type: gate
- checkpoint: docs/m2243-paper-route-current-sim-selected-checkpoint-outcome-localization-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: current_sim_selected_checkpoint_outcome_localization_design_admit_execution
- reason: M2243 freezes selected-checkpoint outcome localization 480 episodes fields groups repair route logic no ranking claims

## Next Blocker

m2243-paper-route-current-sim-selected-checkpoint-outcome-localization-design
