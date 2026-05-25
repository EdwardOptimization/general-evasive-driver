# m908-v4-public-base-compatible-residual-head-probe-design Research Review

## Summary

- Generated at UTC: 20260525T210101Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: public_base_128dim_residual_head_probe_design_admit_m909
- Decision reason: M908 designs M399-frozen residual-head-only probe expecting feature_dim 128 and residual_parameter_count 8451 before any exact pair-delta execution replay PPO or promotion

## Hypothesis

A design-only milestone can specify a safe public-base-compatible residual-head objective probe rooted at M399 without using the M761 64-dim residual head or changing actor inputs.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt, runs/m568_scaled_l3_bc_seed5660/checkpoint.pt, runs/m761_v4_sequence_objective_probe/residual_head.pt
- parent_dataset: docs/m907-v4-pair-delta-public-base-feature-dim-compatibility-audit.md, docs/m906-v4-pair-delta-public-base-exact-compatibility-audit.md, runs/m880_v4_pair_delta_objective_target_enrichment/enriched_objective_train_public_rows.csv, runs/m880_v4_pair_delta_objective_target_enrichment/enriched_objective_eval_public_rows.csv, runs/m880_v4_pair_delta_objective_target_enrichment/enriched_source_holdout_public_rows.csv, runs/m880_v4_pair_delta_objective_target_enrichment/enriched_new_signature_holdout_public_rows.csv
- parent_config: experiments/manifests/m907-v4-pair-delta-public-base-feature-dim-compatibility-audit.json, experiments/manifests/m906-v4-pair-delta-public-base-exact-compatibility-audit.json
- parent_objective: design a public-base-compatible 128-dim residual-head objective probe after M906 feature-dim mismatch
- derived_from: m907-v4-pair-delta-public-base-feature-dim-compatibility-audit
- blocked_by: M399 public-base actor feature_dim 128 cannot use M761 residual head feature_dim 64
- supersedes: None
- invalidates: None

## Success Criteria

- M908 specifies a 128-dim residual head route for M399
- M908 specifies exact split metrics and holdout non-regression gates
- M908 keeps M568/M761 evidence diagnostic-only
- M908 blocks replay, PPO, and promotion

## Failure Criteria

- M908 force-loads M761 residual head into M399
- M908 modifies actor inputs
- M908 admits replay or PPO before exact objective evidence
- M908 omits target-lineage or holdout safeguards

## Evidence Gates

- M908 must keep M399 as the public-base actor
- M908 must design a residual head with feature_dim=128
- M908 must keep M568/M761 as diagnostic lineage only
- M908 must require exact split metrics before replay
- M908 must block actor update, replay execution, PPO, and promotion

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train in M908
- do not force-load M761 residual head into M399
- do not pad, truncate, or project residual features without a registered objective
- do not modify actor inputs
- do not run replay
- do not run PPO
- do not promote a checkpoint

## Failure Taxonomy

- none

## Scoreboard

- milestone: m908-v4-public-base-compatible-residual-head-probe-design
- type: infrastructure
- checkpoint: docs/m908-v4-public-base-compatible-residual-head-probe-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: public_base_128dim_residual_head_probe_design_admit_m909
- reason: M908 designs M399-frozen residual-head-only probe expecting feature_dim 128 and residual_parameter_count 8451 before any exact pair-delta execution replay PPO or promotion

## Next Blocker

Public-base-compatible 128-dim residual-head probe has not yet been designed
