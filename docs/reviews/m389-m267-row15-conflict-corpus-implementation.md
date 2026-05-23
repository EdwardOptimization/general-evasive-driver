# m389-m267-row15-conflict-corpus-implementation Research Review

## Summary

- Generated at UTC: 20260523T141324Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: admit_m390_m267_conflict_residual_repair_probe
- Decision reason: M389 exports a two-row M267/M264 row15-row6 conflict corpus wires optional exact-repair residual and verifies no-update smoke; no PPO promotion or actor-input change

## Hypothesis

A replay-exported current-family conflict corpus can make M267/M264 row15 and row6 visible to exact repair as wrong-history boundary constraints without changing deployable actor inputs.

## Lineage

- parent_checkpoint: runs/m385_recovery_repair_micro_interpolation/checkpoints/alpha_0_00075.pt
- parent_dataset: docs/m388-m267-row15-conflict-residual-design.md, runs/m387_m386_micro_promotion_utility_audit/m267_row15_alpha_trace.csv
- parent_config: experiments/manifests/m388-m267-row15-conflict-residual-design.json
- parent_objective: implement current-family conflict corpus and residual wiring for M267/M264 row15 before more repair or PPO
- derived_from: m388-m267-row15-conflict-residual-design
- blocked_by: m388-m267-row15-conflict-residual-design
- supersedes: None
- invalidates: None

## Success Criteria

- export a compact conflict corpus for row15 and row6
- validate loader shape finite weight and action bounds
- wire optional exact-repair conflict residual
- run a no-update smoke with finite conflict loss
- research validation and focused tests pass

## Failure Criteria

- corpus cannot reconstruct row15/row6 snapshots
- loader accepts invalid shapes or nonfinite values
- exact repair cannot read the optional residual
- actor contract changes
- research validation fails

## Evidence Gates

- no PPO run
- loader/exporter tests pass
- no-update exact-repair smoke reads conflict corpus
- preserve actor input/output contract

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not promote checkpoint
- do not lower M267/M264 thresholds
- do not add hidden or oracle actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m389-m267-row15-conflict-corpus-implementation
- type: infrastructure
- checkpoint: runs/m385_recovery_repair_micro_interpolation/checkpoints/alpha_0_00075.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m390_m267_conflict_residual_repair_probe
- reason: M389 exports a two-row M267/M264 row15-row6 conflict corpus wires optional exact-repair residual and verifies no-update smoke; no PPO promotion or actor-input change

## Next Blocker

m390-m267-conflict-residual-repair-probe
