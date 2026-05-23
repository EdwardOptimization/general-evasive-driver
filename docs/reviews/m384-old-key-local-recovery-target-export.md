# m384-old-key-local-recovery-target-export Research Review

## Summary

- Generated at UTC: 20260523T133411Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: admit_m385_old_key_recovery_residual_repair_probe
- Decision reason: M384 exports 4 replay-selected old-key recovery targets from 1008 local action rollouts and no-update exact repair reports finite recovery loss without PPO or actor input change

## Hypothesis

Replay-selected one-step local action targets can be exported for the old-key gap-tail rows so the M383 recovery residual is aligned with actual terminal-margin recovery instead of the misaligned old-key surrogate.

## Lineage

- parent_checkpoint: runs/m378_v2_gap_tail_final_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m380_alpha01_cumulative_old_key_boundary_audit/gap_tail_rows.csv, runs/m383_old_key_recovery_bootstrap_corpus/old_key_recovery_corpus.npz
- parent_config: experiments/manifests/m383-old-key-local-recovery-residual-implementation.json
- parent_objective: export replay-selected local-action recovery targets for the M383 exact repair residual
- derived_from: m383-old-key-local-recovery-residual-implementation
- blocked_by: m383-old-key-local-recovery-residual-implementation
- supersedes: None
- invalidates: None

## Success Criteria

- export a real old-key recovery corpus with observation hidden action weight and row-id arrays
- record the candidate action grid or sampling rule and the selected terminal-margin improvement per row
- reject rows that do not improve normal-history terminal margin or mark them as base-retention rows
- the exported corpus loads through load_old_key_recovery_snippets
- a no-update exact repair smoke reports finite recovery terms
- research validation passes

## Failure Criteria

- exported targets are just copied preferred actions without replay selection
- target search uses forbidden deployable actor inputs
- loader or no-update smoke fails
- research validation fails

## Evidence Gates

- infrastructure only; no PPO run
- recover target export preserves existing actor input contract
- selected actions must come from replay/local-search margin improvement, not oracle actor inputs
- exported corpus must load through the M383 recovery loader
- no-update exact repair smoke must report finite recovery terms

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not promote a checkpoint
- do not lower old-key thresholds
- do not add hidden or oracle actor inputs
- do not replace direct steer/throttle/brake output
- do not treat bootstrap preferred actions as recovered targets

## Failure Taxonomy

- none

## Scoreboard

- milestone: m384-old-key-local-recovery-target-export
- type: infrastructure
- checkpoint: not_applicable_infrastructure_task
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m385_old_key_recovery_residual_repair_probe
- reason: M384 exports 4 replay-selected old-key recovery targets from 1008 local action rollouts and no-update exact repair reports finite recovery loss without PPO or actor input change

## Next Blocker

m385-old-key-recovery-residual-repair-probe
