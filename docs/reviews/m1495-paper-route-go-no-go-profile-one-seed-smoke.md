# m1495-paper-route-go-no-go-profile-one-seed-smoke Research Review

## Summary

- Generated at UTC: 20260529T072320Z
- Type: gate
- Gate tier: process
- Promotion decision: go_no_go_profile_one_seed_smoke_completed_route_to_audit
- Decision reason: M1495 one-seed plumbing completes all 12 profile runs with finite metrics; L2 trends strongest but one seed cannot support ranking

## Hypothesis

The refreshed 12-profile go/no-go matrix can complete one matched fixed-budget train/eval seed per profile with finite metrics.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m1494_go_no_go_profile_runtime_smoke/summary.json, configs/paper_route_corrected_profiles
- parent_config: experiments/manifests/m1494-paper-route-go-no-go-profile-runtime-smoke.json
- parent_objective: run one fixed-budget train/eval seed per profile as plumbing smoke
- derived_from: m1494-paper-route-go-no-go-profile-runtime-smoke
- blocked_by: full 12-profile runtime smoke has passed, but no fixed-budget training/eval plumbing has been run
- supersedes: jumping directly to three-seed profile pilot without one-seed smoke
- invalidates: None

## Success Criteria

- runs/m1495_go_no_go_profile_one_seed_smoke/summary.json exists
- profile_count is 12
- total_seed_runs is 12
- completed_seed_runs is 12
- failed_seed_runs is 0
- all_eval_metrics_finite is true
- private_holdout_used is false
- promoted is false
- profile_specific_tuning is false
- actor_input_contract_changed is false

## Failure Criteria

- run summary is missing
- any profile seed run fails
- selected eval metrics are non-finite
- private holdout promotion profile-specific tuning or actor-input change occurs

## Evidence Gates

- M1495 must run exactly one fixed-budget training seed per selected profile
- M1495 must use the same training budget, optimizer policy, and eval seed block for all profiles
- M1495 must report completion and finite selected metrics only as plumbing evidence
- M1495 must block promotion private holdout profile ranking and self-ID claims

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not promote
- do not use private holdout
- do not add actor inputs
- do not export corpus
- do not tune one profile from results
- do not claim architecture ranking or recurrent self-identification from one seed

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1495-paper-route-go-no-go-profile-one-seed-smoke
- type: gate
- checkpoint: runs/m1495_go_no_go_profile_one_seed_smoke/summary.json
- success_rate: 0.6875
- termination_rate: 0.3125
- clearance_margin_mean: 0.8825418048258981
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: go_no_go_profile_one_seed_smoke_completed_route_to_audit
- reason: M1495 one-seed plumbing completes all 12 profile runs with finite metrics; L2 trends strongest but one seed cannot support ranking

## Next Blocker

m1496-paper-route-go-no-go-one-seed-result-audit
