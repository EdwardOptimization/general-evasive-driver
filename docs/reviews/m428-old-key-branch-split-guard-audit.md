# m428-old-key-branch-split-guard-audit Research Review

## Summary

- Generated at UTC: 20260523T175121Z
- Type: gate
- Gate tier: process
- Promotion decision: admit_m429_branch_split_old_key_guard_implementation
- Decision reason: M428 attributes M427 old-key failures to 10004 rejected-branch washout 10023 gap erosion and 9872 normal-branch collisions so a branch-split guard is needed

## Hypothesis

M427 failed old-key because the M426 hard-guard set excluded branch-specific constraints on 10004 and omitted 9872 normal-branch guards, not because projected recovery is useless.

## Lineage

- parent_checkpoint: runs/m427_projected_recovery_ltraj1e13_s40_seed10156/candidate_checkpoint.pt
- parent_dataset: runs/m427_projected_old_key_targeted_replay/guard_results.csv, runs/m426_source_coupled_hard_guard_anchor/hard_guard_anchor.npz, runs/m398_old_key_normal_margin_recovery_targets/old_key_recovery_corpus.npz
- parent_config: experiments/manifests/m427-source-coupled-nullspace-projection-probe.json
- parent_objective: audit old-key failures after projected recovery improves utility but fails compact replay
- derived_from: m427-source-coupled-nullspace-projection-probe
- blocked_by: m427-source-coupled-nullspace-projection-probe
- supersedes: None
- invalidates: None

## Success Criteria

- attribute all M427 old-key failed cases to normal-branch or wrong-history-branch mechanisms
- define whether 10004 should split normal recovery from rejected-history guard
- define whether 9872 should be added as a normal-branch hard guard
- pre-register the next implementation or stop the projected recovery path

## Failure Criteria

- audit cannot explain the four old-key failures
- audit recommends another projection without changing the hard guard set
- audit changes actor inputs or output contract
- audit lowers old-key thresholds

## Evidence Gates

- no PPO run
- no checkpoint promotion
- classify M427 old-key failed rows by normal-branch vs wrong-history-branch regression
- decide whether 10004 needs branch-split recovery and rejected-history guarding
- decide whether 9872 requires added normal-branch hard guard

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

- milestone: m428-old-key-branch-split-guard-audit
- type: gate
- checkpoint: runs/m427_projected_recovery_ltraj1e13_s40_seed10156/candidate_checkpoint.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m429_branch_split_old_key_guard_implementation
- reason: M428 attributes M427 old-key failures to 10004 rejected-branch washout 10023 gap erosion and 9872 normal-branch collisions so a branch-split guard is needed

## Next Blocker

m429-branch-split-old-key-guard-implementation
