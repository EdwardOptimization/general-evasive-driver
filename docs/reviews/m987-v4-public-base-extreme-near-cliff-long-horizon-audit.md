# m987-v4-public-base-extreme-near-cliff-long-horizon-audit Research Review

## Summary

- Generated at UTC: 20260526T125419Z
- Type: gate
- Gate tier: proof
- Promotion decision: extreme_near_cliff_long_horizon_empty_route_to_synthesis
- Decision reason: M987 extends continuation horizon to 20 and still finds zero accepted rows despite 7090 action-threshold rows and wrong success rate 1.0

## Hypothesis

Some near-cliff wrong-history failures are delayed beyond the 9-step continuation horizon; increasing max_continuation_steps to 20 will reveal accepted rows without changing thresholds.

## Lineage

- parent_checkpoint: runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt
- parent_dataset: docs/m986-v4-public-base-extreme-near-cliff-source-mining.md, runs/m986_v4_public_base_extreme_near_cliff_source_mining/summary.json
- parent_config: configs/m984_extreme_low_mu_drop.json, configs/m984_brake_authority_loss.json, configs/m984_lateral_authority_loss.json, configs/m984_heavy_cg_delay.json, configs/m984_high_speed_close_obstacle.json, experiments/manifests/m986-v4-public-base-extreme-near-cliff-source-mining.json
- parent_objective: audit whether 9-step continuation hides delayed wrong-history outcome degradation in near-cliff rows
- derived_from: m986-v4-public-base-extreme-near-cliff-source-mining, m985-v4-public-base-extreme-scenario-family-source-mining
- blocked_by: M986 near-cliff mining finds no accepted rows and all wrong-history continuations remain successful over 9 steps
- supersedes: None
- invalidates: starting PPO from the M986 result, lowering accepted-row thresholds before auditing continuation horizon

## Success Criteria

- summary artifact exists
- accepted rows and source diversity are reported by family
- max_continuation_steps is 20
- actor parameters are unchanged
- PPO and promotion are not used
- route decision is explicit

## Failure Criteria

- miner crashes
- actor parameters change
- training or PPO starts
- accepted-row thresholds are lowered
- route decision is missing

## Evidence Gates

- M987 must not run PPO
- M987 must not promote
- M987 must not use private holdout
- M987 must preserve P0 actor-input contract
- M987 must keep accepted-row action and margin thresholds unchanged
- M987 may increase max_continuation_steps from 9 to 20

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not add hidden parameters to actor inputs
- do not train or optimize
- do not use private holdout
- do not lower accepted-row thresholds
- do not promote any checkpoint

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m987-v4-public-base-extreme-near-cliff-long-horizon-audit
- type: gate
- checkpoint: runs/m987_v4_public_base_extreme_near_cliff_long_horizon_audit/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: extreme_near_cliff_long_horizon_empty_route_to_synthesis
- reason: M987 extends continuation horizon to 20 and still finds zero accepted rows despite 7090 action-threshold rows and wrong success rate 1.0

## Next Blocker

m988-v4-public-base-extreme-scenario-family-synthesis
