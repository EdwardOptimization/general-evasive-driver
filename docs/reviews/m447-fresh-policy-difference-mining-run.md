# m447-fresh-policy-difference-mining-run Research Review

## Summary

- Generated at UTC: 20260523T193048Z
- Type: gate
- Gate tier: generalization
- Promotion decision: candidate_family_indistinguishable_admit_challenge_distribution_design
- Decision reason: M447 finds only three return-delta rows across 2048 comparisons and no outcome or margin divergences so M121 is too insensitive

## Hypothesis

A larger fresh pool can reveal whether recent candidates have meaningful closed-loop policy differences that the 160-episode M444 aggregate benchmark missed.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt, runs/m434_selective_10004_projection_r0010/candidate_checkpoint.pt, runs/m438_r0015_active_boundary_lactive1e12_s40_seed10161/candidate_checkpoint.pt, runs/m427_projected_recovery_ltraj1e13_s40_seed10156/candidate_checkpoint.pt, runs/m442_tail_r0010_active_boundary_v2_l1e12_s40_seed10162/candidate_checkpoint.pt
- parent_dataset: configs/m121_human_view_zero_obstacle_relvel.json
- parent_config: experiments/manifests/m446-policy-difference-miner-implementation.json
- parent_objective: fresh policy-difference mining run
- derived_from: m446-policy-difference-miner-implementation
- blocked_by: m446-policy-difference-miner-implementation
- supersedes: None
- invalidates: None

## Success Criteria

- fresh benchmark completes
- policy-difference miner completes
- summary states whether accepted rows include outcome or margin divergences
- no checkpoint is promoted

## Failure Criteria

- benchmark or miner fails
- result is used for promotion
- result drives tuning without a new manifest
- actor contract changes

## Evidence Gates

- 512-episode fresh benchmark seed 9700
- policy-difference miner run
- compact policy-difference corpus written
- no checkpoint promotion

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not tune from this public diagnostic and call it private holdout
- do not change actor input/output contract
- do not lower proof gates

## Failure Taxonomy

- none

## Scoreboard

- milestone: m447-fresh-policy-difference-mining-run
- type: gate
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: 0.876953
- termination_rate: 0.123047
- clearance_margin_mean: 1.831957
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: candidate_family_indistinguishable_admit_challenge_distribution_design
- reason: M447 finds only three return-delta rows across 2048 comparisons and no outcome or margin divergences so M121 is too insensitive

## Next Blocker

m448-differentiating-challenge-distribution-design
