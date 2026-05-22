# m248-source-balanced-ppo-smoke-from-m239 Research Review

## Summary

- Generated at UTC: 20260522T143653Z
- Type: driver_candidate
- Gate tier: proof
- Promotion decision: reject_protected_key_source_regression
- Decision reason: M248 aggregate M232 and M223 source improve strongly but every interpolation alpha regresses protected-key source above +1e-8; proof and behavior gates were not run

## Hypothesis

Starting from M239 with source-balanced outcome losses should prevent the M243-style protected-key source regression while preserving M223 improvement pressure.

## Lineage

- parent_checkpoint: runs/m239_m224_to_m237_interpolation/checkpoints/alpha_0_5.pt
- parent_dataset: runs/m223_m219_boundary_outcome_corpus_seed10060/boundary_outcome_corpus.npz, runs/m231_protected_key_snippet_surface/protected_key_snippets.npz, runs/m232_combined_m223_m231_snippet_anchor/outcome_intervention_snippets.npz, runs/m235_closed_loop_trajectory_anchor_surface/trajectory_anchor.npz
- parent_config: configs/ppo_m248_source_balanced_from_m239_smoke.json
- parent_objective: source-balanced outcome intervention losses, M245 exact source-aware gate, post-PPO interpolation guard, full proof and behavior retention
- derived_from: m247-source-balanced-outcome-loss-implementation
- blocked_by: m247-source-balanced-outcome-loss-implementation
- supersedes: None
- invalidates: None

## Success Criteria

- run exactly one 1024-step PPO smoke from M239 alpha 0.5
- interpolate from M239 to the raw PPO checkpoint without additional training
- select only an alpha with protected_key source delta <= +1e-8
- selected alpha must have M223 source delta < 0 and aggregate M232 delta <= +1e-8
- selected alpha must pass full replay gates protected key and behavior retention

## Failure Criteria

- raw PPO or all interpolation alphas regress protected-key source above +1e-8
- no alpha improves M223 source
- no alpha passes aggregate M232 exact gate
- no alpha passes full replay gates
- change the actor input contract

## Evidence Gates

- fresh 1024-step source-balanced PPO smoke from M239
- post-PPO checkpoint interpolation sweep
- M245 exact source-aware objective gate
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
- do not run proof gates if the exact source gate fails
- do not loosen protected-key thresholds
- do not change actor inputs

## Failure Taxonomy

- proof_washout
- objective_overfit
- promotion_gate_failure

## Scoreboard

- milestone: m248-source-balanced-ppo-smoke-from-m239
- type: driver_candidate
- checkpoint: runs/ppo_m248_source_balanced_from_m239_seed5224/checkpoint.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: reject_protected_key_source_regression
- reason: M248 aggregate M232 and M223 source improve strongly but every interpolation alpha regresses protected-key source above +1e-8; proof and behavior gates were not run

## Next Blocker

Audit protected-key source gradient before more PPO.
