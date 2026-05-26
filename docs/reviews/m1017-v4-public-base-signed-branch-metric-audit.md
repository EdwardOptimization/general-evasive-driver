# m1017-v4-public-base-signed-branch-metric-audit Research Review

## Summary

- Generated at UTC: 20260526T193613Z
- Type: gate
- Gate tier: process
- Promotion decision: signed_branch_metric_audit_route_to_candidate_b_full_public_replay_design
- Decision reason: M1017 diagnoses unsigned branch L2 as a detector but not ordering gate and routes Candidate B to full public replay design without promotion

## Hypothesis

M1016 can be explained by branch action direction: Candidate B has larger unsigned action drift but moves wrong-history margins negative, while Candidate A has smaller drift but moves rows 6 and 15 positive.

## Lineage

- parent_checkpoint: runs/m1016_v4_public_base_m1013_exact_candidate_preflight/checkpoints/m1013_lam0030_a050.pt, runs/m1016_v4_public_base_m1013_exact_candidate_preflight/checkpoints/m1013_lam0001_a020.pt
- parent_dataset: docs/m1016-v4-public-base-m1013-exact-candidate-preflight.md, runs/m1016_v4_public_base_m1013_exact_candidate_preflight/m267_preflight_summary.csv, runs/m1016_v4_public_base_m1013_exact_candidate_preflight/candidate_preflight/*/boundary_replay_rows.csv, runs/m1013_v4_public_base_margin_weighted_branch_repair_update_probe/interpolation_metrics.csv
- parent_config: experiments/manifests/m1016-v4-public-base-m1013-exact-candidate-preflight.json
- parent_objective: audit why L2 branch trust ordering disagrees with M267/M264 replay outcome
- derived_from: m1016-v4-public-base-m1013-exact-candidate-preflight
- blocked_by: M1016 shows Candidate B passes preflight despite higher L2 branch trust loss than failing Candidate A
- supersedes: None
- invalidates: using unsigned branch action L2 as candidate ordering objective by itself

## Success Criteria

- audit document exists
- metric artifact is explained or rejected
- next route is explicit
- PPO and promotion remain blocked

## Failure Criteria

- audit promotes Candidate B
- audit runs new training
- audit uses private holdout
- audit changes actor inputs

## Evidence Gates

- M1017 must not train
- M1017 must not run PPO
- M1017 must not promote
- M1017 must preserve P0 actor inputs
- M1017 must decide whether to design signed/outcome-aware branch residuals or run full replay for Candidate B

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not treat Candidate B preflight pass as promotion
- do not use private holdout
- do not run new actor update
- do not change actor input contract

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1017-v4-public-base-signed-branch-metric-audit
- type: gate
- checkpoint: docs/m1017-v4-public-base-signed-branch-metric-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: signed_branch_metric_audit_route_to_candidate_b_full_public_replay_design
- reason: M1017 diagnoses unsigned branch L2 as a detector but not ordering gate and routes Candidate B to full public replay design without promotion

## Next Blocker

m1018-v4-public-base-m1013-candidate-b-full-replay-design
