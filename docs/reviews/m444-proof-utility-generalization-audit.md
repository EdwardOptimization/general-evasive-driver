# m444-proof-utility-generalization-audit Research Review

## Summary

- Generated at UTC: 20260523T191909Z
- Type: gate
- Gate tier: generalization
- Promotion decision: complete_no_broad_policy_difference_admit_miner
- Decision reason: M444 broad benchmark finds all checkpoint candidates tie M399 success with zero per-seed success differences so fresh policy-difference mining is needed

## Hypothesis

A fresh broad benchmark can tell whether proof-rejected high-recovery candidates have real scenario-distribution value or whether the old-key recovery target is a narrow surrogate.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt, runs/m434_selective_10004_projection_r0010/candidate_checkpoint.pt, runs/m438_r0015_active_boundary_lactive1e12_s40_seed10161/candidate_checkpoint.pt, runs/m427_projected_recovery_ltraj1e13_s40_seed10156/candidate_checkpoint.pt, runs/m442_tail_r0010_active_boundary_v2_l1e12_s40_seed10162/candidate_checkpoint.pt
- parent_dataset: configs/m121_human_view_zero_obstacle_relvel.json, runs/m341_old_key_neighborhood_mining/old_key_neighborhood_compact_corpus.csv
- parent_config: experiments/manifests/m443-active-boundary-v2-stop-audit.json
- parent_objective: non-promotion broad benchmark for proof/utility alignment
- derived_from: m443-active-boundary-v2-stop-audit
- blocked_by: m443-active-boundary-v2-stop-audit
- supersedes: None
- invalidates: None

## Success Criteria

- benchmark completes for base proof-safe and proof-rejected candidates
- policy summary and bucket summaries are saved
- audit states whether broad performance aligns with recovery retained
- no checkpoint is promoted

## Failure Criteria

- benchmark does not complete
- results are used to promote a checkpoint
- results are used to justify more active-boundary scalar tuning without a new manifest
- actor contract changes

## Evidence Gates

- fresh randomized benchmark seed 9600
- policy summary comparison
- mu bucket summary
- vehicle road bucket summary
- no checkpoint promotion

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not promote checkpoint from this audit
- do not report this public diagnostic benchmark as unbiased paper holdout evidence after tuning
- do not tune active-boundary weights from this result and call the same benchmark holdout
- do not lower proof gates
- do not add hidden or oracle actor inputs
- do not use proof labels as actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m444-proof-utility-generalization-audit
- type: gate
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: 0.8625
- termination_rate: 0.1375
- clearance_margin_mean: 1.771655
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: complete_no_broad_policy_difference_admit_miner
- reason: M444 broad benchmark finds all checkpoint candidates tie M399 success with zero per-seed success differences so fresh policy-difference mining is needed

## Next Blocker

m445-fresh-policy-difference-miner-design
