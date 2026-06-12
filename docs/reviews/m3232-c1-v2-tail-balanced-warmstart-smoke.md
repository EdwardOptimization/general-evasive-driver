# m3232-c1-v2-tail-balanced-warmstart-smoke Research Review

## Summary

- Generated at UTC: 20260612T062953Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: c1_v2_tail_balanced_quick_failed
- Decision reason: Failed: C1 v2 quick replayed all demos and wrote checkpoint/dataset but failed validation action-MSE gate (0.291470 vs <=0.12; zero-action baseline 0.559903); C1 remains open and next C1 step should synthesize/reprice before more local BC repair.

## Hypothesis

A revised C1 v2 tail-balanced oracle-demo and behavior-cloning warm-start quick smoke can freeze rare-tail support/probe rows, replay structured A3 oracle demos, and exercise the BC checkpoint/dataset path before validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result feasibility-proof or self-ID claim.

## Lineage

- parent_checkpoint: docs/roadmap-phase3-codex-execution.md, docs/current-status.md, docs/m3228-c1-c5prime-oracle-demo-bc-warmstart.md, docs/m3229-c1-bc-warmstart-failure-localization.md, docs/m3231-d1b-chrono-native-oracle-pricing-full.md
- parent_dataset: runs/feasibility_audit/c5prime_target_consolidation/episode_rows.csv, experiments/feasibility_audit/c5prime_c1_oracle_bc_v2_prereg.json
- parent_config: scripts/feasibility_audit/c5prime_c1_oracle_bc_warmstart.py, experiments/feasibility_audit/c5prime_prereg.json, experiments/feasibility_audit/c5prime_c1_oracle_bc_v2_prereg.json
- parent_objective: revise the C1 warm-start design after M3229 localized the M3228 failure to tail-action generalization
- derived_from: M3222 A3 C5-prime target consolidation, M3228 failed C1 warm-start gate, M3229 failure localization: held-out tail-action generalization dominates, M3231 D1b direction-positive CP-2 precondition satisfied
- blocked_by: C1 remains open; M3228 full and M3232 v2 quick both failed action-MSE gates, so another local warm-start repair needs synthesis/repricing first
- supersedes: the v2 quick-smoke pending state only; it does not supersede the C1 OPEN roadmap status
- invalidates: re-running M3228 unchanged after the tail-action generalization failure, starting C2 from M3228 failed checkpoint or from a quick-only artifact

## Success Criteria

- experiments/feasibility_audit/c5prime_c1_oracle_bc_v2_prereg.json exists before quick rollout
- v2 preregistration contains rare_tail_train_support and rare_tail_validation_probe rows for coast_steer_+0.7 and coast_steer_-0.7
- experiments/feasibility_audit/c5prime_c1_oracle_bc_warmstart_v2_quick.json exists with revision v2_tail_balanced
- quick summary gates.all_passed is true
- quick run writes a dataset NPZ and checkpoint PT under the v2 quick run directory
- the result document separates measured artifacts from inferred interpretation and keeps C1 open

## Failure Criteria

- quick C1 v2 rollout starts without frozen v2 preregistration
- rare-tail support/probe rows are absent from the v2 preregistration
- a selected structured-oracle quick demo does not replay to success
- selection or validation role frames are used for BC training
- quick validation action-MSE gate fails
- the milestone runs PPO, mutates the incumbent, changes actor-input shape, or claims driver performance

## Evidence Gates

- M3232 must use the v2 preregistration frozen before the quick rollout
- M3232 must preserve the original C1 validation action-MSE gate instead of relaxing criteria
- M3232 must include rare coast-steer train support and validation probe rows in the v2 preregistration
- M3232 must run only quick-mode behavior pretraining; it must not admit C2
- M3232 must write quick summary, checkpoint, and dataset artifacts under the v2 run directory
- M3232 must not run PPO, mutate ActiveSafetyReflexDriver, or make a driver-performance claim

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not touch ActiveSafetyReflexDriver
- do not invoke train_ppo or create a guarded-RL checkpoint
- do not train on selection or validation role frames
- do not relax the validation action-MSE gate after M3228 failed
- do not mark C1 complete from a quick smoke
- do not claim current-sim validation, high-fidelity sufficiency, promotion readiness, or self-ID

## Failure Taxonomy

- metric_artifact

## Scoreboard

- milestone: m3232-c1-v2-tail-balanced-warmstart-smoke
- type: infrastructure
- checkpoint: experiments/feasibility_audit/c5prime_c1_oracle_bc_warmstart_v2_quick.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: c1_v2_tail_balanced_quick_failed
- reason: Failed: C1 v2 quick replayed all demos and wrote checkpoint/dataset but failed validation action-MSE gate (0.291470 vs <=0.12; zero-action baseline 0.559903); C1 remains open and next C1 step should synthesize/reprice before more local BC repair.

## Next Blocker

C1 remains open; because M3228 full and M3232 quick both failed action-MSE gates, the next C1 step should be synthesis/repricing rather than another local BC repair.
