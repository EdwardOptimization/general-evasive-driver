# m372-old-key-gap-distribution-retention-design Research Review

## Summary

- Generated at UTC: 20260523T121627Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: not_applicable
- Decision reason: M372 completes when the gap-tail retention design is documented and an implementation milestone is registered without changing thresholds or actor inputs.

## Hypothesis

A gap-distribution retention overlay can make lower-tail old-key gap erosion visible to repair objectives without relying only on accepted-regression hard rows.

## Lineage

- parent_checkpoint: runs/m369_hard_row_repair_interpolation/checkpoints/alpha_0_4.pt, runs/m369_hard_row_repair_interpolation/checkpoints/alpha_0_6.pt
- parent_dataset: docs/m371-alpha06-old-key-gap-p10-audit.md, runs/m371_alpha06_gap_audit/alpha04_alpha06_gap_audit_rows.csv
- parent_config: experiments/manifests/m371-alpha06-old-key-gap-p10-audit.json
- parent_objective: design old-key gap-distribution retention feedback for lower-tail gap erosion
- derived_from: m371-alpha06-old-key-gap-p10-audit
- blocked_by: m371-alpha06-old-key-gap-p10-audit
- supersedes: None
- invalidates: None

## Success Criteria

- design specifies overlay fields for gap-tail rows and target p10 protection
- design separates accepted-regression hard rows from gap-tail retention rows
- design keeps closed-loop old-key replay as the proof gate
- design registers an implementation milestone
- research validation passes

## Failure Criteria

- design treats p10 failure as a reason to lower thresholds
- design changes actor inputs
- design skips closed-loop old-key replay
- research validation fails

## Evidence Gates

- design only; no PPO run
- keep alpha 0.4 as current promoted base
- do not lower old-key gap-p10 threshold
- preserve actor input contract
- define how replay-discovered gap-tail rows feed back into exact repair

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not promote alpha 0.6
- do not lower old-key thresholds
- do not add hidden or oracle actor inputs

## Failure Taxonomy

- none

## Scoreboard

- No scoreboard row recorded.

## Next Blocker

pending M372 old-key gap-distribution retention design
