# m373-old-key-gap-tail-feedback-implementation Research Review

## Summary

- Generated at UTC: 20260523T122736Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: admit_m374_gap_tail_weighted_repair_probe
- Decision reason: M373 implements gap-tail overlay support exports a 40-row old-key corpus with one hard row and five gap-tail rows and verifies no-update exact repair integration without actor-input changes PPO or promotion

## Hypothesis

Gap-tail overlay support can make replay-discovered old-key lower-tail erosion visible to the differentiable repair surrogate while preserving actor-input contract and existing hard-row behavior.

## Lineage

- parent_checkpoint: runs/m369_hard_row_repair_interpolation/checkpoints/alpha_0_4.pt
- parent_dataset: docs/m372-old-key-gap-distribution-retention-design.md, runs/m371_alpha06_gap_audit/alpha04_alpha06_gap_audit_rows.csv
- parent_config: experiments/manifests/m372-old-key-gap-distribution-retention-design.json
- parent_objective: implement gap-tail old-key overlay support and branch-weight feedback
- derived_from: m372-old-key-gap-distribution-retention-design
- blocked_by: m372-old-key-gap-distribution-retention-design
- supersedes: None
- invalidates: None

## Success Criteria

- old-key preference corpus accepts optional gap-tail overlay CSV
- corpus NPZ records gap_tail_row and branch-weight arrays when overlay is present
- hard-row-only and no-overlay corpora remain backward-compatible
- exact repair branch-weighted surrogate works with gap-tail arrays
- research validation passes

## Failure Criteria

- gap-tail overlay changes deployable actor inputs
- existing old-key corpus behavior changes when overlay is absent
- hard-row overlay behavior regresses
- tests fail
- research validation fails

## Evidence Gates

- infrastructure implementation only; no PPO run
- gap-tail overlay does not change actor inputs
- old-key corpus remains backward-compatible when overlay absent
- hard-row overlay behavior from M368 remains valid
- focused tests pass
- research validation passes

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not promote a checkpoint
- do not lower old-key thresholds
- do not add hidden vehicle parameters or oracle labels to actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m373-old-key-gap-tail-feedback-implementation
- type: infrastructure
- checkpoint: runs/m369_hard_row_repair_interpolation/checkpoints/alpha_0_4.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m374_gap_tail_weighted_repair_probe
- reason: M373 implements gap-tail overlay support exports a 40-row old-key corpus with one hard row and five gap-tail rows and verifies no-update exact repair integration without actor-input changes PPO or promotion

## Next Blocker

m374-gap-tail-weighted-repair-probe
