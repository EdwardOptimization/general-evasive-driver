# m429-branch-split-old-key-guard-implementation Research Review

## Summary

- Generated at UTC: 20260523T175557Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: admit_m430_branch_split_nullspace_projection_probe
- Decision reason: M429 exports a 357-row branch-split hard guard with 10004 wrong-history 10023 wrong-history and 9872 normal guards and no-update exact smoke passes

## Hypothesis

A branch-split old-key guard can keep projected recovery's M267-retention benefit while preventing 10004 wrong-history safety and 9872 normal-branch collisions.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt, runs/m427_projected_recovery_ltraj1e13_s40_seed10156/candidate_checkpoint.pt
- parent_dataset: runs/m427_projected_old_key_targeted_replay/guard_results.csv, runs/m398_old_key_normal_margin_recovery_targets/old_key_recovery_corpus.npz, runs/m426_source_coupled_hard_guard_anchor/hard_guard_anchor.npz
- parent_config: experiments/manifests/m428-old-key-branch-split-guard-audit.json
- parent_objective: implement branch-split old-key hard guard after M427 projected recovery failure
- derived_from: m428-old-key-branch-split-guard-audit
- blocked_by: m427-source-coupled-nullspace-projection-probe
- supersedes: None
- invalidates: None

## Success Criteria

- export a hard guard anchor with M267 rows 6 and 15 old-key 10023 spillovers 10004 rejected branch and 9872 normal branch
- exclude 10004 normal branch from the hard guard so M398 recovery can still move it
- write source metadata showing branch role for each old-key source
- run no-update exact repair smoke with finite zero replay loss
- run focused tests for branch filtering and source metadata

## Failure Criteria

- 10004 normal branch is accidentally hard-anchored
- 10004 rejected branch is not guarded
- 9872 normal branch cannot be reconstructed
- implementation changes actor inputs or outputs
- milestone runs PPO or promotes a checkpoint

## Evidence Gates

- export branch-split hard guard anchor
- 10004 rejected-history branch guarded while normal recovery remains utility
- 9872 normal-branch guard rows added
- no-update exact repair smoke passes
- focused tests for branch-split export
- no PPO run
- no checkpoint promotion
- no actor input/output change

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

- milestone: m429-branch-split-old-key-guard-implementation
- type: infrastructure
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m430_branch_split_nullspace_projection_probe
- reason: M429 exports a 357-row branch-split hard guard with 10004 wrong-history 10023 wrong-history and 9872 normal guards and no-update exact smoke passes

## Next Blocker

m430-branch-split-nullspace-projection-probe
