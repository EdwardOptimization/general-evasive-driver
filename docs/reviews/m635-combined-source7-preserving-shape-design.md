# m635-combined-source7-preserving-shape-design Research Review

## Summary

- Generated at UTC: 20260524T113132Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: combined_source7_preserving_shape_design_admit_m636
- Decision reason: M635 designs a two-grid combined projected search to keep source8 source0 source30 gains while restoring source7 preservation

## Hypothesis

A combined projected grid can keep source8 and source0 recovered while restoring source7 and preserving source30 without changing trust limits.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m633_targeted_source8_projected_shape/summary.json, runs/m633_targeted_source8_projected_shape/source_recovery_summary.csv, runs/m630_trust_projected_sequence_shape/accepted_projected_sequences.csv, docs/m634-targeted-source8-projected-shape-audit.md
- parent_config: experiments/manifests/m634-targeted-source8-projected-shape-audit.json, docs/m633-targeted-source8-projected-shape-implementation.md
- parent_objective: design combined source8 recovery and source7 preservation projected shape search
- derived_from: m634-targeted-source8-projected-shape-audit
- blocked_by: m634-targeted-source8-projected-shape-audit
- supersedes: None
- invalidates: None

## Success Criteria

- design specifies source8 recovery grid and source7 preservation grid
- design specifies implementation artifacts and pass criteria
- design keeps optimizer admission training PPO promotion threshold changes and trust-region relaxation blocked
- research validation passes

## Failure Criteria

- design changes thresholds
- design widens trust regions
- design starts training
- design promotes a checkpoint
- design treats M633 as optimizer-ready
- design omits source7 preservation

## Evidence Gates

- define combined source8 recovery and source7 preservation grids
- preserve all trust limits and thresholds
- define source-level pass criteria for sources 8 0 7 and 30
- keep actor training and PPO blocked
- do not claim optimizer admission from design

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote checkpoint
- do not widen trust regions
- do not lower target thresholds
- do not ignore source7 regression
- do not treat candidate count as source diversity

## Failure Taxonomy

- none

## Scoreboard

- milestone: m635-combined-source7-preserving-shape-design
- type: infrastructure
- checkpoint: docs/m635-combined-source7-preserving-shape-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: combined_source7_preserving_shape_design_admit_m636
- reason: M635 designs a two-grid combined projected search to keep source8 source0 source30 gains while restoring source7 preservation

## Next Blocker

m636-combined-source7-preserving-shape-implementation
