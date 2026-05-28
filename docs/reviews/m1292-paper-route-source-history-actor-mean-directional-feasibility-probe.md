# m1292-paper-route-source-history-actor-mean-directional-feasibility-probe Research Review

## Summary

- Generated at UTC: 20260528T142928Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: source_history_actor_mean_directional_feasibility_mixed_route_to_result_audit
- Decision reason: M1292 actor_mean feasibility is mixed: best both_directional_fraction 0.184 with 28/152 both-positive rows and no non-actor mutation; no PPO or promotion

## Hypothesis

A no-PPO actor_mean-only directional feasibility probe can determine whether fixed source-history features can satisfy row-wise correct-history and wrong-history preferences.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt, runs/m1288_source_history_objective_only_update/checkpoints/raw_objective_update.pt
- parent_dataset: docs/m1291-paper-route-source-history-directional-repair-design.md, runs/m1290_source_history_directional_conflict_audit/summary.json, runs/m1290_source_history_directional_conflict_audit/directional_conflict_rows.csv, runs/m1280_four_wheel_source_response_history_materialization/history_frame_rows.csv, runs/m1280_four_wheel_source_response_history_materialization/history_intervention_rows.csv, runs/m1280_four_wheel_source_response_history_materialization/wrong_history_pair_rows.csv, runs/m1277_four_wheel_source_intervention_materialization/intervention_observations.csv, runs/m1277_four_wheel_source_intervention_materialization/intervention_action_sequences.csv
- parent_config: experiments/manifests/m1291-paper-route-source-history-directional-repair-design.json
- parent_objective: implement no-PPO actor_mean directional feasibility probe for M1290 mutually-exclusive source-history rows
- derived_from: m1291-paper-route-source-history-directional-repair-design
- blocked_by: M1291 designs the feasibility probe but no implementation artifacts exist
- supersedes: continuing scalar source-history objective updates without feasibility evidence
- invalidates: None

## Success Criteria

- runs/m1292_source_history_actor_mean_directional_feasibility_probe/summary.json exists
- candidate summaries and directional rows exist
- focused tests pass
- both_directional_fraction is reported for each initialization
- mutation guard confirms only actor_mean changed
- result class is actor_mean feasible, mixed, or capacity-limited
- no PPO, promotion, private holdout, threshold relaxation, or actor-input expansion occurs

## Failure Criteria

- run artifacts are missing
- directional metrics are missing
- forbidden parameters change
- PPO starts
- private holdout is used
- checkpoint is promoted
- actor input contract changes
- thresholds are relaxed after seeing results

## Evidence Gates

- M1292 must preserve actor input contract
- M1292 must not run PPO
- M1292 must not use private holdout
- M1292 must not promote
- M1292 must update only actor_mean parameters in diagnostic candidates
- M1292 must report both_directional_fraction and mutually-exclusive fraction for every initialization
- M1292 must decide whether actor_mean-only is feasible, mixed, or capacity-limited

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not promote
- do not use private holdout
- do not add actor inputs
- do not update GRU encoder context fusion critic log_std or sequence-tail parameters
- do not treat scalar loss improvement as directional feasibility
- do not overclaim self-identification

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1292-paper-route-source-history-actor-mean-directional-feasibility-probe
- type: infrastructure
- checkpoint: runs/m1292_source_history_actor_mean_directional_feasibility_probe/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: source_history_actor_mean_directional_feasibility_mixed_route_to_result_audit
- reason: M1292 actor_mean feasibility is mixed: best both_directional_fraction 0.184 with 28/152 both-positive rows and no non-actor mutation; no PPO or promotion

## Next Blocker

m1293-paper-route-source-history-actor-mean-feasibility-result-audit
