# m629-trust-projected-sequence-shape-design Research Review

## Summary

- Generated at UTC: 20260524T104710Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: trust_projected_sequence_shape_design_admit_m630
- Decision reason: M629 designs radial projection and smoother sequence families for trust-primary low or zero accepted sources while preserving existing trust limits and blocking training

## Hypothesis

Projected or smoother sequence candidates can test whether M627 trust-primary near misses can be converted into accepted source rows while preserving existing trust limits.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m627_near_miss_trust_geometry/summary.json, runs/m627_near_miss_trust_geometry/near_miss_candidates.csv, runs/m627_near_miss_trust_geometry/near_miss_sources.csv, docs/m628-near-miss-trust-geometry-audit.md
- parent_config: experiments/manifests/m628-near-miss-trust-geometry-audit.json, docs/m627-near-miss-trust-geometry-analyzer.md
- parent_objective: design projected or smoother sequence candidate pass after near-miss trust geometry audit
- derived_from: m628-near-miss-trust-geometry-audit
- blocked_by: m628-near-miss-trust-geometry-audit
- supersedes: None
- invalidates: None

## Success Criteria

- design specifies source filters for trust-primary low or zero accepted rows
- design specifies projection or shaping rules that preserve all trust limits
- design specifies comparison metrics for raw versus projected candidate utility and source diversity
- design keeps training PPO promotion optimizer admission threshold changes and trust-region relaxation blocked
- research validation passes

## Failure Criteria

- design relaxes trust limits
- design lowers margin or risk thresholds
- design starts training
- design promotes a checkpoint
- design ignores collision-primary separation
- design uses candidate count as optimizer-admission evidence

## Evidence Gates

- define projected or smoother sequence candidate families
- preserve sequence_mean_l2 max_l2 and delta_delta_l2 limits
- focus trust-primary low or zero accepted sources separately from collision-primary sources
- define artifacts for raw versus projected candidate utility
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
- do not mix collision-primary rows into trust-only projected candidates
- do not treat candidate count as source-level diversity

## Failure Taxonomy

- none

## Scoreboard

- milestone: m629-trust-projected-sequence-shape-design
- type: infrastructure
- checkpoint: docs/m629-trust-projected-sequence-shape-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: trust_projected_sequence_shape_design_admit_m630
- reason: M629 designs radial projection and smoother sequence families for trust-primary low or zero accepted sources while preserving existing trust limits and blocking training

## Next Blocker

m630-trust-projected-sequence-shape-implementation
