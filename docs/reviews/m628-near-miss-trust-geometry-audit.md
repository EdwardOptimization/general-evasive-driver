# m628-near-miss-trust-geometry-audit Research Review

## Summary

- Generated at UTC: 20260524T103945Z
- Type: gate
- Gate tier: process
- Promotion decision: near_miss_trust_geometry_audit_admit_projected_shape_design
- Decision reason: M628 audits M627 and selects projected smoother sequence-shape design for trust-primary low or zero accepted sources while separating collision-primary rows and keeping optimizer admission blocked

## Hypothesis

M627 near-miss geometry can determine whether the next no-training step should design projected smoother sequence candidates or return to source re-mining and safety shaping.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m627_near_miss_trust_geometry/summary.json, runs/m627_near_miss_trust_geometry/near_miss_candidates.csv, runs/m627_near_miss_trust_geometry/near_miss_sources.csv, docs/m627-near-miss-trust-geometry-analyzer.md
- parent_config: experiments/manifests/m627-near-miss-trust-geometry-analyzer.json, docs/m626-near-miss-trust-geometry-design.md
- parent_objective: audit near-miss trust geometry before choosing candidate-shape or source branch
- derived_from: m627-near-miss-trust-geometry-analyzer
- blocked_by: m627-near-miss-trust-geometry-analyzer
- supersedes: None
- invalidates: None

## Success Criteria

- audit interprets M627 primary failure and constraint-flag counts
- audit separates trust-primary and collision-primary blockers
- audit decides a next no-training branch
- audit explicitly keeps optimizer admission training PPO and promotion blocked unless diversity evidence is sufficient
- research validation passes

## Failure Criteria

- audit starts training
- audit promotes a checkpoint
- audit relaxes trust regions
- audit lowers target thresholds
- audit ignores source-level diversity
- audit merges collision-primary and trust-primary blockers

## Evidence Gates

- classify whether near misses are primarily trust geometry safety or source-row issues
- decide whether next branch should be projected candidate shapes source re-mining or safety shaping
- keep trust regions unchanged
- keep target thresholds unchanged
- keep actor training and PPO blocked
- do not claim optimizer admission from near-miss candidates

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote checkpoint
- do not widen trust regions
- do not lower target thresholds
- do not treat candidate count as source-level diversity
- do not use collision-primary rows as trust-region evidence

## Failure Taxonomy

- none

## Scoreboard

- milestone: m628-near-miss-trust-geometry-audit
- type: gate
- checkpoint: docs/m628-near-miss-trust-geometry-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: near_miss_trust_geometry_audit_admit_projected_shape_design
- reason: M628 audits M627 and selects projected smoother sequence-shape design for trust-primary low or zero accepted sources while separating collision-primary rows and keeping optimizer admission blocked

## Next Blocker

m629-candidate-shape-branch-design
