# m1028-v4-public-base-candidate-b-post-ppo-exact-repair-design Research Review

## Summary

- Generated at UTC: 20260526T215345Z
- Type: gate
- Gate tier: process
- Promotion decision: candidate_b_post_ppo_exact_repair_design_admit_m1029_probe
- Decision reason: M1028 designs no-PPO exact repair with M393 row15 conflict residual and M997 temporal plus first replay gates before any full gate

## Hypothesis

A post-PPO repair/projection step can be designed to keep useful M1026 PPO movement only after exact temporal retention and M267/M264 row 15 proof retention are restored.

## Lineage

- parent_checkpoint: runs/m1016_v4_public_base_m1013_exact_candidate_preflight/checkpoints/m1013_lam0030_a050.pt, runs/ppo_m1026_candidate_b_guarded_smoke_seed61026/checkpoint.pt
- parent_dataset: docs/m1027-v4-public-base-candidate-b-guarded-ppo-proof-washout-audit.md, runs/m1026_v4_public_base_candidate_b_guarded_ppo_smoke/raw_candidate_gate/full_gates/m267_m264_replay/boundary_replay_rows.csv, runs/m1026_v4_public_base_candidate_b_guarded_ppo_smoke/proof_replay_summary.csv, runs/m1026_v4_public_base_candidate_b_guarded_ppo_smoke/exact_retention_summary.csv
- parent_config: configs/ppo_m1026_candidate_b_guarded_smoke.json
- parent_objective: design exact post-PPO repair/projection after localized M1026 M267/M264 row 15 proof washout
- derived_from: m1027-v4-public-base-candidate-b-guarded-ppo-proof-washout-audit
- blocked_by: M1027 confirms M1026 proof washout is localized to M267/M264 row 15 wrong-history branch lift
- supersedes: None
- invalidates: longer PPO before exact post-PPO repair/projection design, raw M1026 checkpoint promotion

## Success Criteria

- design artifact exists
- theta_base theta_raw and candidate output are defined
- lexicographic repair constraints are explicit
- row 15 rejected-history branch constraint is explicit
- gate order for implementation is explicit
- no training PPO promotion or private holdout occurs

## Failure Criteria

- design runs repair or PPO
- design omits row 15 proof retention
- design allows scalar aggregate metrics to override proof replay
- design changes actor inputs
- design uses private holdout or promotes a checkpoint

## Evidence Gates

- M1028 must design only and not train
- M1028 must not promote
- M1028 must not use private holdout
- M1028 must preserve P0 actor inputs
- M1028 must define exact/proof/generalization/behavior ordering before repair implementation
- M1028 must include row 15 rejected-history retention as a first-class constraint

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run repair in the design milestone
- do not run longer PPO
- do not tune scalar PPO aux coefficients before repair design
- do not change actor inputs
- do not promote raw M1026 or any repair candidate from the design milestone

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1028-v4-public-base-candidate-b-post-ppo-exact-repair-design
- type: gate
- checkpoint: docs/m1028-v4-public-base-candidate-b-post-ppo-exact-repair-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: candidate_b_post_ppo_exact_repair_design_admit_m1029_probe
- reason: M1028 designs no-PPO exact repair with M393 row15 conflict residual and M997 temporal plus first replay gates before any full gate

## Next Blocker

m1029-v4-public-base-candidate-b-post-ppo-exact-repair-probe
