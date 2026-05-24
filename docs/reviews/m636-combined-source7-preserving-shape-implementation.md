# m636-combined-source7-preserving-shape-implementation Research Review

## Summary

- Generated at UTC: 20260524T114203Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: combined_source7_preserving_shape_implementation_pass_admit_audit
- Decision reason: M636 preserves trust limits and yields accepted candidates for all four focused sources 8 0 7 and 30 while keeping optimizer admission blocked

## Hypothesis

A combined two-grid projected search can recover source8 and source0 while restoring source7 and preserving source30 under unchanged trust limits.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m633_targeted_source8_projected_shape/source_recovery_summary.csv, runs/m630_trust_projected_sequence_shape/accepted_projected_sequences.csv, docs/m635-combined-source7-preserving-shape-design.md
- parent_config: experiments/manifests/m635-combined-source7-preserving-shape-design.json, docs/m634-targeted-source8-projected-shape-audit.md
- parent_objective: implement combined source8 recovery and source7 preservation projected grid
- derived_from: m635-combined-source7-preserving-shape-design
- blocked_by: m635-combined-source7-preserving-shape-design
- supersedes: None
- invalidates: None

## Success Criteria

- implementation writes combined artifacts
- focused tests cover grid group definitions and combined source summary
- real run preserves trust limits
- summary reports all four source outcomes
- research validation passes

## Failure Criteria

- implementation changes thresholds
- implementation starts training
- implementation runs PPO
- implementation promotes checkpoint
- implementation admits optimizer training
- implementation omits source-level summary

## Evidence Gates

- write combined candidate and source recovery artifacts
- report source8 source0 source7 and source30 outcomes
- preserve all trust limits and thresholds
- keep actor training and PPO blocked
- do not promote or admit optimizer training

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote checkpoint
- do not widen trust regions
- do not lower target thresholds
- do not drop source7 from evaluation
- do not treat four source rows as sufficient for optimizer admission without audit

## Failure Taxonomy

- none

## Scoreboard

- milestone: m636-combined-source7-preserving-shape-implementation
- type: infrastructure
- checkpoint: runs/m636_combined_source7_preserving_shape/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: combined_source7_preserving_shape_implementation_pass_admit_audit
- reason: M636 preserves trust limits and yields accepted candidates for all four focused sources 8 0 7 and 30 while keeping optimizer admission blocked

## Next Blocker

m637-combined-source7-preserving-shape-audit
