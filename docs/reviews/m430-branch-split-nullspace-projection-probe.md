# m430-branch-split-nullspace-projection-probe Research Review

## Summary

- Generated at UTC: 20260523T180230Z
- Type: gate
- Gate tier: proof
- Promotion decision: reject_m430_candidate_admit_m431_branch_split_utility_balance_audit
- Decision reason: M430 restores exact M267 old-key and M183 proof gates but is retention-heavy with only 6.2 percent recovery utility retained versus M406

## Hypothesis

Branch-split old-key hard guards can keep M427 projected recovery's utility improvement while repairing 10004 wrong-history safety and 9872 normal-branch collision.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt, runs/m403_lrec1e10_interpolation/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m398_old_key_normal_margin_recovery_targets/old_key_recovery_corpus.npz, runs/m429_branch_split_old_key_guard/branch_split_hard_guard_anchor.npz
- parent_config: experiments/manifests/m429-branch-split-old-key-guard-implementation.json
- parent_objective: no-PPO projected recovery with branch-split old-key hard guard
- derived_from: m429-branch-split-old-key-guard-implementation
- blocked_by: m427-source-coupled-nullspace-projection-probe
- supersedes: None
- invalidates: None

## Success Criteria

- candidate passes exact M297/M270/old-key no-regression
- candidate passes M267/M264 first replay with 17/17 success drops
- candidate passes old-key compact replay with 40/40 accepted
- candidate passes M183/M170 first replay with 17/17 success drops
- candidate retains at least 20% of M406 recovery improvement for primary pass

## Failure Criteria

- exact gates regress
- M267/M264 rows 6 or 15 become wrong-history successes
- old-key compact replay remains below 40/40
- candidate falls below M427 recovery utility
- actor input or output contract changes

## Evidence Gates

- exact M297 no-regression
- exact M270 no-regression
- old-key surrogate no-regression
- M267/M264 first replay
- old-key compact replay
- M183/M170 first replay if first gates pass
- recovery improvement retained vs M406 >= 0.20 for primary pass

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not promote checkpoint
- do not lower exact or replay thresholds
- do not add hidden or oracle actor inputs
- do not make replay labels actor inputs

## Failure Taxonomy

- objective_overfit
- promotion_gate_failure

## Scoreboard

- milestone: m430-branch-split-nullspace-projection-probe
- type: gate
- checkpoint: runs/m430_branch_split_projected_ltraj1e13_s40_seed10157/candidate_checkpoint.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: reject_m430_candidate_admit_m431_branch_split_utility_balance_audit
- reason: M430 restores exact M267 old-key and M183 proof gates but is retention-heavy with only 6.2 percent recovery utility retained versus M406

## Next Blocker

m431-branch-split-utility-balance-audit
