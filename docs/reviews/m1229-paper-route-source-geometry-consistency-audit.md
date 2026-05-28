# m1229-paper-route-source-geometry-consistency-audit Research Review

## Summary

- Generated at UTC: 20260528T080710Z
- Type: gate
- Gate tier: proof
- Promotion decision: source_geometry_consistency_horizon_mismatch_route_to_short_horizon_relocation
- Decision reason: M1229 finds exact source geometry is short-horizon normal-success but long-horizon all-collision so next is short-horizon relocation materialization with no long-horizon or self-ID claim

## Hypothesis

M1227's all-collision result is caused by a source-geometry replay consistency or horizon mismatch, not by lack of source-diverse candidate coverage.

## Lineage

- parent_checkpoint: runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111602/checkpoint.pt
- parent_dataset: runs/m1226_terminal_boundary_candidate_export/candidate_outcomes.csv, runs/m1227_terminal_boundary_relocation_smoke/boundary_relocation_rows.csv, docs/m1228-paper-route-terminal-boundary-negative-audit.md
- parent_config: experiments/manifests/m1228-paper-route-terminal-boundary-negative-audit.json, configs/paper_route_corrected_profiles/m1207_l3_online_gru.json
- parent_objective: audit whether exact source geometry replay reproduces M1222 normal-success candidates under short and long horizons
- derived_from: m1228-paper-route-terminal-boundary-negative-audit
- blocked_by: M1227 exact source-geometry rows still collided under max_continuation_steps=60
- supersedes: expanding the relocation grid without source consistency evidence
- invalidates: assuming M1222 candidate normal_success transfers directly to M1227 relocation replay

## Success Criteria

- runs/m1229_source_geometry_consistency_short/summary.json exists
- runs/m1229_source_geometry_consistency_long/summary.json exists
- short and long horizon normal-success rates are reported
- horizon/source mismatch is classified
- private holdout remains unused
- no training, PPO, promotion, private holdout, profile tuning, or actor-input contract expansion occurs
- next route is selected

## Failure Criteria

- M1229 trains or tunes profiles
- private holdout is used
- offset or width-inflated relocation is mixed into the consistency audit
- all-collision rows are claimed as proof
- next route is left vague

## Evidence Gates

- M1229 may run source-geometry replay consistency only
- M1229 must preserve actor input contract
- M1229 must not train controllers
- M1229 must not run PPO
- M1229 must not use private holdout
- M1229 must not promote
- M1229 must compare short and long continuation horizons
- M1229 must not claim self-identification

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not use private holdout
- do not promote
- do not add hidden or oracle actor inputs
- do not use obstacle offsets or half-width inflation in the consistency audit
- do not treat all-collision rows as proof

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1229-paper-route-source-geometry-consistency-audit
- type: gate
- checkpoint: runs/m1229_source_geometry_consistency_short/summary.json;runs/m1229_source_geometry_consistency_long/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: source_geometry_consistency_horizon_mismatch_route_to_short_horizon_relocation
- reason: M1229 finds exact source geometry is short-horizon normal-success but long-horizon all-collision so next is short-horizon relocation materialization with no long-horizon or self-ID claim

## Next Blocker

m1230-paper-route-short-horizon-relocation-smoke
