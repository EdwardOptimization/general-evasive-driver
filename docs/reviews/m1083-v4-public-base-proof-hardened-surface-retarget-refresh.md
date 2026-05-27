# m1083-v4-public-base-proof-hardened-surface-retarget-refresh Research Review

## Summary

- Generated at UTC: 20260527T135733Z
- Type: gate
- Gate tier: proof
- Promotion decision: proof_hardened_surface_retarget_duplicate_dominated_route_to_synthesis
- Decision reason: M1083 fixes success-drop fraction to 1.0 and finds 626 accepted wrong-history rows but rejects conversion because physical-pair diversity and dominance still fail

## Hypothesis

M1082 retargeting will recover a source-diverse all-success-drop wrong-history boundary surface for the M1078 public-gate base.

## Lineage

- parent_checkpoint: runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt
- parent_dataset: docs/m1082-v4-public-base-proof-hardened-surface-retarget-design.md, runs/m1081_proof_hardened_boundary_robustness_w005_seed108100/summary.json
- parent_config: experiments/manifests/m1082-v4-public-base-proof-hardened-surface-retarget-design.json
- parent_objective: run a retargeted source-diverse current-base surface refresh without weakening robustness thresholds
- derived_from: m1082-v4-public-base-proof-hardened-surface-retarget-design
- blocked_by: M1081 primary robustness failed on physical-pair diversity, success-drop fraction, and pair dominance
- supersedes: None
- invalidates: direct conversion of the M1081 surface, threshold loosening instead of retargeting

## Success Criteria

- matched-current summary exists
- outcome summary exists
- boundary relocation summary exists
- 0.005 robustness summary exists and passes
- accepted wrong-history rows >= 80
- physical pairs >= 10
- left steps >= 5
- checkpoints >= 3
- targets >= 2
- margin buckets >= 2 at width 0.005
- success_drop_fraction == 1.0
- no training or PPO occurs

## Failure Criteria

- surface is sparse
- surface is duplicate-dominated
- success_drop_fraction < 1.0
- actor inputs change
- training or PPO starts
- private holdout is used

## Evidence Gates

- M1083 must not train or run PPO
- M1083 must preserve actor inputs
- M1083 must use the M1082 retargeted sampling and boundary settings
- M1083 must keep primary 0.005 robustness thresholds unchanged
- M1083 must not promote a checkpoint

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not train
- do not promote
- do not use private holdout
- do not change actor inputs
- do not lower success-drop or source-diversity thresholds after seeing failure

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m1083-v4-public-base-proof-hardened-surface-retarget-refresh
- type: gate
- checkpoint: runs/m1083_proof_hardened_retarget_boundary_robustness_w005_seed108200/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: proof_hardened_surface_retarget_duplicate_dominated_route_to_synthesis
- reason: M1083 fixes success-drop fraction to 1.0 and finds 626 accepted wrong-history rows but rejects conversion because physical-pair diversity and dominance still fail

## Next Blocker

m1084-v4-public-base-proof-hardened-surface-refresh-synthesis
