# m382-terminal-margin-recovery-residual-design Research Review

## Summary

- Generated at UTC: 20260523T131508Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: admit_m383_old_key_local_recovery_residual_implementation
- Decision reason: M382 chooses a training-only local-action recovery residual and rejects another branch-weight-only overlay after M381 surrogate/replay misalignment

## Hypothesis

A terminal-margin or local-action recovery residual can align exact repair with closed-loop old-key lower-tail safety better than stronger branch-weight preference overlays.

## Lineage

- parent_checkpoint: runs/m378_v2_gap_tail_final_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m381_old_key_surrogate_replay_alignment_audit/summary.json, runs/m380_alpha01_cumulative_old_key_boundary_audit/gap_tail_rows.csv
- parent_config: experiments/manifests/m381-old-key-surrogate-replay-alignment-audit.json
- parent_objective: design a terminal-margin or local-action recovery residual after M381 shows old-key surrogate and replay tails are misaligned
- derived_from: m381-old-key-surrogate-replay-alignment-audit
- blocked_by: m381-old-key-surrogate-replay-alignment-audit
- supersedes: None
- invalidates: None

## Success Criteria

- design specifies target rows, target actions or margins, exact loss terms, and gate order
- design explains how it avoids using oracle inputs in the deployable actor
- next implementation milestone is registered
- research validation passes

## Failure Criteria

- design reuses only stronger old-key branch weighting despite M381 misalignment
- design changes actor inputs
- design lowers replay thresholds
- research validation fails

## Evidence Gates

- design only; no PPO run
- preserve current M379 public-gate base
- do not lower old-key thresholds
- define how tail-row terminal margin or local-action recovery targets enter exact repair
- preserve actor input contract

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not promote a checkpoint
- do not lower old-key thresholds
- do not add hidden or oracle actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m382-terminal-margin-recovery-residual-design
- type: infrastructure
- checkpoint: runs/m378_v2_gap_tail_final_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m383_old_key_local_recovery_residual_implementation
- reason: M382 chooses a training-only local-action recovery residual and rejects another branch-weight-only overlay after M381 surrogate/replay misalignment

## Next Blocker

m383-old-key-local-recovery-residual-implementation
