# m986-v4-public-base-extreme-near-cliff-source-mining Research Review

## Summary

- Generated at UTC: 20260526T124159Z
- Type: gate
- Gate tier: proof
- Promotion decision: extreme_near_cliff_empty_route_to_long_horizon_audit
- Decision reason: M986 narrows normal_margin_max to 0.20 and still finds zero accepted rows despite 10431 action-threshold rows and candidate max margin gap 0.00274

## Hypothesis

Extreme scenario-family wrong-history outcome sensitivity is concentrated near terminal-margin cliffs; restricting normal-success rows to margin <= 0.20 will reveal accepted rows without weakening accepted-row thresholds.

## Lineage

- parent_checkpoint: runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt
- parent_dataset: docs/m985-v4-public-base-extreme-scenario-family-source-mining.md, runs/m985_v4_public_base_extreme_scenario_family_source_mining/summary.json
- parent_config: configs/m984_extreme_low_mu_drop.json, configs/m984_brake_authority_loss.json, configs/m984_lateral_authority_loss.json, configs/m984_heavy_cg_delay.json, configs/m984_high_speed_close_obstacle.json, experiments/manifests/m985-v4-public-base-extreme-scenario-family-source-mining.json
- parent_objective: focus source mining on terminal-margin near-cliff normal-success rows after broad-window mining found no accepted rows
- derived_from: m985-v4-public-base-extreme-scenario-family-source-mining, m984-v4-public-base-extreme-scenario-family-config-smoke
- blocked_by: M985 finds no accepted rows despite many action-threshold candidates; top margin gaps occur with too much terminal slack
- supersedes: None
- invalidates: starting PPO from the M985 broad-window result, lowering accepted-row action or margin thresholds

## Success Criteria

- summary artifact exists
- accepted rows and source diversity are reported by family
- normal_margin_max is 0.20
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

- M986 must not run PPO
- M986 must not promote
- M986 must not use private holdout
- M986 must preserve P0 actor-input contract
- M986 must keep accepted-row action and margin thresholds unchanged
- M986 may narrow the normal-success mining window to terminal-margin near-cliff rows

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

- milestone: m986-v4-public-base-extreme-near-cliff-source-mining
- type: gate
- checkpoint: runs/m986_v4_public_base_extreme_near_cliff_source_mining/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: extreme_near_cliff_empty_route_to_long_horizon_audit
- reason: M986 narrows normal_margin_max to 0.20 and still finds zero accepted rows despite 10431 action-threshold rows and candidate max margin gap 0.00274

## Next Blocker

m987-v4-public-base-extreme-near-cliff-long-horizon-audit
