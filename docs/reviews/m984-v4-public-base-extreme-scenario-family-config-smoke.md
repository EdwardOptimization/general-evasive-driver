# m984-v4-public-base-extreme-scenario-family-config-smoke Research Review

## Summary

- Generated at UTC: 20260526T121656Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: extreme_scenario_family_config_smoke_pass_route_to_source_mining
- Decision reason: M984 creates five extreme scenario configs and smoke-runs all with 211 snapshots 57 near-boundary preferred rows and no actor/PPO changes

## Hypothesis

Existing single-track simulator knobs can define richer global-failure scenario families that are more likely to expose source-diverse wrong-history outcome sensitivity without violating the P0 actor contract.

## Lineage

- parent_checkpoint: runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt
- parent_dataset: docs/m983-v4-public-base-post-repair-surface-refresh-synthesis.md
- parent_config: configs/ppo_m541_matched_l3_variance_4096.json, configs/eval_m574_moderate_ood_l3.json
- parent_objective: create richer source-mining families after ordinary fresh/OOD mining failed to expose source-diverse outcome-sensitive rows
- derived_from: m983-v4-public-base-post-repair-surface-refresh-synthesis
- blocked_by: M983 pivots away from same-family mining to scenario-family generation
- supersedes: None
- invalidates: claiming per-wheel or asymmetric fault coverage before dynamics support exists

## Success Criteria

- extreme family configs are created
- config smoke artifact exists
- each family samples valid obstacle scenarios
- actor input contract remains P0 no-wheel/no-oracle
- unsupported per-wheel failure scope is documented
- no PPO or promotion occurs

## Failure Criteria

- a config cannot sample scenarios
- a config changes actor input contract
- hidden parameters enter actor observation
- training or PPO starts
- unsupported per-wheel fault claims are made

## Evidence Gates

- M984 must not run PPO
- M984 must not promote
- M984 must preserve P0 actor-input contract
- M984 must keep hidden dynamics as simulator-only/logging-only fields
- M984 must explicitly separate supported global-failure approximations from unsupported per-wheel failures

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not add hidden parameters to actor inputs
- do not train or optimize
- do not use private holdout
- do not claim split-mu or individual-wheel failure support without changing dynamics
- do not promote any checkpoint

## Failure Taxonomy

- none

## Scoreboard

- milestone: m984-v4-public-base-extreme-scenario-family-config-smoke
- type: infrastructure
- checkpoint: runs/m984_v4_public_base_extreme_scenario_family_config_smoke/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: extreme_scenario_family_config_smoke_pass_route_to_source_mining
- reason: M984 creates five extreme scenario configs and smoke-runs all with 211 snapshots 57 near-boundary preferred rows and no actor/PPO changes

## Next Blocker

m985-v4-public-base-extreme-scenario-family-source-mining
