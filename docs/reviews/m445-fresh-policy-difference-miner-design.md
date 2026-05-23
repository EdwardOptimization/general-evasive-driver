# m445-fresh-policy-difference-miner-design Research Review

## Summary

- Generated at UTC: 20260523T192121Z
- Type: infrastructure
- Gate tier: generalization
- Promotion decision: admit_m446_policy_difference_miner_implementation
- Decision reason: M445 designs a source-diverse policy-difference miner with outcome margin and return divergence types after M444 aggregate tie

## Hypothesis

After M444 found no aggregate broad success differences, the next useful evidence is a fresh source-diverse policy-difference miner that finds scenarios where candidates actually diverge in closed-loop behavior.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt, runs/m427_projected_recovery_ltraj1e13_s40_seed10156/candidate_checkpoint.pt, runs/m438_r0015_active_boundary_lactive1e12_s40_seed10161/candidate_checkpoint.pt, runs/m442_tail_r0010_active_boundary_v2_l1e12_s40_seed10162/candidate_checkpoint.pt
- parent_dataset: runs/m444_proof_utility_generalization_seed9600/episodes.csv, runs/m444_proof_utility_generalization_seed9600/policy_summary.csv, runs/m444_proof_utility_generalization_seed9600/obstacle_label_summary.csv
- parent_config: experiments/manifests/m444-proof-utility-generalization-audit.json
- parent_objective: fresh policy-difference mining design
- derived_from: m444-proof-utility-generalization-audit
- blocked_by: m444-proof-utility-generalization-audit
- supersedes: None
- invalidates: None

## Success Criteria

- design specifies policy set and fresh seed pool
- design specifies accepted divergence types
- design specifies source-diversity and bucket limits
- design specifies output artifacts for M446 implementation
- design preserves the human-view actor contract

## Failure Criteria

- design falls back to active-boundary scalar tuning
- design uses hidden/oracle actor inputs
- design promotes a checkpoint from M444
- design does not define diversity targets

## Evidence Gates

- define source-diverse policy-difference mining schema
- define outcome and margin divergence thresholds
- define fresh scenario pool and diversity targets
- no checkpoint promotion

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not tune from M444 and call it private holdout
- do not add hidden or oracle actor inputs
- do not make policy labels or proof labels actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m445-fresh-policy-difference-miner-design
- type: infrastructure
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m446_policy_difference_miner_implementation
- reason: M445 designs a source-diverse policy-difference miner with outcome margin and return divergence types after M444 aggregate tie

## Next Blocker

m446-policy-difference-miner-implementation
