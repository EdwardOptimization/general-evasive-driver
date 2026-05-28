# m1294-paper-route-source-history-pair-group-objective-design Research Review

## Summary

- Generated at UTC: 20260528T143446Z
- Type: gate
- Gate tier: process
- Promotion decision: source_history_pair_group_objective_design_admit_bounded_actor_mean_implementation
- Decision reason: M1294 designs no-PPO pair-group actor_mean objective and admits bounded M1295 probe with group-level directional gates

## Hypothesis

A pair-group directional objective can be designed to target M1292 mutually-exclusive rows more directly than scalar row-wise actor_mean optimization.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt, runs/m1288_source_history_objective_only_update/checkpoints/raw_objective_update.pt
- parent_dataset: docs/m1293-paper-route-source-history-actor-mean-feasibility-result-audit.md, runs/m1292_source_history_actor_mean_directional_feasibility_probe/summary.json, runs/m1292_source_history_actor_mean_directional_feasibility_probe/candidate_summaries.csv, runs/m1292_source_history_actor_mean_directional_feasibility_probe/directional_feasibility_rows.csv, runs/m1290_source_history_directional_conflict_audit/directional_conflict_rows.csv
- parent_config: experiments/manifests/m1293-paper-route-source-history-actor-mean-feasibility-result-audit.json
- parent_objective: design pair-group directional objective after M1292 mixed actor_mean feasibility
- derived_from: m1293-paper-route-source-history-actor-mean-feasibility-result-audit
- blocked_by: M1292 best_both_directional_fraction is only 0.1842105263 and requires pair-group repair design
- supersedes: continuing row-wise actor_mean optimization without pair-group structure
- invalidates: None

## Success Criteria

- docs/m1294-paper-route-source-history-pair-group-objective-design.md exists
- design specifies pair-group objective
- design specifies group-level directional metrics
- design admits bounded implementation or routes to scope/corpus audit
- no training, PPO, promotion, private holdout, threshold relaxation, or actor-input expansion occurs

## Failure Criteria

- design document is missing
- design ignores M1292 mixed result
- design ignores pair/probe group structure
- design starts PPO directly
- design overclaims self-identification
- training, PPO, private holdout, promotion, threshold relaxation, or actor-input expansion occurs

## Evidence Gates

- M1294 must preserve actor input contract
- M1294 must not train
- M1294 must not run PPO
- M1294 must not use private holdout
- M1294 must not promote
- M1294 must design a pair-group directional objective that targets both rows in each pair/probe group
- M1294 must specify exact pass/fail gates before implementation

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote
- do not use private holdout
- do not add actor inputs
- do not treat M1292 mixed result as solved
- do not overclaim self-identification

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1294-paper-route-source-history-pair-group-objective-design
- type: gate
- checkpoint: docs/m1294-paper-route-source-history-pair-group-objective-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: source_history_pair_group_objective_design_admit_bounded_actor_mean_implementation
- reason: M1294 designs no-PPO pair-group actor_mean objective and admits bounded M1295 probe with group-level directional gates

## Next Blocker

m1295-paper-route-source-history-pair-group-objective-probe
