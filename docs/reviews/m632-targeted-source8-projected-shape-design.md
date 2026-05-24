# m632-targeted-source8-projected-shape-design Research Review

## Summary

- Generated at UTC: 20260524T110707Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: targeted_source8_projected_shape_design_admit_m633
- Decision reason: M632 designs source 8 targeted local projected shape search with source 0 secondary and sources 7 30 sentinels while preserving trust limits

## Hypothesis

Source 8 is close enough after M630 projection that a targeted local shape search may recover it without changing trust limits or thresholds.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m630_trust_projected_sequence_shape/summary.json, runs/m630_trust_projected_sequence_shape/source_recovery_summary.csv, runs/m630_trust_projected_sequence_shape/projected_sequence_candidates.csv, docs/m631-trust-projected-sequence-shape-audit.md
- parent_config: experiments/manifests/m631-trust-projected-sequence-shape-audit.json, docs/m630-trust-projected-sequence-shape-implementation.md
- parent_objective: design source-8 targeted projected sequence shape search after narrow positive M630
- derived_from: m631-trust-projected-sequence-shape-audit
- blocked_by: m631-trust-projected-sequence-shape-audit
- supersedes: None
- invalidates: None

## Success Criteria

- design identifies source 8 as the primary target and source 0 as secondary
- design specifies local projected candidate families and grids
- design specifies no-training artifacts and source-level recovery metrics
- design keeps optimizer admission training PPO promotion and threshold changes blocked
- research validation passes

## Failure Criteria

- design changes thresholds
- design widens trust regions
- design starts training
- design promotes a checkpoint
- design treats M630 as optimizer-ready
- design ignores source-level diversity

## Evidence Gates

- define source-8 local candidate-shape search
- preserve all trust limits and margin risk thresholds
- keep source 0 as secondary diagnostic and collision sources separate
- define artifacts for source-level recovery and raw versus targeted comparison
- keep actor training and PPO blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote checkpoint
- do not widen trust regions
- do not lower target thresholds
- do not call source 7 or 30 breadth sufficient
- do not merge collision-primary rows

## Failure Taxonomy

- none

## Scoreboard

- milestone: m632-targeted-source8-projected-shape-design
- type: infrastructure
- checkpoint: docs/m632-targeted-source8-projected-shape-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: targeted_source8_projected_shape_design_admit_m633
- reason: M632 designs source 8 targeted local projected shape search with source 0 secondary and sources 7 30 sentinels while preserving trust limits

## Next Blocker

m633-targeted-source8-projected-shape-implementation
