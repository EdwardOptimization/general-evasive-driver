# m1193-paper-route-controller-profile-training-smoke-design Research Review

## Summary

- Generated at UTC: 20260528T045508Z
- Type: gate
- Gate tier: infrastructure
- Promotion decision: training_smoke_design_routes_to_branch_synthesis_before_mask_integration
- Decision reason: M1193 designs a fair resource-capped profile training-smoke protocol but blocks direct training because train_ppo vector env paths do not yet apply controller-profile masks and workflow cadence requires synthesis before another implementation milestone; no training PPO replay promotion private holdout or actor-input change

## Hypothesis

A fair resource-capped training-smoke protocol can be designed for generated L0/L1/L2/L3 configs without starting training or weakening input-contract controls.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m1192-paper-route-controller-profile-runtime-smoke-run.md, runs/m1192_controller_profile_runtime_smoke/summary.json, configs/paper_route_profiles
- parent_config: experiments/manifests/m1192-paper-route-controller-profile-runtime-smoke-run.json
- parent_objective: design a fair bounded training-smoke protocol for L0/L1/L2/L3 profile comparison after runtime instantiation passes
- derived_from: m1192-paper-route-controller-profile-runtime-smoke-run
- blocked_by: profile runtime smoke passes but training smoke should not start without a pre-registered fair resource-capped protocol
- supersedes: launching generated profile training directly after runtime smoke
- invalidates: claiming profile comparability from runtime instantiation alone

## Success Criteria

- docs/m1193-paper-route-controller-profile-training-smoke-design.md exists
- protocol fixes profile set, seeds, budgets, env split, metrics, gates, resource cap, and fallback ladder
- runtime mask train_ppo integration requirement is explicitly handled before L0 training
- no controller training, candidate replay, PPO, promotion, private holdout, or actor-input contract change occurs
- next implementation or run milestone is selected

## Failure Criteria

- training starts in M1193
- protocol gives profiles unequal budgets or per-profile tuning
- private holdout is used
- runtime mask training integration risk is ignored
- hidden or oracle actor inputs are introduced

## Evidence Gates

- M1193 may design controller profile training-smoke protocol only
- M1193 must not train controller weights
- M1193 must not run PPO
- M1193 must not run candidate replay
- M1193 must not promote
- M1193 must not use private holdout
- M1193 must not add hidden or oracle actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train generated configs
- do not run PPO
- do not evaluate driver performance
- do not use private holdout
- do not tune per profile from early results
- do not change actor inputs
- do not add hidden or oracle actor inputs
- do not claim profile superiority from a design document

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1193-paper-route-controller-profile-training-smoke-design
- type: gate
- checkpoint: docs/m1193-paper-route-controller-profile-training-smoke-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: training_smoke_design_routes_to_branch_synthesis_before_mask_integration
- reason: M1193 designs a fair resource-capped profile training-smoke protocol but blocks direct training because train_ppo vector env paths do not yet apply controller-profile masks and workflow cadence requires synthesis before another implementation milestone; no training PPO replay promotion private holdout or actor-input change

## Next Blocker

m1194-paper-route-finite-window-gru-infrastructure-synthesis
