# m383-old-key-local-recovery-residual-implementation Research Review

## Summary

- Generated at UTC: 20260523T132533Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: admit_m384_old_key_local_recovery_target_export
- Decision reason: M383 implements optional old-key recovery corpus loader exact repair loss CLI and tests; no-update smoke reports finite recovery terms with no PPO promotion or actor input change

## Hypothesis

A training-only old-key local-action recovery residual can be added to exact repair without changing deployed actor inputs or outputs, creating an objective path aligned with replay-tail recovery.

## Lineage

- parent_checkpoint: runs/m378_v2_gap_tail_final_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m380_alpha01_cumulative_old_key_boundary_audit/gap_tail_rows.csv, docs/m382-terminal-margin-recovery-residual-design.md
- parent_config: experiments/manifests/m382-terminal-margin-recovery-residual-design.json
- parent_objective: implement the training-only old-key local-action recovery residual described by M382
- derived_from: m382-terminal-margin-recovery-residual-design
- blocked_by: m382-terminal-margin-recovery-residual-design
- supersedes: None
- invalidates: None

## Success Criteria

- new recovery corpus loader validates observation hidden action dimensions
- exact repair exposes optional old-key recovery loss and logs it
- focused tests cover no-corpus and recovery-corpus paths
- no-update smoke reads a recovery corpus and reports finite recovery terms
- research validation passes

## Failure Criteria

- implementation changes actor input or output contract
- implementation treats recovery residual as a promotion gate without replay
- tests or research validation fail

## Evidence Gates

- implementation only; no PPO run
- export or load old-key recovery corpus
- exact repair can include optional recovery residual
- no-update smoke verifies finite recovery loss
- preserve actor input contract

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not promote a checkpoint
- do not lower old-key thresholds
- do not add hidden or oracle actor inputs
- do not replace direct steer/throttle/brake output

## Failure Taxonomy

- none

## Scoreboard

- milestone: m383-old-key-local-recovery-residual-implementation
- type: infrastructure
- checkpoint: not_applicable_infrastructure_task
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m384_old_key_local_recovery_target_export
- reason: M383 implements optional old-key recovery corpus loader exact repair loss CLI and tests; no-update smoke reports finite recovery terms with no PPO promotion or actor input change

## Next Blocker

m384-old-key-local-recovery-target-export
