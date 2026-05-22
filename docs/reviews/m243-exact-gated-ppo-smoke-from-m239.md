# m243-exact-gated-ppo-smoke-from-m239 Research Review

## Summary

- Generated at UTC: 20260522T140701Z
- Type: driver_candidate
- Gate tier: proof
- Promotion decision: reject_exact_m232_regression
- Decision reason: M243 exact objective gate rejects all alphas because M223 improves but combined M232 regresses; proof and behavior gates not run

## Hypothesis

Starting from the M239 public-gate base and using exact full-corpus objective gates should make PPO continuation decisions more reliable than the M237/M240 sampled fixed-batch workflow.

## Lineage

- parent_checkpoint: runs/m239_m224_to_m237_interpolation/checkpoints/alpha_0_5.pt
- parent_dataset: runs/m232_combined_m223_m231_snippet_anchor/outcome_intervention_snippets.npz, runs/m235_closed_loop_trajectory_anchor_surface/trajectory_anchor.npz
- parent_config: configs/ppo_m237_trajectory_anchor_from_m224_smoke.json
- parent_objective: exact full-corpus M232/M223 objective gate, post-PPO checkpoint interpolation guard, full proof and behavior retention
- derived_from: m242-exact-outcome-objective-evaluator
- blocked_by: m240-interpolation-guarded-ppo-repeat-from-m224
- supersedes: None
- invalidates: None

## Success Criteria

- run exactly one 1024-step PPO smoke from M239 alpha 0.5
- interpolate from M239 to the raw PPO checkpoint without additional training
- select only an alpha that improves exact M232 or does not regress it while improving exact M223
- selected alpha must pass full replay gates protected key and behavior retention
- record whether exact-objective-gated continuation is viable

## Failure Criteria

- raw PPO or all interpolation alphas regress exact M232 materially
- no alpha passes protected key
- no alpha passes full replay gates
- selected alpha regresses behavior materially
- change the actor input contract

## Evidence Gates

- fresh 1024-step PPO smoke from M239 public-gate base
- post-PPO checkpoint interpolation sweep
- exact full-corpus M232/M223 objective evaluation
- M183 M168 and M170 replay gates
- M193 M189 replay gate
- M212 M204 replay gate
- M223 M219 replay gate
- protected key 9944 guard
- behavior seeds 9505 and 9506
- research validator

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not promote raw PPO without interpolation gates
- do not use sampled fixed-batch objective as the primary objective gate
- do not run more than one PPO smoke in M243
- do not loosen replay or protected-key thresholds
- do not change actor inputs

## Failure Taxonomy

- objective_overfit
- promotion_gate_failure

## Scoreboard

- milestone: m243-exact-gated-ppo-smoke-from-m239
- type: driver_candidate
- checkpoint: runs/ppo_m243_exact_gated_from_m239_seed5223/checkpoint.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: reject_exact_m232_regression
- reason: M243 exact objective gate rejects all alphas because M223 improves but combined M232 regresses; proof and behavior gates not run

## Next Blocker

Audit protected-key versus M223 per-row objective conflict before more PPO.
