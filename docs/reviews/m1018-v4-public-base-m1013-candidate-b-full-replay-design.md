# m1018-v4-public-base-m1013-candidate-b-full-replay-design Research Review

## Summary

- Generated at UTC: 20260526T194659Z
- Type: gate
- Gate tier: proof
- Promotion decision: candidate_b_full_replay_design_admit_m1019_gate
- Decision reason: M1018 designs exact temporal retention six public replay source-diverse diagnostics and behavior seeds for Candidate B while keeping PPO promotion and private holdout blocked

## Hypothesis

Candidate B should be evaluated by the standard full public replay stack because it passed M267/M264 preflight despite the unsigned branch metric artifact.

## Lineage

- parent_checkpoint: runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt, runs/m1016_v4_public_base_m1013_exact_candidate_preflight/checkpoints/m1013_lam0030_a050.pt
- parent_dataset: docs/m1017-v4-public-base-signed-branch-metric-audit.md, runs/m1016_v4_public_base_m1013_exact_candidate_preflight/m267_preflight_summary.csv, runs/m1013_v4_public_base_margin_weighted_branch_repair_update_probe/interpolation_metrics.csv
- parent_config: experiments/manifests/m1017-v4-public-base-signed-branch-metric-audit.json
- parent_objective: design full public replay gate for M1013 Candidate B after M267/M264 preflight pass
- derived_from: m1017-v4-public-base-signed-branch-metric-audit
- blocked_by: Candidate B has passed only M267/M264 preflight and needs the full public replay gate before any promotion/generalization discussion
- supersedes: None
- invalidates: discarding Candidate B solely because of unsigned branch L2

## Success Criteria

- design document exists
- six public replay surfaces are specified
- exact temporal retention and behavior seeds are specified
- PPO and promotion remain blocked

## Failure Criteria

- design promotes Candidate B
- design uses private holdout
- design skips public proof surfaces
- design changes actor inputs

## Evidence Gates

- M1018 must not train
- M1018 must not run PPO
- M1018 must not promote
- M1018 must preserve P0 actor inputs
- M1018 must design full replay evaluation before Candidate B can advance

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not use private holdout
- do not promote Candidate B from M267/M264 alone
- do not skip exact temporal retention
- do not change actor input contract

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1018-v4-public-base-m1013-candidate-b-full-replay-design
- type: gate
- checkpoint: docs/m1018-v4-public-base-m1013-candidate-b-full-replay-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: candidate_b_full_replay_design_admit_m1019_gate
- reason: M1018 designs exact temporal retention six public replay source-diverse diagnostics and behavior seeds for Candidate B while keeping PPO promotion and private holdout blocked

## Next Blocker

m1019-v4-public-base-m1013-candidate-b-full-replay-gate
