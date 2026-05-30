# m1767-completed-taxonomy-outcome-dominance-localization Research Review

## Summary

- Generated at UTC: 20260530T065227Z
- Type: gate
- Gate tier: process
- Promotion decision: diffuse_outcome_dominance_blocks_ranking_route_to_result_audit
- Decision reason: M1767 localizes completed taxonomy dominance into 305 dominant slices across 6 families and 12 profiles and keeps ranking blocked

## Hypothesis

Existing completed M1764 rows can localize the outcome dominance that blocks ranking.

## Lineage

- parent_checkpoint: not_applicable_outcome_localization
- parent_dataset: docs/m1766-completed-taxonomy-outcome-audit.md, runs/m1764_revised_scenario_taxonomy_single_seed_completion/episode_rows.csv, runs/m1764_revised_scenario_taxonomy_single_seed_completion/profile_aggregate.csv, runs/m1764_revised_scenario_taxonomy_single_seed_completion/scenario_family_aggregate.csv
- parent_config: experiments/manifests/m1766-completed-taxonomy-outcome-audit.json
- parent_objective: localize completed taxonomy outcome dominance before repair or comparison
- derived_from: m1766-completed-taxonomy-outcome-audit
- blocked_by: M1766 blocks controller-family ranking due outcome dominance
- supersedes: direct repair design without localization, direct controller-family ranking
- invalidates: None

## Success Criteria

- docs/m1767-completed-taxonomy-outcome-dominance-localization.md exists
- localization uses only M1764 artifacts
- dominant slices or diffuse dominance are explicit
- next route is explicit
- rollout training replay PPO promotion private holdout actor-input changes profile tuning ranking paper-level and level3 claims remain blocked

## Failure Criteria

- localization document is missing
- localization runs new rollout or changes configs
- localization ranks controller families
- localization claims paper-level or level3 evidence
- next route is ambiguous

## Evidence Gates

- M1767 must use only existing M1764 episode/aggregate artifacts
- M1767 must localize dominant failure slices by evaluation role metric family scenario family profile hidden dynamics road timing and lateral buckets
- M1767 must not run rollout train replay PPO promote use private holdout change actor inputs or rank controller families
- M1767 must decide whether to route to repair design branch synthesis metric-semantics audit or stop

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run environment rollout
- do not train
- do not run replay
- do not run PPO
- do not promote a checkpoint
- do not use private holdout
- do not change actor inputs
- do not change reward
- do not change dynamics
- do not change termination behavior
- do not change profile configs
- do not change scenario specs
- do not tune profiles
- do not rank controller families
- do not claim paper-level evidence
- do not claim level3 self-identification

## Failure Taxonomy

- behavior_regression
- metric_artifact

## Scoreboard

- milestone: m1767-completed-taxonomy-outcome-dominance-localization
- type: gate
- checkpoint: docs/m1767-completed-taxonomy-outcome-dominance-localization.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: diffuse_outcome_dominance_blocks_ranking_route_to_result_audit
- reason: M1767 localizes completed taxonomy dominance into 305 dominant slices across 6 families and 12 profiles and keeps ranking blocked

## Next Blocker

m1768-completed-taxonomy-outcome-dominance-result-audit
