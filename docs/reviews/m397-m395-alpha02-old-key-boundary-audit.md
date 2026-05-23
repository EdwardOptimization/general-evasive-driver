# m397-m395-alpha02-old-key-boundary-audit Research Review

## Summary

- Generated at UTC: 20260523T150904Z
- Type: gate
- Gate tier: process
- Promotion decision: admit_m398_old_key_normal_margin_recovery_target_export
- Decision reason: M397 classifies alpha 0.2 old-key failure as normal-branch terminal-margin cliff not wrong-history sensitivity loss; alpha 0.4 broadens to two accepted regressions

## Hypothesis

The first post-M395 boundary is a cumulative old-key normal-branch terminal-margin cliff on case 9958, not a broad loss of wrong-history sensitivity.

## Lineage

- parent_checkpoint: runs/m394_s02_micro_interpolation/checkpoints/alpha_0_1.pt
- parent_dataset: docs/m396-m395-micro-promotion-utility-audit.md, runs/m396_s02a020_old_key_replay_gate/old_key_replay_comparison_rows.csv, runs/m396_s02a020_old_key_replay_gate/summary.json
- parent_config: experiments/manifests/m396-m395-micro-promotion-utility-audit.json
- parent_objective: audit alpha 0.2 cumulative old-key normal-branch boundary after M395
- derived_from: m396-m395-micro-promotion-utility-audit
- blocked_by: m396-m395-micro-promotion-utility-audit
- supersedes: None
- invalidates: None

## Success Criteria

- quantify alpha 0.1 versus alpha 0.2 active-row margins and actions
- determine whether the failure is singleton stale row or representative old-key surface behavior
- decide the next no-PPO infrastructure or repair milestone
- record all evidence in docs and manifests

## Failure Criteria

- audit cannot reproduce or locate the active old-key row
- audit changes actor inputs or thresholds
- research validation fails

## Evidence Gates

- no PPO run
- audit active old-key case 9958|perturbed|39|36
- classify normal-branch cliff versus wrong-history sensitivity loss
- decide whether next task is local recovery target export, objective redesign, or broader surface refresh

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not promote checkpoint
- do not lower old-key thresholds
- do not add hidden or oracle actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m397-m395-alpha02-old-key-boundary-audit
- type: gate
- checkpoint: runs/m394_s02_micro_interpolation/checkpoints/alpha_0_1.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m398_old_key_normal_margin_recovery_target_export
- reason: M397 classifies alpha 0.2 old-key failure as normal-branch terminal-margin cliff not wrong-history sensitivity loss; alpha 0.4 broadens to two accepted regressions

## Next Blocker

m398-old-key-normal-margin-recovery-target-export
