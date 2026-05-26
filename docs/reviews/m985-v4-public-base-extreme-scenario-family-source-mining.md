# m985-v4-public-base-extreme-scenario-family-source-mining Research Review

## Summary

- Generated at UTC: 20260526T123239Z
- Type: gate
- Gate tier: proof
- Promotion decision: extreme_scenario_broad_window_empty_route_to_near_cliff_mining
- Decision reason: M985 mines all five M984 families with broad normal-margin window and finds zero accepted rows despite 15019 action-threshold rows and candidate max margin gap 0.00440

## Hypothesis

Richer hidden-dynamics scenario families will expose source-diverse outcome-sensitive wrong-history rows more reliably than the ordinary fresh/OOD public families used in M980-M982.

## Lineage

- parent_checkpoint: runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt
- parent_dataset: docs/m984-v4-public-base-extreme-scenario-family-config-smoke.md, runs/m984_v4_public_base_extreme_scenario_family_config_smoke/summary.json
- parent_config: configs/m984_extreme_low_mu_drop.json, configs/m984_brake_authority_loss.json, configs/m984_lateral_authority_loss.json, configs/m984_heavy_cg_delay.json, configs/m984_high_speed_close_obstacle.json, experiments/manifests/m984-v4-public-base-extreme-scenario-family-config-smoke.json
- parent_objective: mine source-diverse wrong-history outcome-sensitive rows from richer scenario families
- derived_from: m984-v4-public-base-extreme-scenario-family-config-smoke, m983-v4-public-base-post-repair-surface-refresh-synthesis
- blocked_by: M984 creates and smokes configs but does not yet run source-diverse mining
- supersedes: None
- invalidates: training before source-diverse accepted rows exist, using the isolated M980/M982 pocket as the only new surface

## Success Criteria

- summary artifact exists
- accepted rows and source diversity are reported by family
- actor parameters are unchanged
- PPO and promotion are not used
- route decision is explicit

## Failure Criteria

- miner crashes
- actor parameters change
- training or PPO starts
- thresholds are lowered after seeing output
- route decision is missing

## Evidence Gates

- M985 must not run PPO
- M985 must not promote
- M985 must not use private holdout
- M985 must preserve P0 actor-input contract
- M985 must report source diversity by scenario family
- M985 must not lower acceptance thresholds after seeing output

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not add hidden parameters to actor inputs
- do not train or optimize
- do not use private holdout
- do not claim unsupported per-wheel fault coverage
- do not promote any checkpoint

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m985-v4-public-base-extreme-scenario-family-source-mining
- type: gate
- checkpoint: runs/m985_v4_public_base_extreme_scenario_family_source_mining/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: extreme_scenario_broad_window_empty_route_to_near_cliff_mining
- reason: M985 mines all five M984 families with broad normal-margin window and finds zero accepted rows despite 15019 action-threshold rows and candidate max margin gap 0.00440

## Next Blocker

m986-v4-public-base-extreme-near-cliff-source-mining
