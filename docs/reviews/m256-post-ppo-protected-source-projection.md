# m256-post-ppo-protected-source-projection Research Review

## Summary

- Generated at UTC: 20260522T151518Z
- Type: driver_candidate
- Gate tier: proof
- Promotion decision: reject_projection_proof_washout
- Decision reason: M256 projection repairs exact source losses but every tested interpolation alpha fails M183/M170 row16 proof retention; trajectory anchor support is needed before retry

## Hypothesis

A no-PPO actor-coupling projection from the M254 raw PPO checkpoint can restore the protected-key source while retaining useful M223 movement, giving a candidate that exact-source gates before public proof evaluation.

## Lineage

- parent_checkpoint: runs/m252_alpha_boundary_interpolation/checkpoints/alpha_0_00008.pt, runs/ppo_m254_exact_source_from_m253_seed5225/checkpoint.pt
- parent_dataset: runs/m231_protected_key_snippet_surface/protected_key_snippets.npz, runs/m232_combined_m223_m231_snippet_anchor/outcome_intervention_snippets.npz, runs/m254_source_aware_exact_m232_eval/source_summary.csv
- parent_config: docs/m255-m254-protected-source-regression-audit.md
- parent_objective: post-PPO protected-key source projection with M253 action anchor
- derived_from: m255-m254-protected-source-regression-audit
- blocked_by: m255-m254-protected-source-regression-audit
- supersedes: None
- invalidates: None

## Success Criteria

- projection reduces protected-key source loss versus M254 raw
- at least one projected/interpolated alpha has M223 source delta < 0, aggregate M232 delta <= +1e-8, and protected-key source delta <= +1e-8 versus M253
- proof gates are only run for exact-gated candidates
- no PPO is run

## Failure Criteria

- projection cannot restore protected-key source without losing M223 improvement
- all projected/interpolated candidates fail exact source gate
- candidate exact-gates but fails public proof retention
- actor input contract changes

## Evidence Gates

- protected-key source projection from M254 raw PPO
- M245 exact source-aware objective gate
- post-projection interpolation if exact source/proof margins require it
- public proof gates only after exact source gate passes
- research validator

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run new PPO in M256
- do not promote projection without exact source gate
- do not run proof gates if exact source gate fails
- do not change actor inputs

## Failure Taxonomy

- proof_washout
- promotion_gate_failure

## Scoreboard

- milestone: m256-post-ppo-protected-source-projection
- type: driver_candidate
- checkpoint: runs/m256_post_ppo_protected_source_projection_seed10067/optimized_checkpoint.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: reject_projection_proof_washout
- reason: M256 projection repairs exact source losses but every tested interpolation alpha fails M183/M170 row16 proof retention; trajectory anchor support is needed before retry

## Next Blocker

Implement or design row16/trajectory-anchor support for post-PPO projection before retrying projection.
