# m1617-paper-route-contour-aware-candidate-objective-design Research Review

## Summary

- Generated at UTC: 20260529T182726Z
- Type: gate
- Gate tier: process
- Promotion decision: contour_aware_candidate_objective_design_admit_audit_and_synthesis
- Decision reason: M1617 designs lexicographic candidate objective semantics and admits required design audit/synthesis before any evaluator implementation while blocking loss construction training PPO promotion and private holdout

## Hypothesis

A design-only objective can define lexicographic candidate and diagnostic roles before any objective construction or training.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m1615_contour_aware_candidate_corpus/summary.json, runs/m1615_contour_aware_candidate_corpus/positive_candidate_rows.csv, runs/m1615_contour_aware_candidate_corpus/diagnostic_guardrail_rows.csv, docs/m1616-paper-route-contour-aware-candidate-corpus-export-result-audit.md
- parent_config: experiments/manifests/m1616-paper-route-contour-aware-candidate-corpus-export-result-audit.json
- parent_objective: design contour-aware candidate objective without constructing it
- derived_from: m1616-paper-route-contour-aware-candidate-corpus-export-result-audit
- blocked_by: M1616 admits design-only objective planning but blocks objective construction and training
- supersedes: direct objective construction from M1615, direct actor update from M1615, direct PPO after M1615
- invalidates: None

## Success Criteria

- docs/m1617-paper-route-contour-aware-candidate-objective-design.md exists
- objective semantics are explicit
- positive candidate and diagnostic guardrail roles are lexicographically separated
- exact full-corpus check requirements are explicit
- post-design audit or implementation route is explicit
- training PPO promotion private holdout objective construction and self-ID claims remain blocked

## Failure Criteria

- design document is missing
- design constructs a loss or objective config
- design treats diagnostics as positive candidates
- design routes directly to training PPO promotion private holdout objective construction or actor-input changes

## Evidence Gates

- M1617 must design the objective without constructing or running it
- M1617 must keep positive candidates and diagnostic guardrails lexicographically separated
- M1617 must require exact full-corpus checks before any update
- M1617 must require audit before implementation
- M1617 must keep training PPO promotion and private holdout blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not construct a loss
- do not construct an objective
- do not train
- do not run PPO
- do not run implementation smoke
- do not promote a checkpoint
- do not use private holdout
- do not add actor inputs
- do not claim level3 self-identification

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1617-paper-route-contour-aware-candidate-objective-design
- type: gate
- checkpoint: docs/m1617-paper-route-contour-aware-candidate-objective-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: contour_aware_candidate_objective_design_admit_audit_and_synthesis
- reason: M1617 designs lexicographic candidate objective semantics and admits required design audit/synthesis before any evaluator implementation while blocking loss construction training PPO promotion and private holdout

## Next Blocker

m1618-paper-route-contour-aware-candidate-objective-design-audit-and-synthesis
