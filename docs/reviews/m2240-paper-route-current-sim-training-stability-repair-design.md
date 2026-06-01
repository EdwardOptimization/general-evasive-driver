# m2240-paper-route-current-sim-training-stability-repair-design Research Review

## Summary

- Generated at UTC: 20260601T144316Z
- Type: gate
- Gate tier: process
- Promotion decision: current_sim_training_stability_repair_design_admit_candidate_checkpoint_execution
- Decision reason: M2240 freezes same-budget periodic checkpoint repair checkpoint_interval 4096 candidate count 120 selected rows 15 no ranking claims

## Hypothesis

A training-stability repair design can address M2238 late-regression evidence more directly than another blind budget increase.

## Lineage

- parent_checkpoint: not_applicable_design_only
- parent_dataset: docs/m2239-paper-route-current-sim-task-curriculum-readiness-diagnosis-result-audit.md, runs/m2238_paper_route_current_sim_task_curriculum_readiness_diagnosis/summary.json, runs/m2238_paper_route_current_sim_task_curriculum_readiness_diagnosis/training_plateau.csv, runs/m2238_paper_route_current_sim_task_curriculum_readiness_diagnosis/budget_delta.csv
- parent_config: experiments/manifests/m2239-paper-route-current-sim-task-curriculum-readiness-diagnosis-result-audit.json
- parent_objective: design a non-training repair route for M2238 late-regression and below-floor readiness evidence
- derived_from: m2239-paper-route-current-sim-task-curriculum-readiness-diagnosis-result-audit
- blocked_by: M2238/M2239 block another blind budget escalation and route to training stability repair design
- supersedes: directly increasing total_steps again, ranking below-floor profile checkpoints, changing actor inputs to recover readiness
- invalidates: None

## Success Criteria

- docs/m2240-paper-route-current-sim-training-stability-repair-design.md exists
- repair design specifies checkpoint retention or best-checkpoint selection
- repair design preserves actor input contract and matched profile/seed fairness
- repair design defines readiness floors and guardrails for any follow-up execution
- fallback route is explicit
- no reset rollout measured execution training replay PPO private holdout ranking paper-level finite-window-vs-GRU or level3 claim is made

## Failure Criteria

- design requires actor input contract changes
- design is just another total_steps increase
- checkpoint retention/readiness gates are unspecified
- M2240 starts new training, reset, rollout, measured execution, replay, PPO, or private holdout
- M2240 ranks profiles or selects a winner

## Evidence Gates

- M2240 must design a training-stability repair without executing training
- M2240 must preserve the human-view/no-privileged actor input contract
- M2240 must specify checkpoint retention or best-checkpoint selection criteria before execution
- M2240 must keep controller-family ranking, winner selection, finite-window-vs-GRU, paper-level, and self-ID claims blocked
- M2240 must include a fallback route if checkpoint-selection repair is insufficient

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

- training_instability
- seed_fragility
- metric_artifact
- scenario_sampling_failure

## Scoreboard

- milestone: m2240-paper-route-current-sim-training-stability-repair-design
- type: gate
- checkpoint: docs/m2240-paper-route-current-sim-training-stability-repair-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: current_sim_training_stability_repair_design_admit_candidate_checkpoint_execution
- reason: M2240 freezes same-budget periodic checkpoint repair checkpoint_interval 4096 candidate count 120 selected rows 15 no ranking claims

## Next Blocker

m2240-paper-route-current-sim-training-stability-repair-design
