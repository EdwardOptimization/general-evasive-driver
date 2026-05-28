# m1365-paper-route-bidirectional-broader-public-replay Research Review

## Summary

- Generated at UTC: 20260528T204325Z
- Type: gate
- Gate tier: proof
- Promotion decision: bidirectional_broader_public_replay_pass_route_to_result_audit
- Decision reason: M1365 passes six public replay surfaces source-diverse protected diagnostics and behavior seeds for M1362 alpha 0.1 without promotion

## Hypothesis

M1362 alpha 0.1 may retain broader public replay and behavior diagnostics after passing exact metrics and two replay preflight surfaces.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt, runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: docs/m1364-paper-route-bidirectional-broader-public-replay-design.md, runs/m1362_bidirectional_active_set_interpolation_preflight/summary.json
- parent_config: experiments/manifests/m1364-paper-route-bidirectional-broader-public-replay-design.json, configs/m121_human_view_zero_obstacle_relvel.json
- parent_objective: run broader public replay diagnostics for M1362 alpha 0.1 before any promotion route
- derived_from: m1364-paper-route-bidirectional-broader-public-replay-design
- blocked_by: M1364 designs the broader gate but it has not been run
- supersedes: direct promotion after M1364, direct PPO after M1364, private holdout before public replay
- invalidates: None

## Success Criteria

- runs/m1365_bidirectional_broader_public_replay/summary.json exists
- summary records six public replay surfaces
- summary records source-diverse and old-key diagnostics
- summary records behavior seeds 9505 and 9506
- summary records actor input contract status
- no training, PPO, promotion, private holdout, threshold relaxation, or actor-input expansion occurs

## Failure Criteria

- summary artifact is missing
- six public replay surface results are missing
- behavior seed results are missing
- PPO, private holdout, promotion, threshold relaxation, training, or actor-input expansion occurs

## Evidence Gates

- M1365 must not train
- M1365 must not run PPO
- M1365 must not use private holdout
- M1365 must not promote
- M1365 must preserve actor input contract
- M1365 must run the six public replay surfaces
- M1365 must record source-diverse protected and old-key diagnostics
- M1365 must record behavior seeds 9505 and 9506

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote
- do not use private holdout
- do not add actor inputs
- do not relax thresholds
- do not treat behavior as replacing replay proof
- do not claim driver performance
- do not claim strong self-identification

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1365-paper-route-bidirectional-broader-public-replay
- type: gate
- checkpoint: runs/m1365_bidirectional_broader_public_replay/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: bidirectional_broader_public_replay_pass_route_to_result_audit
- reason: M1365 passes six public replay surfaces source-diverse protected diagnostics and behavior seeds for M1362 alpha 0.1 without promotion

## Next Blocker

m1366-paper-route-bidirectional-broader-public-replay-result-audit
