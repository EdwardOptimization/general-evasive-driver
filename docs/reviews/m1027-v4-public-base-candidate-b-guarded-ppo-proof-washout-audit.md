# m1027-v4-public-base-candidate-b-guarded-ppo-proof-washout-audit Research Review

## Summary

- Generated at UTC: 20260526T213810Z
- Type: gate
- Gate tier: process
- Promotion decision: candidate_b_guarded_ppo_washout_localized_route_to_exact_repair_design
- Decision reason: M1027 localizes M1026 proof washout to M267/M264 row 15 wrong-history branch lift and routes to exact post-PPO repair design

## Hypothesis

M1026 proof washout is a localized wrong-history branch lift on M267/M264 rather than training instability, actor-input drift, exact-retention regression, or broad behavior regression.

## Lineage

- parent_checkpoint: runs/m1016_v4_public_base_m1013_exact_candidate_preflight/checkpoints/m1013_lam0030_a050.pt, runs/ppo_m1026_candidate_b_guarded_smoke_seed61026/checkpoint.pt
- parent_dataset: docs/m1026-v4-public-base-candidate-b-guarded-ppo-smoke.md, runs/m1026_v4_public_base_candidate_b_guarded_ppo_smoke/summary.json, runs/m1026_v4_public_base_candidate_b_guarded_ppo_smoke/proof_replay_summary.csv, runs/m1026_v4_public_base_candidate_b_guarded_ppo_smoke/exact_retention_summary.csv, runs/m1026_v4_public_base_candidate_b_guarded_ppo_smoke/generalization_comparison.csv, runs/m1026_v4_public_base_candidate_b_guarded_ppo_smoke/behavior_comparison.csv
- parent_config: configs/ppo_m1026_candidate_b_guarded_smoke.json, experiments/manifests/m1026-v4-public-base-candidate-b-guarded-ppo-smoke.json
- parent_objective: audit why the first Candidate B guarded PPO proposal passed exact/generalization/behavior but washed out M267/M264 proof retention
- derived_from: m1026-v4-public-base-candidate-b-guarded-ppo-smoke
- blocked_by: M1026 raw PPO retained exact temporal metrics and broad behavior but reduced M267/M264 success-drop count from 17 to 16
- supersedes: None
- invalidates: longer PPO from the same recipe before proof-washout audit, treating M1026 as training instability, promoting the raw M1026 PPO checkpoint

## Success Criteria

- audit artifact exists
- failed proof surface and row-level mechanism are identified as far as current artifacts allow
- training-instability wrapper artifact is separated from the true proof result
- route decision is explicit
- no PPO, training, promotion, or private holdout occurs

## Failure Criteria

- audit reruns PPO instead of diagnosing M1026
- audit promotes or accepts raw M1026 despite proof washout
- audit omits M267/M264 failed-surface evidence
- audit changes actor inputs
- audit uses private holdout

## Evidence Gates

- M1027 must not train or run PPO
- M1027 must not promote
- M1027 must not use private holdout
- M1027 must preserve the P0 actor-input contract
- M1027 must audit the M267/M264 failed row or rows from M1026
- M1027 must decide between exact repair/projection design, PPO recipe audit, or surface refresh

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not rerun longer PPO
- do not tune scalar PPO coefficients before the audit
- do not change actor inputs
- do not promote raw M1026
- do not ignore the M267/M264 success-drop regression because broad metrics passed

## Failure Taxonomy

- proof_washout

## Scoreboard

- milestone: m1027-v4-public-base-candidate-b-guarded-ppo-proof-washout-audit
- type: gate
- checkpoint: docs/m1027-v4-public-base-candidate-b-guarded-ppo-proof-washout-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: candidate_b_guarded_ppo_washout_localized_route_to_exact_repair_design
- reason: M1027 localizes M1026 proof washout to M267/M264 row 15 wrong-history branch lift and routes to exact post-PPO repair design

## Next Blocker

m1028-v4-public-base-candidate-b-post-ppo-exact-repair-design
