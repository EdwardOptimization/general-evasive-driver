# m398-old-key-normal-margin-recovery-target-export Research Review

## Summary

- Generated at UTC: 20260523T151341Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: admit_m399_old_key_normal_margin_recovery_repair_probe
- Decision reason: M398 exports 2/2 accepted old-key normal-margin recovery targets with mean margin improvement 0.001788 and no-update exact-repair loading passes

## Hypothesis

The post-M395 old-key boundary can be better handled by exporting local normal-branch recovery targets for the current normal-margin cliff rows before another no-PPO repair probe.

## Lineage

- parent_checkpoint: runs/m394_s02_micro_interpolation/checkpoints/alpha_0_1.pt
- parent_dataset: docs/m397-m395-alpha02-old-key-boundary-audit.md, runs/m396_s02a020_old_key_replay_gate/old_key_replay_comparison_rows.csv, runs/m397_s02a040_old_key_replay_gate/old_key_replay_comparison_rows.csv
- parent_config: experiments/manifests/m397-m395-alpha02-old-key-boundary-audit.json
- parent_objective: export local normal-branch recovery targets for current old-key terminal-margin cliffs
- derived_from: m397-m395-alpha02-old-key-boundary-audit
- blocked_by: m397-m395-alpha02-old-key-boundary-audit
- supersedes: None
- invalidates: None

## Success Criteria

- build a source row file for active old-key normal-branch cliff rows
- search local first-action overrides that improve normal margin without leaving the action trust region
- export a finite old-key recovery corpus readable by exact_post_ppo_repair
- record target margins, action distances, and skipped rows

## Failure Criteria

- no local recovery target can be found for case 9958
- exported corpus violates shape finite value or action bounds
- actor contract changes
- research validation fails

## Evidence Gates

- no PPO run
- export local normal-branch recovery targets for old-key case 9958 and any current-family sibling rows when available
- verify no-update exact repair can load the refreshed recovery corpus
- preserve actor input/output contract

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

- milestone: m398-old-key-normal-margin-recovery-target-export
- type: infrastructure
- checkpoint: runs/m394_s02_micro_interpolation/checkpoints/alpha_0_1.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m399_old_key_normal_margin_recovery_repair_probe
- reason: M398 exports 2/2 accepted old-key normal-margin recovery targets with mean margin improvement 0.001788 and no-update exact-repair loading passes

## Next Blocker

m399-old-key-normal-margin-recovery-repair-probe
