# m387-m386-micro-promotion-utility-audit Research Review

## Summary

- Generated at UTC: 20260523T135739Z
- Type: gate
- Gate tier: process
- Promotion decision: admit_m388_m267_row15_conflict_residual_design
- Decision reason: M387 classifies M386 as proof-safe micro retention not meaningful driver improvement; M267/M264 row15 flips at alpha 0.001 so next design must handle cross-surface conflict

## Hypothesis

M386 may be a proof-safe but utility-small micro promotion; before chaining repair or PPO, audit whether alpha 0.00075 materially improves the active objectives or only records retention progress.

## Lineage

- parent_checkpoint: runs/m385_recovery_repair_micro_interpolation/checkpoints/alpha_0_00075.pt, runs/m378_v2_gap_tail_final_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m386-full-public-gate-for-m385-a00075.md, runs/m386_full_public_gate_for_m385_a00075/summary.json
- parent_config: experiments/manifests/m386-full-public-gate-for-m385-a00075.json
- parent_objective: audit whether the M386 micro promotion is useful enough to chain more repair or PPO
- derived_from: m386-full-public-gate-for-m385-a00075
- blocked_by: m386-full-public-gate-for-m385-a00075
- supersedes: None
- invalidates: None

## Success Criteria

- classify M386 utility based on exact deltas, replay slack, first failing alpha, and behavior deltas
- identify the next blocker without running training
- document whether to chain from M386 or redesign the repair objective
- research validation passes

## Failure Criteria

- audit omits the M267/M264 row15 boundary
- audit recommends PPO based only on promotion status
- actor contract changes
- research validation fails

## Evidence Gates

- no PPO run
- audit step size and proof-boundary slack
- decide whether to chain from M386 or redesign the objective
- preserve actor contract

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not promote another checkpoint
- do not lower M267/M264 success-drop requirement
- do not change actor inputs or outputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m387-m386-micro-promotion-utility-audit
- type: gate
- checkpoint: runs/m385_recovery_repair_micro_interpolation/checkpoints/alpha_0_00075.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m388_m267_row15_conflict_residual_design
- reason: M387 classifies M386 as proof-safe micro retention not meaningful driver improvement; M267/M264 row15 flips at alpha 0.001 so next design must handle cross-surface conflict

## Next Blocker

m388-m267-row15-conflict-residual-design
