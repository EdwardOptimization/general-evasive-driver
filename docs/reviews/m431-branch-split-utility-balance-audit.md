# m431-branch-split-utility-balance-audit Research Review

## Summary

- Generated at UTC: 20260523T180836Z
- Type: gate
- Gate tier: proof
- Promotion decision: admit_m432_selective_10004_guard_design
- Decision reason: M431 finds 10004 wrong-history is the dominant branch-split utility conflict while 9872 normal guards are aligned with recovery

## Hypothesis

M430's proof-safe but low-utility outcome is caused by an over-hard branch-split guard; a per-source or per-branch balance can preserve the M430 proof gates while recovering more of M427's projected-recovery utility.

## Lineage

- parent_checkpoint: runs/m427_projected_recovery_ltraj1e13_s40_seed10156/candidate_checkpoint.pt, runs/m430_branch_split_projected_ltraj1e13_s40_seed10157/candidate_checkpoint.pt
- parent_dataset: runs/m429_branch_split_old_key_guard/branch_split_hard_guard_anchor.npz, runs/m398_old_key_normal_margin_recovery_targets/old_key_recovery_corpus.npz
- parent_config: experiments/manifests/m430-branch-split-nullspace-projection-probe.json
- parent_objective: projected recovery gradient with branch-split old-key hard guard
- derived_from: m430-branch-split-nullspace-projection-probe
- blocked_by: m430-branch-split-nullspace-projection-probe
- supersedes: None
- invalidates: None

## Success Criteria

- identify which branch-split rows dominate the recovery-gradient projection conflicts
- explain why M430 recovery retention falls to 0.061702 after M427 reached 0.174354
- define a next no-PPO probe that can test selective softening without actor-contract changes
- do not claim promotion or driver improvement from the audit alone

## Failure Criteria

- cannot attribute the utility loss to specific sources or branches
- next recipe would require lowering proof thresholds
- next recipe would require changing actor inputs or outputs
- audit recommends PPO before proof-safe utility balance is understood

## Evidence Gates

- projection trace conflict attribution
- per-source and per-branch trajectory-anchor loss attribution
- M427 vs M430 utility and proof comparison
- next recipe must preserve exact M297/M270/old-key no-regression and M267/M264 old-key M183/M170 proof gates

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not promote checkpoint
- do not lower exact or replay thresholds
- do not add hidden or oracle actor inputs
- do not make replay labels actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m431-branch-split-utility-balance-audit
- type: gate
- checkpoint: runs/m430_branch_split_projected_ltraj1e13_s40_seed10157/candidate_checkpoint.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m432_selective_10004_guard_design
- reason: M431 finds 10004 wrong-history is the dominant branch-split utility conflict while 9872 normal guards are aligned with recovery

## Next Blocker

m432-selective-10004-guard-design
