# m2249-paper-route-current-sim-offtrack-recovery-corridor-training-execution-design Research Review

## Summary

- Generated at UTC: 20260601T155859Z
- Type: gate
- Gate tier: process
- Promotion decision: current_sim_offtrack_recovery_corridor_training_execution_design_admit_execution
- Decision reason: M2249 freezes M2250 command over M2248 matrix using candidate-checkpoint runner no training/ranking claims

## Hypothesis

A controlled execution design can run the M2248 repaired config matrix through the existing candidate-checkpoint runner without ranking or paper claims.

## Lineage

- parent_checkpoint: not_applicable_design_only
- parent_dataset: docs/m2248-paper-route-current-sim-offtrack-recovery-corridor-reward-extension-materialization.md, runs/m2248_paper_route_current_sim_offtrack_recovery_corridor_reward_extension_materialization/summary.json, runs/m2248_paper_route_current_sim_offtrack_recovery_corridor_reward_extension_materialization/training_matrix.csv
- parent_config: experiments/manifests/m2248-paper-route-current-sim-offtrack-recovery-corridor-reward-extension-materialization.json
- parent_objective: design a controlled training execution over M2248 repaired configs
- derived_from: m2248-paper-route-current-sim-offtrack-recovery-corridor-reward-extension-materialization
- blocked_by: M2248 materialized configs but did not run training
- supersedes: ad-hoc manual training from repaired configs, running repaired configs without candidate checkpoint evaluation, ranking before readiness floors
- invalidates: None

## Success Criteria

- docs/m2249-paper-route-current-sim-offtrack-recovery-corridor-training-execution-design.md exists
- design references the M2248 training matrix
- design fixes output dir, task id, next blocker, and guardrails
- design keeps candidate checkpoint evaluation
- no reset rollout measured execution training replay private holdout ranking paper-level finite-window-vs-GRU or level3 claim is made

## Failure Criteria

- design starts training
- design uses a matrix other than M2248
- candidate checkpoint retention is omitted
- design ranks profiles or selects a winner
- design changes actor input contract or widens track_width

## Evidence Gates

- M2249 must design training execution without running training
- M2249 must use exactly the M2248 training matrix
- M2249 must keep the 5-profile x 3-seed matched panel
- M2249 must keep candidate-checkpoint retention and selected-checkpoint evaluation
- M2249 must keep ranking, winner selection, paper claims, finite-window-vs-GRU, and self-ID claims blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run environment reset
- do not run environment rollout
- do not execute policy actions
- do not run measured execution
- do not run replay
- do not run PPO outside the pre-registered training runner
- do not use private holdout
- do not promote any checkpoint
- do not rank controller families
- do not select a winner
- do not change actor observation contract
- do not widen track_width
- do not claim paper-level evidence
- do not claim finite-window vs GRU conclusion
- do not claim level3 self-identification

## Failure Taxonomy

- training_instability
- behavior_regression
- scenario_sampling_failure
- metric_artifact

## Scoreboard

- milestone: m2249-paper-route-current-sim-offtrack-recovery-corridor-training-execution-design
- type: gate
- checkpoint: docs/m2249-paper-route-current-sim-offtrack-recovery-corridor-training-execution-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: current_sim_offtrack_recovery_corridor_training_execution_design_admit_execution
- reason: M2249 freezes M2250 command over M2248 matrix using candidate-checkpoint runner no training/ranking claims

## Next Blocker

m2249-paper-route-current-sim-offtrack-recovery-corridor-training-execution-design
