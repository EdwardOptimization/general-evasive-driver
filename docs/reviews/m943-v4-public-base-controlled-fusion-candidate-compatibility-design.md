# m943-v4-public-base-controlled-fusion-candidate-compatibility-design Research Review

## Summary

- Generated at UTC: 20260525T233251Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: controlled_fusion_candidate_compatibility_design_admit_m944
- Decision reason: M943 designs candidate checkpoint materialization and exact no-update compatibility for M942 alphas 0.0675 0.0700 and 0.0725 before any replay PPO or promotion

## Hypothesis

The M942 objective-level candidate can be checked safely by first materializing interpolated checkpoints and reproducing exact no-update objective metrics before any replay or PPO.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt, runs/m940_v4_public_base_controlled_fusion_boundary_objective/checkpoints/raw_boundary_objective_update.pt
- parent_dataset: docs/m942-v4-public-base-controlled-fusion-micro-boundary-audit.md, runs/m942_v4_public_base_controlled_fusion_micro_boundary_audit/summary.json, runs/m942_v4_public_base_controlled_fusion_micro_boundary_audit/alpha_metrics.csv
- parent_config: experiments/manifests/m942-v4-public-base-controlled-fusion-micro-boundary-audit.json
- parent_objective: design exact no-update compatibility for M942 candidate controlled-fusion alphas
- derived_from: m942-v4-public-base-controlled-fusion-micro-boundary-audit
- blocked_by: candidate alphas must be materialized and exact-checked before replay or PPO
- supersedes: None
- invalidates: None

## Success Criteria

- M943 defines primary and backup candidate alphas
- M943 defines checkpoint materialization artifacts
- M943 defines exact no-update compatibility metrics
- M943 blocks replay PPO and promotion
- M943 preserves the P0 actor contract

## Failure Criteria

- M943 omits exact compatibility before replay
- M943 admits replay PPO or promotion
- M943 changes actor inputs
- M943 unfreezes forbidden model components

## Evidence Gates

- M943 must design candidate checkpoint materialization for alphas 0.0675 0.0700 0.0725
- M943 must keep exact compatibility before replay
- M943 must keep training replay PPO and promotion blocked
- M943 must preserve the P0 actor input contract

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train in M943
- do not run replay
- do not run PPO
- do not promote a checkpoint
- do not change actor inputs
- do not unfreeze response_encoder context_encoder or online_gru_cell

## Failure Taxonomy

- none

## Scoreboard

- milestone: m943-v4-public-base-controlled-fusion-candidate-compatibility-design
- type: infrastructure
- checkpoint: docs/m943-v4-public-base-controlled-fusion-candidate-compatibility-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: controlled_fusion_candidate_compatibility_design_admit_m944
- reason: M943 designs candidate checkpoint materialization and exact no-update compatibility for M942 alphas 0.0675 0.0700 and 0.0725 before any replay PPO or promotion

## Next Blocker

m944-v4-public-base-controlled-fusion-candidate-compatibility-implementation
