# m907-v4-pair-delta-public-base-feature-dim-compatibility-audit Research Review

## Summary

- Generated at UTC: 20260525T205742Z
- Type: gate
- Gate tier: process
- Promotion decision: public_base_feature_dim_compatibility_route_to_128dim_residual_design
- Decision reason: M907 confirms M399 and M568 share P0 human-view inputs but differ in actor feature width 128 vs 64 and routes to public-base-compatible residual-head design

## Hypothesis

The M906 failure is a feature-dimension compatibility blocker between M399 public base and the M761 residual head, not a forbidden-input actor contract violation.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt, runs/m568_scaled_l3_bc_seed5660/checkpoint.pt, runs/m761_v4_sequence_objective_probe/residual_head.pt
- parent_dataset: docs/m906-v4-pair-delta-public-base-exact-compatibility-audit.md, runs/m906_public_base_exact_compatibility/summary.json
- parent_config: experiments/manifests/m906-v4-pair-delta-public-base-exact-compatibility-audit.json
- parent_objective: audit residual-head and public-base actor feature dimension mismatch before any compatibility fix
- derived_from: m906-v4-pair-delta-public-base-exact-compatibility-audit
- blocked_by: M906 failed because M761 residual feature_dim 64 does not match M399 actor feature_dim 128
- supersedes: None
- invalidates: None

## Success Criteria

- M907 records the exact mismatch
- M907 separates compatibility from actor input contract
- M907 chooses a next route
- M907 keeps training, replay, PPO, and promotion blocked

## Failure Criteria

- M907 trains or modifies a model
- M907 runs replay or PPO
- M907 promotes a checkpoint
- M907 treats the mismatch as solved
- M907 omits next-route decision

## Evidence Gates

- M907 must audit the feature-dimension mismatch
- M907 must distinguish architecture mismatch from actor input contract violation
- M907 must choose a compatibility route
- M907 must keep training, replay, PPO, and promotion blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train a residual head in M907
- do not modify actor inputs
- do not run replay
- do not run PPO
- do not promote a checkpoint
- do not ignore the feature_dim mismatch

## Failure Taxonomy

- lineage_invalid
- contract_violation
- metric_artifact
- objective_overfit

## Scoreboard

- milestone: m907-v4-pair-delta-public-base-feature-dim-compatibility-audit
- type: gate
- checkpoint: docs/m907-v4-pair-delta-public-base-feature-dim-compatibility-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: public_base_feature_dim_compatibility_route_to_128dim_residual_design
- reason: M907 confirms M399 and M568 share P0 human-view inputs but differ in actor feature width 128 vs 64 and routes to public-base-compatible residual-head design

## Next Blocker

Public-base residual-head feature-dimension mismatch has not yet been audited for route selection
