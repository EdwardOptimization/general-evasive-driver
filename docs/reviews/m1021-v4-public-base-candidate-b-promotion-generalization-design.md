# m1021-v4-public-base-candidate-b-promotion-generalization-design Research Review

## Summary

- Generated at UTC: 20260526T201436Z
- Type: gate
- Gate tier: promotion
- Promotion decision: candidate_b_promotion_generalization_design_admit_m1022_gate
- Decision reason: M1021 designs a no-training tiered promotion/generalization gate for Candidate B with exact retention proof replay fresh public OOD behavior and decision tiers

## Hypothesis

Candidate B can only be considered for public-base promotion after a separate promotion/generalization protocol that goes beyond M1019 public replay evidence.

## Lineage

- parent_checkpoint: runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt, runs/m1016_v4_public_base_m1013_exact_candidate_preflight/checkpoints/m1013_lam0030_a050.pt
- parent_dataset: runs/m1019_v4_public_base_m1013_candidate_b_full_replay_gate/summary.json, docs/m1020-v4-public-base-temporal-sequence-objective-post-candidate-b-synthesis.md
- parent_config: experiments/manifests/m1020-v4-public-base-temporal-sequence-objective-post-candidate-b-synthesis.json
- parent_objective: design Candidate B promotion/generalization audit after M1019 public gate pass and M1020 synthesis
- derived_from: m1020-v4-public-base-temporal-sequence-objective-post-candidate-b-synthesis
- blocked_by: Candidate B has public replay evidence but no promotion/generalization audit
- supersedes: None
- invalidates: promoting Candidate B directly from M1019

## Success Criteria

- design artifact exists
- proof retention, fresh public generalization, behavior, and promotion tiers are specified
- M974 base and Candidate B checkpoint lineage are explicit
- PPO and promotion remain blocked

## Failure Criteria

- design promotes Candidate B
- design uses private holdout
- design skips fresh public generalization
- design changes actor inputs

## Evidence Gates

- M1021 must design proof retention, fresh public generalization, behavior ablation, and promotion decision tiers
- M1021 must not train
- M1021 must not run PPO
- M1021 must not promote
- M1021 must preserve P0 actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not use private holdout
- do not promote Candidate B from design alone
- do not skip fresh public generalization
- do not use stale baselines instead of M974
- do not change actor input contract

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1021-v4-public-base-candidate-b-promotion-generalization-design
- type: gate
- checkpoint: docs/m1021-v4-public-base-candidate-b-promotion-generalization-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: candidate_b_promotion_generalization_design_admit_m1022_gate
- reason: M1021 designs a no-training tiered promotion/generalization gate for Candidate B with exact retention proof replay fresh public OOD behavior and decision tiers

## Next Blocker

m1022-v4-public-base-candidate-b-promotion-generalization-gate
