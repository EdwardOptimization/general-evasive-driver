# m1080-v4-public-base-proof-hardened-surface-refresh-design Research Review

## Summary

- Generated at UTC: 20260527T112857Z
- Type: gate
- Gate tier: process
- Promotion decision: proof_hardened_surface_refresh_design_admit_m1081_refresh
- Decision reason: M1080 designs a current-base source-diverse protected/preference refresh with primary 0.005 margin-bucket robustness before new medium PPO

## Hypothesis

The promoted M1078 public-gate base needs a fresh source-diverse protected/preference surface before any new medium PPO proposal.

## Lineage

- parent_checkpoint: runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt
- parent_dataset: docs/m1079-v4-public-base-contract-clean-post-promotion-synthesis.md, docs/m1078-v4-public-base-contract-clean-projection-promotion-audit.md
- parent_config: experiments/manifests/m1079-v4-public-base-contract-clean-post-promotion-synthesis.json
- parent_objective: design a current-base source-diverse protected/preference surface refresh before any new medium PPO proposal
- derived_from: m1079-v4-public-base-contract-clean-post-promotion-synthesis
- blocked_by: M1079 opened proof_hardened_base_surface_refresh and blocked direct medium PPO until refresh design
- supersedes: None
- invalidates: running medium PPO directly from the M1078 public-gate base, reusing only M1072/M1073 active rows as if they were fresh current-base evidence

## Success Criteria

- design artifact exists
- current base checkpoint is explicit
- mining axes are explicit
- source-diversity thresholds are explicit
- objective/replay conversion plan is explicit
- no training, PPO, mining, promotion, or private holdout occurs

## Failure Criteria

- design artifact is missing
- current base checkpoint is ambiguous
- source-diversity thresholds are missing
- training, PPO, or mining starts
- private holdout is used

## Evidence Gates

- M1080 must not train
- M1080 must not run PPO
- M1080 must not use private holdout
- M1080 must not mine rows; design only
- M1080 must define acceptance criteria for a current-base source-diverse refresh

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not mine rows
- do not promote
- do not use private holdout
- do not weaken actor-input or changed-parameter contracts

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1080-v4-public-base-proof-hardened-surface-refresh-design
- type: gate
- checkpoint: docs/m1080-v4-public-base-proof-hardened-surface-refresh-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: proof_hardened_surface_refresh_design_admit_m1081_refresh
- reason: M1080 designs a current-base source-diverse protected/preference refresh with primary 0.005 margin-bucket robustness before new medium PPO

## Next Blocker

m1081-v4-public-base-proof-hardened-surface-refresh
