# m254-exact-source-gated-ppo-smoke-from-m253 Research Review

## Summary

- Generated at UTC: 20260522T150741Z
- Type: driver_candidate
- Gate tier: proof
- Promotion decision: reject_protected_key_source_regression
- Decision reason: M254 PPO completes and aggregate/M223 exact losses improve but every interpolated alpha regresses protected-key source above +1e-8 so proof gates are skipped

## Hypothesis

Starting PPO from the source-calibrated M253 base may reduce the protected-key regression seen in M248, allowing a small PPO smoke to improve M223 and aggregate exact source loss without protected-key source regression.

## Lineage

- parent_checkpoint: runs/m252_alpha_boundary_interpolation/checkpoints/alpha_0_00008.pt
- parent_dataset: runs/m223_m219_boundary_outcome_corpus_seed10060/boundary_outcome_corpus.npz, runs/m231_protected_key_snippet_surface/protected_key_snippets.npz, runs/m232_combined_m223_m231_snippet_anchor/outcome_intervention_snippets.npz, runs/m235_closed_loop_trajectory_anchor_surface/trajectory_anchor.npz
- parent_config: configs/ppo_m248_source_balanced_from_m239_smoke.json, docs/m253-full-public-gate-for-m252-a0-00008.md
- parent_objective: source-balanced exact objective PPO smoke with existing snippet and trajectory anchors
- derived_from: m253-full-public-gate-for-m252-a0-00008
- blocked_by: m253-full-public-gate-for-m252-a0-00008
- supersedes: None
- invalidates: None

## Success Criteria

- 1024-step PPO smoke completes from M253
- post-PPO interpolation includes at least alpha 0.1, 0.25, 0.5, 0.75, and 1.0
- at least one alpha improves M223 source loss and aggregate M232 without protected-key source regression above +1e-8
- run proof and behavior gates only for alphas that pass the exact source gate
- no actor-input contract changes

## Failure Criteria

- PPO fails to complete
- all alphas regress protected-key source loss
- any exact-gated alpha fails proof retention
- behavior materially regresses

## Evidence Gates

- 1024-step PPO smoke from M253
- post-PPO interpolation sweep
- M245 exact source-aware objective gate
- public proof gates only if exact source gate passes
- research validator

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run longer PPO before the smoke passes
- do not ignore protected-key source regression
- do not run proof gates if exact source gate fails
- do not change actor inputs

## Failure Taxonomy

- objective_overfit
- proof_washout
- promotion_gate_failure

## Scoreboard

- milestone: m254-exact-source-gated-ppo-smoke-from-m253
- type: driver_candidate
- checkpoint: runs/ppo_m254_exact_source_from_m253_seed5225/checkpoint.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: reject_protected_key_source_regression
- reason: M254 PPO completes and aggregate/M223 exact losses improve but every interpolated alpha regresses protected-key source above +1e-8 so proof gates are skipped

## Next Blocker

Audit the persistent PPO protected-key source regression before any more PPO.
