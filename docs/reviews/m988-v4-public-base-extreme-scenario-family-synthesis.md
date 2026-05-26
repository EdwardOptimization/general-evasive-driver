# m988-v4-public-base-extreme-scenario-family-synthesis Research Review

## Summary

- Generated at UTC: 20260526T125419Z
- Type: gate
- Gate tier: process
- Promotion decision: pivot_to_capability_step_fault_generation
- Decision reason: M988 synthesizes M984-M987 and pivots from config-only extreme mining to hidden capability-step fault event design

## Hypothesis

M984-M987 provide enough evidence to close the config-only extreme scenario branch and pivot to hidden capability-step/fault event design.

## Lineage

- parent_checkpoint: runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt
- parent_dataset: docs/m984-v4-public-base-extreme-scenario-family-config-smoke.md, docs/m985-v4-public-base-extreme-scenario-family-source-mining.md, docs/m986-v4-public-base-extreme-near-cliff-source-mining.md, docs/m987-v4-public-base-extreme-near-cliff-long-horizon-audit.md
- parent_config: configs/m984_extreme_low_mu_drop.json, configs/m984_brake_authority_loss.json, configs/m984_lateral_authority_loss.json, configs/m984_heavy_cg_delay.json, configs/m984_high_speed_close_obstacle.json
- parent_objective: synthesize config-only extreme scenario-family mining before changing simulator semantics
- derived_from: m984-v4-public-base-extreme-scenario-family-config-smoke, m985-v4-public-base-extreme-scenario-family-source-mining, m986-v4-public-base-extreme-near-cliff-source-mining, m987-v4-public-base-extreme-near-cliff-long-horizon-audit
- blocked_by: M985-M987 all find zero accepted rows despite live action separation
- supersedes: None
- invalidates: continuing same config-only mining as the main branch, training from M984-M987, claiming source-diverse extreme scenario proof-surface evidence

## Success Criteria

- synthesis artifact exists
- supported and falsified claims are explicit
- failure taxonomy is explicit
- public gate overfit risk is updated
- next branch decision is explicit
- no training or promotion occurs

## Failure Criteria

- synthesis artifact is missing
- route decision is missing
- thresholds are lowered retroactively
- training or PPO starts
- unsupported per-wheel failure claims are made

## Evidence Gates

- M988 must synthesize M984-M987 before opening a new branch
- M988 must not run PPO
- M988 must not promote
- M988 must not use private holdout
- M988 must preserve P0 actor-input contract

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train or optimize
- do not lower thresholds retroactively
- do not claim source-diverse proof rows from M984-M987
- do not claim per-wheel faults under the current single-track dynamics

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m988-v4-public-base-extreme-scenario-family-synthesis
- type: gate
- checkpoint: docs/m988-v4-public-base-extreme-scenario-family-synthesis.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: pivot_to_capability_step_fault_generation
- reason: M988 synthesizes M984-M987 and pivots from config-only extreme mining to hidden capability-step fault event design

## Next Blocker

m989-v4-public-base-capability-step-fault-design
