# m633-targeted-source8-projected-shape-implementation Research Review

## Summary

- Generated at UTC: 20260524T112057Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: targeted_source8_projected_shape_implementation_pass_admit_audit
- Decision reason: M633 recovers sources 8 and 0 and preserves source 30 but regresses source 7 sentinel so optimizer admission remains blocked

## Hypothesis

A source-8 local projected shape search can recover source 8 or improve it materially while preserving trust limits and sentinel sources.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m630_trust_projected_sequence_shape/projected_sequence_candidates.csv, runs/m630_trust_projected_sequence_shape/source_recovery_summary.csv, docs/m632-targeted-source8-projected-shape-design.md
- parent_config: experiments/manifests/m632-targeted-source8-projected-shape-design.json, docs/m631-trust-projected-sequence-shape-audit.md
- parent_objective: implement source-8 targeted projected candidate-shape search
- derived_from: m632-targeted-source8-projected-shape-design
- blocked_by: m632-targeted-source8-projected-shape-design
- supersedes: None
- invalidates: None

## Success Criteria

- implementation writes targeted candidate and source summary artifacts
- focused tests cover explicit source-id filtering and targeted families
- real run preserves trust limits
- summary records source8 source0 source7 and source30 outcomes
- research validation passes

## Failure Criteria

- implementation changes thresholds
- implementation starts training
- implementation runs PPO
- implementation promotes checkpoint
- implementation admits optimizer training
- implementation merges collision-primary rows

## Evidence Gates

- write targeted projected candidate artifacts
- report source8 recovery and source0 secondary result
- report source7 and source30 regression sentinels
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
- do not omit source 7 or 30 sentinels
- do not include collision-primary sources

## Failure Taxonomy

- none

## Scoreboard

- milestone: m633-targeted-source8-projected-shape-implementation
- type: infrastructure
- checkpoint: runs/m633_targeted_source8_projected_shape/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: targeted_source8_projected_shape_implementation_pass_admit_audit
- reason: M633 recovers sources 8 and 0 and preserves source 30 but regresses source 7 sentinel so optimizer admission remains blocked

## Next Blocker

m634-targeted-source8-projected-shape-audit
