# m1082-v4-public-base-proof-hardened-surface-retarget-design Research Review

## Summary

- Generated at UTC: 20260527T123318Z
- Type: gate
- Gate tier: process
- Promotion decision: proof_hardened_surface_retarget_design_admit_m1083_refresh
- Decision reason: M1082 designs a retargeted refresh with expanded source coverage tighter near-boundary success-drop pressure and unchanged robustness thresholds

## Hypothesis

A retargeted refresh with more probe sources, stricter source caps, and boundary relocation offsets can recover a source-diverse all-success-drop surface without weakening robustness thresholds.

## Lineage

- parent_checkpoint: runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt
- parent_dataset: docs/m1081-v4-public-base-proof-hardened-surface-refresh.md, runs/m1081_proof_hardened_boundary_robustness_w005_seed108100/summary.json
- parent_config: experiments/manifests/m1081-v4-public-base-proof-hardened-surface-refresh.json
- parent_objective: design a retargeted current-base surface refresh after M1081 found a duplicate/source-diversity dominated surface
- derived_from: m1081-v4-public-base-proof-hardened-surface-refresh
- blocked_by: M1081 found a surface but primary robustness failed on physical-pair diversity, success-drop fraction, and pair dominance
- supersedes: None
- invalidates: converting the M1081 surface directly into replay/objective corpora, loosening M1081 robustness gates after failure

## Success Criteria

- design artifact exists
- retargeted sampling changes are explicit
- physical-pair diversity mitigation is explicit
- success-drop fraction mitigation is explicit
- no robustness thresholds are weakened
- no training, PPO, mining, promotion, or private holdout occurs

## Failure Criteria

- design artifact is missing
- thresholds are weakened
- physical-pair diversity mitigation is missing
- success-drop mitigation is missing
- training, PPO, or mining starts
- private holdout is used

## Evidence Gates

- M1082 must not train
- M1082 must not run PPO
- M1082 must not mine rows; design only
- M1082 must not promote
- M1082 must not use private holdout
- M1082 must address physical-pair diversity and success-drop fraction explicitly

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not mine rows
- do not promote
- do not use private holdout
- do not lower source-diversity or success-drop thresholds

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1082-v4-public-base-proof-hardened-surface-retarget-design
- type: gate
- checkpoint: docs/m1082-v4-public-base-proof-hardened-surface-retarget-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: proof_hardened_surface_retarget_design_admit_m1083_refresh
- reason: M1082 designs a retargeted refresh with expanded source coverage tighter near-boundary success-drop pressure and unchanged robustness thresholds

## Next Blocker

m1083-v4-public-base-proof-hardened-surface-retarget-refresh
